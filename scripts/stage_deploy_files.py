#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 null 分隔清单复制文件到部署暂存目录（正确处理中文/空格路径）。"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path("d:/二手车出口网站")
SRC_MANIFEST = ROOT / "_pages_deploy" / "_manifest_z.txt"
DEST = ROOT / "_pages_deploy" / "site"

files = SRC_MANIFEST.read_text(encoding="utf-8").split("\0")
files = [f for f in files if f.strip()]
print(f"TOTAL {len(files)}", flush=True)

copied = skipped = 0
for i, rel in enumerate(files):
    src = ROOT / rel
    dst = DEST / rel
    if not src.is_file():
        skipped += 1
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied += 1
    if (i + 1) % 1000 == 0:
        print(f"PROGRESS {i+1}/{len(files)}", flush=True)

size = sum(f.stat().st_size for f in DEST.rglob("*") if f.is_file())
print(f"DONE copied={copied} skipped={skipped} size={size/1024/1024:.1f}MB", flush=True)
