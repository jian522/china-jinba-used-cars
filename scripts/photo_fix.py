#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""车辆图片批量修复（与 photo_check.py 组成校验-修复闭环）。

修复策略（确定性算子，不改变车辆真实外观）：
  R1 条带水印 → 裁掉底/顶部纯色条带，再居中裁回 720x540，重转 webp + 缩略图
  R1 角部叠印 → 仅当呈现"文字行"特征（行剖面变异系数 CV≥0.85 且能量离群）
               判为疑似水印，列入人工复核清单；均匀纹理（背景树木/建筑/
               车身反光）不是水印，不处理 —— 见 2026-09-09 摸底结论：
               106 处角部告警中 68 处与原图同位、CV 多 <0.7，属场景纹理
  R2 封面违规 → 从该车其余图中挑"外观分"最高的一张换到第 1 位（仅改
               vehicles.json photos 顺序 + 互换文件名，不改像素）

用法：
  "$PY" scripts/photo_fix.py --dry-run             # 预演，只报告打算怎么修
  "$PY" scripts/photo_fix.py --all --commit        # 全量修复
  "$PY" scripts/photo_fix.py --id 323,325 --commit # 只修指定车辆
  "$PY" scripts/photo_fix.py --json fix-report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vehicles.json"
TARGET_W, TARGET_H = 720, 540
QUALITY = 88
THUMB_W = 300

sys.path.insert(0, str(ROOT / "scripts"))
from photo_check import corner_overlay, gray, interior_like, rear_like, strip_bar  # noqa: E402


def text_score(corner: np.ndarray) -> float:
    """行剖面变异系数：文字行能量集中于少数行 → CV 大；均匀纹理 → CV 小。"""
    e = np.abs(np.diff(corner, axis=1))
    row_energy = e.mean(axis=1)
    return float(row_energy.std() / (row_energy.mean() + 1e-6))


def watermark_corners(a: np.ndarray) -> list[str]:
    """高置信水印角：能量离群 + 文字行特征。"""
    h, w = a.shape
    k = max(24, int(min(h, w) * 0.12))
    corners = {
        "top-left": a[:k, :k], "top-right": a[:k, -k:],
        "bottom-left": a[-k:, :k], "bottom-right": a[-k:, -k:],
    }
    energies = {n: float(np.abs(np.diff(c, axis=1)).mean()) for n, c in corners.items()}
    med = float(np.median(list(energies.values())))
    hits = []
    for n, c in corners.items():
        e = energies[n]
        if med > 0.5 and e > med * 2.6 and e > 4.0 and text_score(c) >= 0.85:
            hits.append(n)
    return hits


