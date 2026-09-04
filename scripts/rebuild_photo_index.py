#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 uploads/cars/<id>/ 目录重建 assets/vehicle-images.json 图片索引。
build_v2.py 依赖该文件把每台车的真实照片路径并入车辆记录。
格式：{ "7": ["/uploads/cars/7/primary.jpg", "/uploads/cars/7/7007_1.jpg", ...], ... }
主图 primary.jpg 始终排在首位。
"""
import json
from pathlib import Path

ROOT = Path('D:/二手车出口网站')
cars = ROOT / 'uploads' / 'cars'
idx = {}
exts = ('.jpg', '.jpeg', '.png', '.webp')
for d in sorted(cars.iterdir()):
    if not d.is_dir() or not d.name.isdigit():
        continue
    imgs = [f'/uploads/cars/{d.name}/{f.name}'
            for f in sorted(d.iterdir())
            if f.suffix.lower() in exts]
    if not imgs:
        continue
    imgs.sort(key=lambda p: (0 if p.endswith('/primary.jpg') else 1, p))
    idx[d.name] = imgs
out = ROOT / 'assets' / 'vehicle-images.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(idx, ensure_ascii=False), encoding='utf-8')
print(f'wrote {len(idx)} vehicles, {sum(len(v) for v in idx.values())} photos -> {out}')
