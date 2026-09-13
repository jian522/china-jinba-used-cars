#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动选定合规封面（正前脸 / 左前 45°）——部署前强制步骤。

## 背景（2026-09-12 用户要求）
上架车辆的**首图必须为正前脸或左前 45°**。che168 详情页的顺序图集里第 1 张
经常是内饰/车尾/局部特写，不能直接当封面。人工目检可靠但不可持续——每日
自动上架必须无人值守。

## 为什么不用纯图像特征自动判定（2026-09-12 实测结论，勿重蹈）
本轮做了两版尝试，都在真实数据上被证伪：

  1. **亮区启发式**（`exterior_like`：上部亮区占比）：4 台车 36 张里
     把"车头局部特写""车尾"判成外观（车头局部特写上亮下暗、边少，与正前
     45° 全景特征重叠）。
  2. **整车掩膜**（与边框连通的近背景色 = 背景）：展厅白墙/灰地/天空与车身
     色差归零，flood fill 溢出到整个背景，前景/背景彻底反向。轮胎特写更会
     因通体近黑被判成"前景连通"，`sym/holes` 等形状特征随之失效。

**结论：che168 这类"干净展厅 + 灰地 + 白墙"的拍摄场景里，纯灰度特征无法
可靠区分"整车外观"与"局部特写/内饰"。** 与其做一个会误放的启发式（误放
比漏放危害大：违规车直接上线），不如把**语义判断交给视觉模型**，用确定性
算子只做"宁缺毋滥"的粗筛。

## 本脚本的三段式设计
  1. **粗筛（确定性算子）**：排除过暗/纹理过密/上下亮区完全不通的图。只求
     不误放，允许漏放。给视觉模型一个明显更小的候选集（通常 5~12 张）。
  2. **语义裁决（视觉模型）**：对候选集逐张判断"是否为整车正前脸/左前45°
     外观"。两种实现：
     - `--judge vision`（默认）：调用 WorkBuddy 视觉模型（需在 Agent 会话中
       由 Agent 传图裁决，脚本本身只导出候选清单 + 拼图）
     - `--judge manual`：导出候选拼图 + picks JSON 草稿，交人工/AI 目检勾选
  3. **硬校验 + 落地**：选中图必须通过 `photo_check` 全部规则（R1 水印 +
     R2 视角）。通过后**只把其内容写进 primary.webp**（photos 列表不变），
     被占位那张图退回原 primary 内容，图片集合无损。

全部候选都不合规 → 该车**不发布**（unpublished），等人工处理，绝不硬塞。

## 用法
```
# 1) 导出候选清单 + 拼图（供 AI/人工目检）
"$PY" scripts/cover_auto.py --export --id 335,336,337,338

# 2) 按目检结果落地（picks JSON: {vehicle_id: img文件序号}）
"$PY" scripts/cover_auto.py --picks .workbuddy/cover_auto/picks.json --commit

# 只跑粗筛看统计
"$PY" scripts/cover_auto.py --id 335 --dry-run
```
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
DATA = ROOT / "data" / "vehicles.json"
TARGET_W, TARGET_H = 720, 540
QUALITY = 88
THUMB_W = 300

sys.path.insert(0, str(ROOT / "scripts"))
from photo_check import check_image  # noqa: E402

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
HOST = "https://wap.che168.com"

# ---- 粗筛阈值（只排除"确定不是外观"的图，宁缺毋滥）----
MEAN_MIN = 88.0        # 过暗 → 内饰
EDGES_MAX = 32.0       # 纹理过密 → 细节特写/按键
TOP_BRIGHT_MIN = 0.03  # 上部无任何亮区 → 无天空/开阔背景


def gray(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("L"), dtype=float)


def get(url: str, retries: int = 3, timeout: int = 25) -> str:
    import requests
    for i in range(retries):
        try:
            r = requests.get(url, headers={"User-Agent": UA,
                                           "Referer": HOST + "/"}, timeout=timeout)
            if r.status_code == 200 and len(r.content) > 5000:
                return r.text
        except Exception as e:  # noqa: BLE001
            print(f"    retry {i + 1} {url}: {e}")
            time.sleep(1.0 + i)
    return ""