def exterior_score(a: np.ndarray) -> tuple[int, float]:
    """外观分（越小越好）：类别 0=外观(有天空亮区) 1=中性 2=内饰/细节；
    类内用上部亮区占比排序（前脸/45° 构图上部开阔）。"""
    h, w = a.shape
    mean = a.mean()
    top = a[: h // 4].mean()
    edges = np.abs(np.diff(a, axis=1)).mean()
    if top > mean + 18 and mean > 90:
        cat = 0
    elif mean < 95 or edges > 26:
        cat = 2
    else:
        cat = 1
    return cat, -float((a[: h // 4] > 200).mean())


def crop_bars(im: Image.Image) -> Image.Image:
    """裁掉底部/顶部纯色条带（角标底板）。"""
    a = gray(im)
    cut_b = 0.06 if strip_bar(a, 0.06, top=False) else 0.0
    cut_t = 0.05 if strip_bar(a, 0.05, top=True) else 0.0
    if not (cut_b or cut_t):
        return im
    w, h = im.size
    return im.crop((0, int(h * cut_t), w, int(h * (1 - cut_b))))


def recrop_43(im: Image.Image) -> Image.Image:
    """统一回 720x540：等比放大覆盖目标框后居中裁剪。"""
    w, h = im.size
    scale = max(TARGET_W / w, TARGET_H / h)
    if scale > 1.0:
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    w, h = im.size
    left, top = (w - TARGET_W) // 2, (h - TARGET_H) // 2
    return im.crop((left, top, left + TARGET_W, top + TARGET_H))


def save_webp(im: Image.Image, path: Path) -> None:
    im.convert("RGB").save(path, "WEBP", quality=QUALITY, method=6)
    th = im.copy()
    th.thumbnail((THUMB_W, THUMB_W), Image.LANCZOS)
    th.save(path.with_name(path.name.replace(".webp", ".th.webp")),
            "WEBP", quality=80, method=6)


def fix_bar(path: Path) -> bool:
    """迭代裁条带：白墙/纯色地面会让"裁完又出现新条带"，
    循环裁到底部不再是纯色条（上限 4 轮，防把图裁没了）。"""
    im = Image.open(path).convert("RGB")
    changed = False
    for _ in range(4):
        a = gray(im)
        bot = strip_bar(a, 0.06, top=False)
        top = strip_bar(a, 0.05, top=True)
        if not (bot or top):
            break
        w, h = im.size
        cut_b = 0.06 if bot else 0.0
        cut_t = 0.05 if top else 0.0
        im = im.crop((0, int(h * cut_t), w, int(h * (1 - cut_b))))
        changed = True
    if not changed:
        return False
    if im.size[0] < TARGET_W * 0.6 or im.size[1] < TARGET_H * 0.6:
        return False          # 裁太多，放弃（交人工）
    save_webp(recrop_43(im), path)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--id", help="逗号分隔车辆 id")
    ap.add_argument("--commit", action="store_true", help="真正写盘；缺省预演")
    ap.add_argument("--json", dest="out_json", help="修复报告输出路径")
    args = ap.parse_args()

    if not DATA.exists():
        print(f"NOT FOUND: {DATA}")
        return 2
    data = json.loads(DATA.read_text(encoding="utf-8"))
    only_ids = ({int(x) for x in args.id.split(",")}
                if args.id else None)

    fix_report = []
    for v in data:
        if v.get("status") != "published":
            continue
        if only_ids and v["id"] not in only_ids:
            continue
        vid, stock = v["id"], v["stock_id"]
        photos = v.get("photos") or []
        entry = {"stock": stock, "id": vid, "actions": [], "manual": []}

        # --- R1 条带修复 ---
        for rel in photos:
            p = ROOT / rel.lstrip("/")
            if not p.is_file():
                continue
            a = gray(Image.open(p))
            has_bar = strip_bar(a, 0.06, top=False) or strip_bar(a, 0.05, top=True)
            wm = watermark_corners(a)
            if has_bar:
                if args.commit:
                    done = fix_bar(p)
                    entry["actions"].append(
                        f"条带裁剪+重裁4:3: {p.name}" if done else f"条带复核消失: {p.name}")
                else:
                    entry["actions"].append(f"[预演]条带裁剪: {p.name}")
            for c in wm:
                entry["manual"].append(f"疑似文字水印角({c}): {p.name} → 人工复核/换图")

        # --- R2 封面违规换图 ---
        if photos:
            cover = ROOT / photos[0].lstrip("/")
            if cover.is_file():
                ca = gray(Image.open(cover))
                if interior_like(ca) or rear_like(ca):
                    scored = []
                    for i, rel in enumerate(photos[1:], start=2):
                        p = ROOT / rel.lstrip("/")
                        if not p.is_file():
                            continue
                        scored.append((exterior_score(gray(Image.open(p))), i, rel))
                    if scored:
                        scored.sort(key=lambda x: (x[0][0], x[0][1], x[1]))
                        best_i, best_rel = scored[0][1], scored[0][2]
                        act = (f"封面换图: {photos[0]} ↔ 第{best_i}张 {best_rel}"
                               if args.commit
                               else f"[预演]封面换图 → {best_rel}")
                        entry["actions"].append(act)
                        if args.commit:
                            # 互换 photos 列表位置 + 互换文件名（保持 primary 命名）
                            photos[0], photos[best_i - 1] = best_rel, photos[0]
                            new_cover = ROOT / photos[0].lstrip("/")
                            old_cover = ROOT / photos[best_i - 1].lstrip("/")
                            tmp = old_cover.with_suffix(".swap.webp")
                            old_cover.rename(tmp)
                            new_cover.rename(old_cover)
                            tmp.rename(new_cover)
                            for base in (new_cover, old_cover):
                                th = base.with_name(
                                    base.name.replace(".webp", ".th.webp"))
                                if th.exists():
                                    th2 = base.with_suffix(".swap.th.webp")

                                    def _sw(a_: Path, b_: Path) -> None:
                                        if a_.exists():
                                            a_.rename(b_)
                                    _sw(th, th2)
                            # 缩略图同步互换
                            for base in (new_cover, old_cover):
                                th = base.with_name(
                                    base.name.replace(".webp", ".th.webp"))
                                sw = base.with_suffix(".swap.th.webp")
                                if sw.exists():
                                    sw.rename(th)

        if entry["actions"] or entry["manual"]:
            fix_report.append(entry)

    if args.commit:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")

    for e in fix_report:
        head = f"{e['stock']} (id {e['id']})"
        for a in e["actions"]:
            print(f"  {head}: {a}")
        for m in e["manual"]:
            print(f"  {head}: [人工] {m}")
    n_fix = sum(1 for e in fix_report if e["actions"])
    n_man = sum(len(e["manual"]) for e in fix_report)
    print(f"\n{'已修复' if args.commit else '预演'} {n_fix} 台；"
          f"待人工复核 {n_man} 处（文字水印嫌疑）")
    if args.out_json:
        Path(args.out_json).write_text(
            json.dumps(fix_report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"报告 → {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
