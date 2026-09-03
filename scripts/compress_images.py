#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量压缩车辆图片

背景：uploads 下 1455 张 jpg 共 731 MB，其中 645 张超过 300KB（553 张超 1MB）。
这些图都是固定的 1152x864，只是 JPEG 质量被设成近无损，压到 q85 可省约 90% 体积，
对非洲/中东目标市场的加载速度是决定性影响。

策略：只降质量、不改尺寸；原图先备份到 .workbuddy/backup_images/（已被 .gitignore 排除）；
单张压缩失败（文件损坏等）就跳过并保留原图，绝不写出半成品。

用法：
  python scripts/compress_images.py check              # 只体检，不改任何文件
  python scripts/compress_images.py run [quality]      # 备份 + 压缩（默认 q85）
"""
import io
import shutil
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / 'uploads'
BACKUP = ROOT / '.workbuddy' / 'backup_images'
THRESHOLD = 300 * 1024  # 小于这个体积不动


def scan():
    fs = [f for f in IMG_DIR.rglob('*.jpg') if f.stat().st_size > THRESHOLD]
    fs.sort()
    return fs


def check():
    """体检：跳过损坏文件，不动任何文件"""
    fs = list(IMG_DIR.rglob('*.jpg'))
    broken, total = [], sum(f.stat().st_size for f in fs)
    for f in fs:
        try:
            im = Image.open(f)
            im.load()
        except Exception as e:
            broken.append((f.as_posix(), type(e).__name__, str(e)[:50]))
    need = scan()
    print(f'图片总数 {len(fs)}  总体积 {total / 1048576:.0f} MB')
    print(f'需压缩(>{THRESHOLD // 1024}KB) {len(need)} 张, '
          f'{sum(f.stat().st_size for f in need) / 1048576:.0f} MB')
    print(f'损坏文件 {len(broken)} 个:')
    for p, t, e in broken:
        print(f'  {p} -> {t}: {e}')
    return broken


def compress(quality=85):
    fs = scan()
    before = sum(f.stat().st_size for f in fs)
    print(f'待压缩 {len(fs)} 张，{before / 1048576:.0f} MB，目标质量 q{quality}', flush=True)
    print(f'备份原图到 {BACKUP}', flush=True)

    t0 = time.time()
    BACKUP.mkdir(parents=True, exist_ok=True)
    done, skipped, saved = 0, [], 0
    for i, f in enumerate(fs, 1):
        rel = f.relative_to(IMG_DIR)
        try:
            im = Image.open(f)
            im.load()
        except Exception as e:
            skipped.append((rel.as_posix(), f'{type(e).__name__}: {str(e)[:40]}'))
            continue
        orig = f.stat().st_size
        dst = BACKUP / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(f, dst)
        try:
            buf = io.BytesIO()
            im.convert('RGB').save(buf, 'JPEG', quality=quality,
                                   optimize=True, progressive=True)
            new = buf.tell()
            if new >= orig:  # 压缩反而变大就别动
                continue
            f.write_bytes(buf.getvalue())
            saved += orig - new
            done += 1
        except Exception as e:
            skipped.append((rel.as_posix(), f'写入失败 {type(e).__name__}'))
            continue
        if i % 100 == 0:
            el = time.time() - t0
            print(f'  {i}/{len(fs)}  {el:.0f}s  已省 {saved / 1048576:.0f} MB', flush=True)

    el = time.time() - t0
    after = sum(f.stat().st_size for f in fs)
    print(f'完成 {done} 张，跳过 {len(skipped)} 个，用时 {el:.0f}s')
    print(f'体积 {before / 1048576:.0f} MB -> {after / 1048576:.0f} MB '
          f'(省 {(1 - after / before) * 100:.0f}%)')
    print(f'平均单张 {before / len(fs) / 1024:.0f}KB -> {after / len(fs) / 1024:.0f}KB')
    if skipped:
        print('跳过清单:')
        for p, e in skipped:
            print(f'  {p} -> {e}')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'check':
        check()
    elif cmd == 'run':
        compress(int(sys.argv[2]) if len(sys.argv) > 2 else 85)
    else:
        print(__doc__)