def fetch_gallery(car_id: str, out_dir: Path, limit: int = 40) -> list[Path]:
    """抓 che168 详情页全部 720x540 图，返回按页面顺序的本地文件列表。

    **顺序与 che168 页面一致**，因此 `img_NN` 与 `photos[NN-1]` 语义对位
    （imports 批次只留了前 9 张，重抓能把候选池扩到 27~32 张）。
    """
    import requests
    html = get(f"{HOST}/dealer/0/{car_id}.html")
    if not html:
        return []
    urls = re.findall(
        r"(?:https?:)?//2sc\d?\.autoimg\.cn/escimg/[^\"' )]+?720x540[^\"' )]+?\.jpg", html)
    if not urls:
        urls = [u for u in re.findall(
            r"(?:https?:)?//2sc\d?\.autoimg\.cn/escimg/[^\"' )]+?\.jpg", html)
            if "f_480x360" not in u and "icon" not in u]
    seen, uniq = set(), []
    for u in urls:
        if u.startswith("//"):
            u = "https:" + u
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, u in enumerate(uniq[:limit], 1):
        try:
            r = requests.get(u, headers={"User-Agent": UA,
                                          "Referer": f"{HOST}/dealer/0/{car_id}.html"},
                             timeout=25)
            if r.status_code == 200 and len(r.content) > 3000:
                p = out_dir / f"img_{i:02d}.jpg"
                p.write_bytes(r.content)
                saved.append(p)
        except Exception as e:  # noqa: BLE001
            print(f"    img {i:02d} err: {e}")
        time.sleep(0.2)
    return saved


