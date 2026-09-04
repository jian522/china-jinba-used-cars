#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 uploads/cars/<id> 下的每张车辆图生成 300px 缩略 webp（<stem>.th.webp）。

用途：车辆详情页的缩略图网格改用小图，主图/灯箱/分享图仍用原图，
从而显著降低移动端详情页加载体积（9 张全尺寸 → 9 张小图）。

幂等：目标已存在且比源新则跳过。
用法：python scripts/make_thumbs.py [--width 300] [--quality 80]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
EXTS = (".jpg", ".jpeg", ".png", ".webp")


def make(path: Path, width: int, quality: int) -> Path | None:
    target = path.with_name(path.stem + ".th.webp")
    try:
        if target.exists() and target.stat().st_mtime >= path.stat().st_mtime:
            return None
        img = Image.open(path)
        img.load()
        img = ImageOps.exif_transpose(img).convert("RGB")
        if img.width > width:
            h = round(img.height * width / img.width)
            img = img.resize((width, h), Image.LANCZOS)
        target.parent.mkdir(parents=True, exist_ok=True)
        img.save(target, "WEBP", quality=quality, method=6)
        return target
    except Exception as exc:  # noqa: BLE001
        print(f"  !! {path} -> {exc}")
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=300)
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--cars", help="可选：只处理指定车辆 id 目录（逗号分隔）")
    args = ap.parse_args()

    base = ROOT / "uploads" / "cars"
    car_dirs = []
    if args.cars:
        for c in args.cars.split(","):
            d = base / c.strip()
            if d.is_dir():
                car_dirs.append(d)
    else:
        car_dirs = sorted((p for p in base.iterdir() if p.is_dir()),
                          key=lambda p: int(p.name) if p.name.isdigit() else 1 << 30)
    made = skipped = failed = 0
    for d in car_dirs:
        for p in sorted(d.iterdir()):
            if p.suffix.lower() not in EXTS or p.stem.endswith(".th"):
                continue
            r = make(p, args.width, args.quality)
            if r is None:
                skipped += 1
            else:
                made += 1
                if made % 200 == 0:
                    print(f"  {made} ...", flush=True)
    print(f"done: created {made}, skipped {skipped} (已存在或源缺失)")


if __name__ == "__main__":
    main()
