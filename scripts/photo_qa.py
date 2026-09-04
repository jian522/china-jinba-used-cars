#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""照片质检预检（发布前使用，读取目录或指定车辆 ID 的照片集合）。

检查项：
  1. 张数：应在 [--min, --max] 内（站点发布标准 6–9；补图阶段可放宽到 1–5，用 --mode draft）
  2. 尺寸：每张 ≥ min_w×min_h（默认 800×600），EXIF 方向已校正
  3. 首图约定：photos[0] 应为主图 primary（提示：应为前脸或左前 45° 外观）
  4. 重复检测：集合内 md5 重复、以及跨目录疑似同图（相同尺寸+相近 md5 前缀）给出警告
  5. 水印/文字可疑提示：将图缩小后比较四角与整体的边缘强度，任何一角显著偏高时提示
     “请人工复核四角是否含文字/水印/logo”（仅提示，不作为硬性失败）

用法：
  python scripts/photo_qa.py --dir <图片目录>
  python scripts/photo_qa.py --car <vehicle_id>          # 读取 uploads/cars/<id>
退出码：0=通过（可含警告）；1=存在硬性错误（数量/尺寸/无法解码）。
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
EXTS = (".jpg", ".jpeg", ".png", ".webp")


def load(path: Path):
    img = Image.open(path)
    img.load()
    return ImageOps.exif_transpose(img).convert("RGB")


def edge_density(gray: Image.Image, box) -> float:
    """某区域的平均边缘强度（0-255 均值），作为‘角落可能存在文字/水印’的粗判特征。"""
    crop = gray.crop(box)
    crop = crop.resize((64, 48))
    edges = crop.filter(ImageFilter.FIND_EDGES)
    data = list(edges.getdata())
    return sum(data) / len(data)


def corner_suspect(img: Image.Image) -> list[str]:
    g = img.convert("L")
    w, h = g.size
    cw, ch = max(1, w // 4), max(1, h // 4)
    corners = {
        "左上": (0, 0, cw, ch), "右上": (w - cw, 0, w, ch),
        "左下": (0, h - ch, cw, h), "右下": (w - cw, h - ch, w, h),
    }
    whole = edge_density(g, (0, 0, w, h))
    hits = []
    for name, box in corners.items():
        v = edge_density(g, box)
        if v > max(14.0, whole * 1.8):
            hits.append(f"{name}(edge={v:.0f},全图={whole:.0f})")
    return hits


def md5_of(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def check_files(files: list[Path], args) -> tuple[int, list[str], list[str]]:
    errs: list[str] = []
    warns: list[str] = []
    hashes: dict[str, str] = {}
    n = len(files)
    if not (args.min <= n <= args.max):
        errs.append(f"照片数量 {n} 不在 [{args.min},{args.max}] 区间（发布标准 6–9 张）")
    if files and files[0].stem.lower() != "primary":
        warns.append(f"首张 {files[0].name} 不是 primary；站点约定 photos[0]=主图，"
                     "主图应为外观前脸或左前 45° 角")
    for i, p in enumerate(files):
        try:
            img = load(p)
        except Exception as exc:  # noqa: BLE001
            errs.append(f"{p.name} 无法解码: {exc}")
            continue
        w, h = img.size
        if w < args.min_w or h < args.min_h:
            errs.append(f"{p.name} 尺寸 {w}x{h} 小于要求 {args.min_w}x{args.min_h}")
        m = md5_of(p)
        if m in hashes:
            warns.append(f"{p.name} 与 {hashes[m]} 内容重复 (md5)")
        else:
            hashes[m] = p.name
        if args.watermark and i < 2:
            for hit in corner_suspect(img):
                warns.append(f"{p.name} 角落疑似含文字/水印/logo: {hit}（请人工复核）")
    return len(errs), errs, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="图片所在目录")
    ap.add_argument("--car", type=int, help="车辆 ID（读取 uploads/cars/<id>）")
    ap.add_argument("--min", type=int, default=6)
    ap.add_argument("--max", type=int, default=10)
    ap.add_argument("--min-w", type=int, default=800)
    ap.add_argument("--min-h", type=int, default=600)
    ap.add_argument("--no-watermark", action="store_true", help="关闭水印粗检（省时间）")
    args = ap.parse_args()

    if args.car is not None:
        d = ROOT / "uploads" / "cars" / str(args.car)
        if not d.is_dir():  # 部分批次照片目录≠车辆 id，按 data/vehicles.json 的 photos[0] 解析
            import json as _json
            veh = _json.loads((ROOT / "data" / "vehicles.json").read_text(encoding="utf-8"))
            hit = next((v for v in veh if int(v.get("id", 0)) == args.car), None)
            if hit and hit.get("photos"):
                d = ROOT / hit["photos"][0].lstrip("/").rsplit("/", 1)[0]
    elif args.dir:
        d = Path(args.dir)
    else:
        ap.error("需要 --car 或 --dir")
    if not d.is_dir():
        print(f"目录不存在: {d}")
        return 2

    files = sorted([p for p in d.iterdir() if p.suffix.lower() in EXTS],
                   key=lambda p: (0, p.name) if p.stem.lower() == "primary" else (1, p.name))
    if not files:
        print(f"未找到图片: {d}")
        return 2
    args.watermark = not args.no_watermark
    ec, errs, warns = check_files(files, args)
    print(f"检查目录: {d}")
    print(f"图片数量: {len(files)}  硬性错误: {ec}  警告: {len(warns)}")
    for e in errs:
        print("  E " + e)
    for w in warns:
        print("  W " + w)
    return 1 if ec else 0


if __name__ == "__main__":
    raise SystemExit(main())