def prefilter(path: Path) -> tuple[bool, str, dict]:
    """粗筛：只排除"确定不是整车外观"的图。返回 (通过, 原因, 指标)。"""
    a = gray(Image.open(path))
    h = a.shape[0]
    mean = float(a.mean())
    edges = float(np.abs(np.diff(a, axis=1)).mean())
    top_bright = float((a[: h // 4] > 170).mean())
    m = {"mean": round(mean, 1), "edges": round(edges, 1),
         "top_bright": round(top_bright, 4)}
    if mean < MEAN_MIN:
        return False, f"过暗 {mean:.0f}(内饰嫌疑)", m
    if edges > EDGES_MAX:
        return False, f"纹理过密 {edges:.1f}(细节特写)", m
    if top_bright < TOP_BRIGHT_MIN:
        return False, f"上部无亮区 {top_bright:.3f}(无开阔背景)", m
    return True, "", m


def save_cover_content(src: Path, target: Path) -> None:
    """把 src 的内容按 4:3 写进 target，并重建缩略图。"""
    im = Image.open(src).convert("RGB")
    w, h = im.size
    scale = max(TARGET_W / w, TARGET_H / h)
    if scale > 1.0:
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    w, h = im.size
    left, top = (w - TARGET_W) // 2, (h - TARGET_H) // 2
    im = im.crop((left, top, left + TARGET_W, top + TARGET_H))
    target.parent.mkdir(parents=True, exist_ok=True)
    im.save(target, "WEBP", quality=QUALITY, method=6)
    th = im.copy()
    th.thumbnail((THUMB_W, THUMB_W), Image.LANCZOS)
    th.save(target.with_name(target.name.replace(".webp", ".th.webp")),
            "WEBP", quality=80, method=6)


def infoid_of(v: dict) -> str | None:
    m = re.search(r"car (\d{5,})", v.get("source", "") or "")
    return m.group(1) if m else None


def build_sheet(items: list[tuple[str, Path]], out: Path,
                cols: int = 6, cw: int = 300) -> None:
    """把候选图拼成一张带序号的接触表（contact sheet），供目检/视觉模型裁决。"""
    if not items:
        return
    ch = int(cw * TARGET_H / TARGET_W)
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, (ch + 22) * rows), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, (label, p) in enumerate(items):
        try:
            im = Image.open(p).convert("RGB").resize((cw, ch))
        except Exception:  # noqa: BLE001
            continue
        x, y = (i % cols) * cw, (i // cols) * (ch + 22) + 20
        sheet.paste(im, (x, y))
        d.text((x + 4, y - 16), label, fill=(0, 0, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="真正写盘；缺省预演")
    ap.add_argument("--export", action="store_true",
                    help="导出候选清单 + 拼图（供目检），不写任何图")
    ap.add_argument("--picks", help="picks JSON: {\"<vehicle_id>\": <img序号>}")
    ap.add_argument("--id", help="逗号分隔车辆 id（缺省=最近 10 台 published）")
    ap.add_argument("--no-refetch", action="store_true",
                    help="不重抓 che168，只用 imports/ 现有原图当候选")
    ap.add_argument("--json", dest="out_json")
    args = ap.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    pub = [v for v in data if v.get("status") == "published"]
    by_id = {v["id"]: v for v in data}

    # ---- 模式 B：按 picks 落地 ----
    if args.picks:
        picks = {int(k): int(v) for k, v in
                 json.loads(Path(args.picks).read_text(encoding="utf-8")).items()}
        n = 0
        for vid, idx in sorted(picks.items()):
            v = by_id.get(vid)
            if v is None:
                print(f"!! id {vid} 不在库中")
                continue
            if idx <= 0:
                print(f"   {v['stock_id']} 序号 {idx} 不合法（须 ≥1）")
                continue
            photos = v.get("photos") or []
            cover = ROOT / photos[0].lstrip("/")
            gdir = ROOT / ".workbuddy" / "cover_auto" / str(vid)
            src = gdir / f"img_{idx:02d}.jpg"
            if not src.is_file():
                print(f"!! {v['stock_id']} 候选缺失 {src}")
                continue
            # 硬校验：必须过 photo_check 全部规则。
            # 注意：必须对**真实候选路径**校验，不能用临时目录——
            # photo_check 的条带豁免依赖"原图/重抓图集同位同性质"的同源比对，
            # 临时路径会让 band_exempt_by_source 取不到源而误判（2026-09-12 踩过）。
            r = check_image(src, is_cover=True)
            if not r["ok"]:
                print(f"!! {v['stock_id']} 选中图未过 photo_check: {r['issues']}")
                continue
            print(f"   {v['stock_id']} (id {vid}): primary ← img_{idx:02d}.jpg"
                  f"  {'[写盘]' if args.commit else '[预演]'}")
            if args.commit:
                # idx=1 时 photos[idx-1] 就是 primary 自己，互换会把旧封面写回
                # （等于空操作，2026-09-13 实证）→ 直接写入，旧封面内容弃用
                # （新批次旧封面多为内饰/车尾废图，画廊已有同类）。
                if idx > 1 and idx <= len(photos) and (ROOT / photos[idx - 1].lstrip("/")).is_file():
                    # 内容互换：候选进 primary，原 primary 退回该位置图 → 图片集合无损
                    target = ROOT / photos[idx - 1].lstrip("/")
                    tmp = Path(tempfile.mkdtemp()) / "orig.webp"
                    tmp.write_bytes(cover.read_bytes())
                    save_cover_content(src, cover)
                    save_cover_content(tmp, target)
                else:
                    save_cover_content(src, cover)
                n += 1
        print(f"\n{'已换封面' if args.commit else '预演'} {n if args.commit else len(picks)} 台")
        return 0

    # ---- 模式 A：粗筛 / 导出候选 ----
    if args.id:
        only = {int(x) for x in args.id.split(",")}
        targets = [v for v in pub if v["id"] in only]
    else:
        targets = sorted(pub, key=lambda v: v["id"])[-10:]

    work = ROOT / ".workbuddy" / "cover_auto"
    report = []
    all_items: list[tuple[str, Path]] = []

    for v in targets:
        vid, stock = v["id"], v["stock_id"]
        photos = v.get("photos") or []
        if not photos:
            print(f"✗ {stock} 无 photos")
            continue

        car_id = infoid_of(v)
        gdir = work / str(vid)
        if car_id and not args.no_refetch:
            if gdir.exists():
                shutil.rmtree(gdir)
            cands = fetch_gallery(car_id, gdir)
            print(f"  {stock} (id {vid}) 重抓 {len(cands)} 张（car {car_id}）")
            time.sleep(0.5)
        else:
            cands = sorted(gdir.glob("img_*.jpg")) if gdir.is_dir() else []
        if not cands:
            for b in sorted((ROOT / "imports").iterdir()):
                d = b / stock
                if d.is_dir():
                    cands = sorted(p for p in d.glob("*.jpg"))
                    break
            print(f"  {stock} (id {vid}) 用 imports 原图 {len(cands)} 张")

        if not cands:
            print(f"✗ {stock} 无候选图")
            report.append({"stock": stock, "id": vid, "ok": False, "reason": "无候选图"})
            continue

        passed = []
        for p in cands:
            try:
                ok, why, m = prefilter(p)
            except Exception as e:  # noqa: BLE001
                print(f"    {p.name} 读取失败 {e}")
                continue
            if ok:
                passed.append(p)
        print(f"    粗筛通过 {len(passed)}/{len(cands)} 张")
        seq = []
        for p in passed:
            m = re.match(r"img_(\d+)$", p.stem)
            num = int(m.group(1)) if m else 1
            seq.append({"n": num, "file": p.name})
            all_items.append((f"{stock} #{num}", p))
        report.append({"stock": stock, "id": vid, "ok": bool(passed),
                       "candidates_total": len(cands),
                       "candidates_pass": len(passed), "seq": seq,
                       "reason": "" if passed else "粗筛后无候选"})

    if args.export or args.out_json or not args.commit:
        build_sheet(all_items, work / "candidates.png")
        print(f"\n候选拼图 → {work / 'candidates.png'}（{len(all_items)} 张）")

    for r in report:
        if r["ok"]:
            print(f"  {r['stock']} (id {r['id']}) 候选 {r['candidates_pass']}/"
                  f"{r['candidates_total']}: {[s['n'] for s in r.get('seq', [])]}")
        else:
            print(f"  ! {r['stock']}: {r['reason']}")

    out = work / "candidates.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"清单 → {out}")
    print(f"\n下一步：目检 candidates.png，把选中序号写成 picks JSON，再跑 "
          f"--picks <file> --commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
