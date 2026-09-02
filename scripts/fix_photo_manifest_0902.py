# -*- coding: utf-8 -*-
"""照片数据修复 + 全站刷新
1) 把6台车目录中未登记的第10张图补进 vehicles.json（photo_status=complete 保持）
2) 4台 unpublished 1图车保持 unpublished（仍缺实拍组，需车商供图）
3) 重建 assets/vehicle-images.json（rebuild_site.py 的 manifest 逻辑）
4) 刷新 sitemap/feed 中的统计（如有）
"""
import json
import re
from pathlib import Path

ROOT = Path(r'D:\二手车出口网站')
DATA = ROOT / 'data' / 'vehicles.json'
data = json.load(open(DATA, encoding='utf-8'))

fixed = []
for v in data:
    vid = v['id']
    d = ROOT / 'uploads/cars' / str(vid)
    if not d.exists():
        continue
    in_json = [p.split('/')[-1] for p in v.get('photos', [])]
    real = sorted(p.name for p in d.glob('*.jpg'))
    extra = [f for f in real if f not in in_json]
    if extra:
        for f in extra:
            v['photos'].append(f'/uploads/cars/{vid}/{f}')
        v['photo_status'] = 'complete'
        fixed.append((vid, v['stock_id'], len(extra)))

DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patched vehicles:', fixed)

# ---- 重建 vehicle-images.json（与 rebuild_site.py 同规则）----
photo_manifest = {}
for folder in sorted((ROOT / 'uploads/cars').iterdir(), key=lambda p: int(p.name)):
    photos = []
    primary = folder / 'primary.jpg'
    if primary.exists():
        photos.append(f'/uploads/cars/{folder.name}/primary.jpg')
    photos.extend('/' + str(p.relative_to(ROOT)).replace('\\', '/')
                  for p in sorted(folder.iterdir())
                  if p.is_file() and p.name != 'primary.jpg')
    photo_manifest[folder.name] = photos
(ROOT / 'assets' / 'vehicle-images.json').write_text(
    json.dumps(photo_manifest, ensure_ascii=False, separators=(',', ':')))
print('vehicle-images.json rebuilt:', len(photo_manifest), 'folders')

# ---- 别名映射：photos 指向其他车目录的车辆（如 216-270 → 161-215）----
# rebuild_site.py 只按 uploads/cars/<dir>/ 目录号生成 manifest；当车辆 photos 引用
# 其他目录时，详情页相册取不到图。这里为每台这样的车追加 key = photos[0] 的目录内容。
data2 = json.load(open(DATA, encoding='utf-8'))
manifest = json.loads((ROOT / 'assets' / 'vehicle-images.json').read_text(encoding='utf-8'))
aliased = 0
for v in data2:
    vid = str(v['id'])
    if vid not in manifest and v.get('photos'):
        srcdir = v['photos'][0].split('/')[3]
        if srcdir in manifest:
            manifest[vid] = list(manifest[srcdir])
            aliased += 1
(ROOT / 'assets' / 'vehicle-images.json').write_text(
    json.dumps(manifest, ensure_ascii=False, separators=(',', ':')))
print('aliased keys:', aliased, 'total keys:', len(manifest))

# ---- 统计 ----
pub = [v for v in data if v.get('status') == 'published']
print('published:', len(pub), 'total photos:', sum(len(v['photos']) for v in pub))
