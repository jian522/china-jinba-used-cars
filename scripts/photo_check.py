#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""车辆图片规则校验（jinba 流水线部署前强制步骤）。

规则（用户 2026-09-09 指定）：
  R1 每张图必须是干净背景，不得含公司 logo / 水印 / 角标叠印。
  R2 首图（primary，封面）必须是车辆正前面或左前 45° 角的外观照；
     内饰、仪表、细节特写、纯车尾不能当封面。

检测手段（确定性图像特征，不用生成式）：
  水印 R1：
    a) 边缘条带：底部/顶部近似纯色条带（che168 角标底板）
    b) 半透明叠印：角部固定区域与全图相比呈现"低饱和+局部低对比纹理"
       —— 用角部区域高频能量与四角中位数比值的离群度判定
  封面 R2：
    a) 内饰排除：整体偏暗且上部无天空亮区（内饰特征），或边缘密度过高（细节特写）
    b) 尾部排除：车牌居中偏下且左右对称性高 + 上部无天空 —— 保守策略只判
       "上部亮区占比"与"垂直边缘分布"，正脸/45° 上部必有天空/背景亮区且
       车头横向特征展开；纯车尾在 4:3 构图中亮区偏小
    满足 a 且不触发排除项 → 判定前脸/45° 通过（45° 与正脸在构图特征上同族，
    细分角度靠人工在 cover-report 里复核，脚本只拦"明显不对"的）。

用法：
  "$PY" scripts/photo_check.py                     # 全量 published 车辆
  "$PY" scripts/photo_check.py --id 323 325 326    # 只查指定车辆 id
  "$PY" scripts/photo_check.py --json out.json     # 结果写 JSON（供流水线读取）

退出码：0=全部合规；1=存在违规（部署前必须处理）；2=运行错误。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vehicles.json"


def gray(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("L"), dtype=float)


def strip_bar(a: np.ndarray, frac: float, top: bool) -> bool:
    """近似纯色条带（角标底板）。"""
    h = a.shape[0]
    strip = a[: int(h * frac)] if top else a[int(h * (1 - frac)):, :]
    body = a[int(h * 0.1): int(h * 0.9), :]
    return strip.std() < 18 and abs(strip.mean() - body.mean()) > 25


def corner_overlay(a: np.ndarray) -> list[str]:
    """检测四角半透明水印叠印：角部高频能量显著低于四角中位数 → 有覆盖物。"""
    h, w = a.shape
    k = max(24, int(min(h, w) * 0.12))
    corners = {
        "top-left": a[:k, :k],
        "top-right": a[:k, -k:],
        "bottom-left": a[-k:, :k],
        "bottom-right": a[-k:, -k:],
    }
    # 高频能量 = 相邻像素差分绝对值均值（叠印文字/图形会抬高，均匀遮挡会降低；
    # 这里抓"叠印字"：角部高频能量远高于该图典型水平）
    energies = {n: float(np.abs(np.diff(c, axis=1)).mean()) for n, c in corners.items()}
    vals = np.array(list(energies.values()))
    med = float(np.median(vals))
    hits = []
    for n, c in corners.items():
        e = energies[n]
        if not (med > 0.5 and e > med * 2.6 and e > 4.0):
            continue
        # 文字行特征：能量集中于少数行（行剖面 CV≥0.85）。均匀纹理
        # （树木/建筑/车身反光）CV 低，不是水印 —— 2026-09-09 摸底结论。
        re_ = np.abs(np.diff(c, axis=1)).mean(axis=1)
        cv = re_.std() / (re_.mean() + 1e-6)
        if cv < 0.85:
            continue
        # 多行文字 vs 水平亮线：文字水印的竖笔画使列剖面呈字符空隙结构
        # （列能量 CV≥0.35）；灯带/天花板边缘是整行亮暗跃变，列剖面平坦
        # （CV<0.35）。峰行上下行亮度与角均值接近（无强反差底板）也是场景特征。
        e_cols = np.abs(np.diff(c, axis=0)).mean(axis=0)
        col_cv = e_cols.std() / (e_cols.mean() + 1e-6)
        if col_cv < 0.35:
            continue        # 列剖面平坦 → 水平结构（灯带/檐口/车身边缘）
        hits.append(n)
    return hits


