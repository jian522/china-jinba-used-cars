#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取站点所有页面用到的 CSS 类名，用于重建 design-system.css 时查漏。"""
import re
from pathlib import Path

ROOT = Path('D:/二手车出口网站')
files = [
    ROOT / 'scripts' / 'build_v2.py',
    ROOT / 'scripts' / 'rebuild_home_v6.py',
    ROOT / '404.html',
    ROOT / 'en' / 'index.html',
    ROOT / 'en' / 'cars' / 'index.html',
    ROOT / 'en' / 'cars' / '7' / 'index.html',
    ROOT / 'en' / 'about' / 'index.html',
    ROOT / 'en' / 'contact' / 'index.html',
    ROOT / 'en' / 'markets' / 'index.html',
    ROOT / 'en' / 'brands' / 'byd' / 'index.html',
    ROOT / 'admin' / 'index.html',
    ROOT / 'admin' / 'login' / 'index.html',
    ROOT / 'admin' / 'photo-coverage' / 'index.html',
]
classes = set()
miss = []
for f in files:
    if not f.exists():
        miss.append(str(f))
        continue
    txt = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.findall(r'class="([^"]+)"', txt):
        for c in m.split():
            classes.add(c)
print('=== MISSING FILES ===')
for m in miss:
    print(' ', m)
print('=== CLASSES (%d) ===' % len(classes))
for c in sorted(classes):
    print(c)