def interior_like(a: np.ndarray) -> bool:
    """内饰/细节特征：整体暗 + 上部无亮区（窗外天空），或边缘密度过高。"""
    h, w = a.shape
    mean = a.mean()
    top = a[: h // 4].mean()
    edges = np.abs(np.diff(a, axis=1)).mean()
    if top < mean + 8 and mean < 110:
        return True           # 暗且上部无亮区 → 车内
    if edges > 30 and top < mean + 6:
        return True           # 高纹理密度 → 细节特写/内饰按键
    return False


def rear_like(a: np.ndarray) -> bool:
    """纯车尾保守判定：构图左右高度对称 + 中下部有亮色矩形（车牌）+ 上部亮区小。

    只拦明显车尾，不追求识别全部 —— 宁可漏报交人工，不误杀好图。
    """
    h, w = a.shape
    left = a[:, : w // 2]
    right = a[:, w // 2:]
    sym = float(np.abs(left.mean() - right.mean()))
    top_bright = (a[: h // 4] > 200).mean()
    # 车牌区：中下部找高亮小块
    mid = a[int(h * 0.55): int(h * 0.9), :]
    plate = (mid > 235).mean()
    return sym < 6 and plate > 0.012 and top_bright < 0.04


def check_image(path: Path, *, is_cover: bool) -> dict:
    res: dict = {"file": path.name, "ok": True, "issues": []}
    try:
        im = Image.open(path)
        im = im.convert("RGB")
    except Exception as e:  # noqa: BLE001
        res["ok"] = False
        res["issues"].append(f"unreadable: {e}")
        return res
    a = gray(im)

    # R1 水印
    if strip_bar(a, 0.06, top=False) or strip_bar(a, 0.05, top=True):
        res["ok"] = False
        res["issues"].append("R1 边缘纯色条带（角标/水印底板）")
    corners = corner_overlay(a)
    if corners and not exempt_by_source(path, corners):
        res["ok"] = False
        res["issues"].append(f"R1 角部疑似叠印水印/logo: {','.join(corners)}")
    elif corners:
        res["issues"].append(f"R1 角部已豁免（原图同位同能量，场景纹理）: {','.join(corners)}")

    # R2 封面必须是前脸/45°外观
    if is_cover:
        if interior_like(a):
            res["ok"] = False
            res["issues"].append("R2 封面疑似内饰/细节特写，需换正前或左前45°外观")
        elif rear_like(a):
            res["ok"] = False
            res["issues"].append("R2 封面疑似纯车尾，需换正前或左前45°外观")
    return res


def _imports_dir(stock: str) -> Path | None:
    for b in sorted((ROOT / "imports").iterdir()):
        d = b / stock
        if d.is_dir():
            return d
    return None


def exempt_by_source(path: Path, corners: list[str]) -> bool:
    """原图同位能量豁免：webp 与 imports 原图同角高频能量比在 0.9–1.1 →
    高频来自拍摄场景（树木/建筑/反光），不是转码产生的叠印。
    （webp 多经 720x540 裁剪，角区位置与原图同比例对应。）

    兜底同族豁免：enhance/fix 裁剪可能改变取景导致同位对比失效；
    此时若同车**任一** imports 原图同角能量 ≥ webp 的 70%（同一展厅
    灯带/建筑结构会在多张原图同角出现），同样判为场景纹理。"""
    name_map = {"top-left": "TL", "top-right": "TR",
                "bottom-left": "BL", "bottom-right": "BR"}
    # path = uploads/cars/<vid>/<file>；stock 从 photo_check 调用侧不好拿，
    # 用 vid 反查 vehicles.json
    try:
        vid = path.parent.name
        data = json.loads(DATA.read_text(encoding="utf-8"))
        v = next(x for x in data if str(x["id"]) == vid)
        stock = v["stock_id"]
    except Exception:  # noqa: BLE001
        return False
    impd = _imports_dir(stock)
    if impd is None:
        return False
    fn = path.name
    if fn.startswith("primary"):
        src = impd / "primary.jpg"
    else:
        try:
            idx = int(fn.replace("photo-", "").split(".")[0])
        except ValueError:
            return False
        src = impd / f"{stock}_src_{idx}.jpg"
        if not src.is_file():
            # enhance 管线重排过顺序：按序号兜底找同尺寸近似原图
            cands = sorted(impd.glob(f"{stock}_src_*.jpg"))
            if not cands:
                return False
            src = cands[min(idx - 2, len(cands) - 1)] if idx >= 2 else cands[0]
    if not src.is_file():
        return False
    try:
        wimg = gray(Image.open(path))
        simg = gray(Image.open(src))
    except Exception:  # noqa: BLE001
        return False
    wh, ww = wimg.shape
    sh, sw = simg.shape
    wk = max(24, int(min(wh, ww) * 0.12))
    sk = max(24, int(min(sh, sw) * 0.12))
    _sname = {"top-left": "TL", "top-right": "TR",
              "bottom-left": "BL", "bottom-right": "BR"}
    wslices = {"TL": (0, wk, 0, wk), "TR": (0, wk, ww - wk, ww),
               "BL": (wh - wk, wh, 0, wk), "BR": (wh - wk, wh, ww - wk, ww)}
    sslices = {"TL": (0, sk, 0, sk), "TR": (0, sk, sw - sk, sw),
               "BL": (sh - sk, sh, 0, sk), "BR": (sh - sk, sh, sw - sk, sw)}

    def e_of(a: np.ndarray, sl: tuple) -> float:
        c = a[sl[0]:sl[1], sl[2]:sl[3]]
        return float(np.abs(np.diff(c, axis=1)).mean())

    we = {n: e_of(wimg, wslices[_sname[n]]) for n in corners}
    se = {n: e_of(simg, sslices[_sname[n]]) for n in corners}
    ratios = [we[n] / (se[n] + 1e-6) for n in corners]
    if all(0.9 <= r <= 1.1 for r in ratios):
        return True
    # 兜底同族豁免：同车任一原图同角能量 ≥ webp 的 70% → 场景纹理
    try:
        stock_dir = impd
        for jpg in stock_dir.glob("*.jpg"):
            jimg = gray(Image.open(jpg))
            jh, jw = jimg.shape
            jk = max(24, int(min(jh, jw) * 0.12))
            if all(e_of(jimg, sslices[_sname[n]]) >= 0.7 * we[n] for n in corners):
                return True
    except Exception:  # noqa: BLE001
        pass
    return False


def main() -> int:
    args = sys.argv[1:]
    only_ids = set()
    out_json = None
    it = iter(args)
    for a in it:
        if a == "--id":
            only_ids = {int(x) for x in next(it).split(",")}
        elif a == "--json":
            out_json = Path(next(it))

    if not DATA.exists():
        print(f"NOT FOUND: {DATA}")
        return 2
    data = json.loads(DATA.read_text(encoding="utf-8"))

    report = []
    n_bad = 0
    for v in data:
        if v.get("status") != "published":
            continue
        if only_ids and v["id"] not in only_ids:
            continue
        photos = v.get("photos") or []
        if not photos:
            report.append({"stock": v["stock_id"], "id": v["id"],
                           "ok": False, "issues": ["无 photos"]})
            n_bad += 1
            continue
        vres = {"stock": v["stock_id"], "id": v["id"], "ok": True, "photos": []}
        for i, rel in enumerate(photos):
            p = ROOT / rel.lstrip("/")
            if not p.is_file():
                r = {"file": rel, "ok": False, "issues": ["文件缺失"]}
            else:
                r = check_image(p, is_cover=(i == 0))
            vres["photos"].append(r)
            if not r["ok"]:
                vres["ok"] = False
        if not vres["ok"]:
            n_bad += 1
        report.append(vres)

    bad = [r for r in report if not r["ok"]]
    for r in bad:
        issues = [i for ph in r.get("photos", []) for i in ph["issues"]]
        print(f"✗ {r['stock']} (id {r['id']}): {'; '.join(issues)}")
    print(f"\n检查 {len(report)} 台 published 车辆，违规 {n_bad} 台")
    if out_json:
        out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        print(f"报告 → {out_json}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
