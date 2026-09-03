# -*- coding: utf-8 -*-
"""清理损坏占位图并重建受影响的车辆详情页。

背景
----
uploads/cars 下有 197 个 JPEG 打开失败（严格模式下 OSError: image file is
truncated）。经核验这些文件只有 2 种唯一内容（105 次 + 92 次），是批量复制
的占位图，生成时即写坏，无源可恢复，且不是真实车照。

影响面：四语车辆页 zh/en/ru/ar 共引用 197 处，涉及 120 台车（每台 6 张里
坏 1-2 张，无整车全坏）。

做法
----
1. 备份损坏文件到 .workbuddy/broken_backup/
2. 从 assets/vehicle-images.json 移除对应引用
3. 删除损坏文件
4. 复用 build_v2.py 的 detail() 只重建受影响车辆页（不重跑全站，避免
   把 v6 首页打回 v5）
5. 重建 sitemap-images.xml，回写 data/vehicles.json

用法
----
  python scripts/repair_broken_photos.py dry     # 只报告，不改动
  python scripts/repair_broken_photos.py run     # 执行修复
"""
import json
import pathlib
import shutil
import sys
from collections import defaultdict

from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = False  # 严格模式，截断即视为损坏

ROOT = pathlib.Path(__file__).resolve().parent.parent
UPLOADS = ROOT / 'uploads' / 'cars'
INDEX = ROOT / 'assets' / 'vehicle-images.json'
VEHICLES = ROOT / 'data' / 'vehicles.json'
BACKUP = ROOT / '.workbuddy' / 'broken_backup'
BUILD = ROOT / 'scripts' / 'build_v2.py'
LANGS = ['en', 'zh', 'ru', 'ar']

# build_v2.py 中 V=enrich_all(V) 所在行（含）之前为可安全复用的定义段
# 186-186 行含 vehicle-images.json 磁盘存在性过滤（不存在的引用会被剔除），
# 必须包含，否则重建页面仍会引用已删除的坏图文件。
INIT_LINE = 196


def find_broken():
    """返回损坏文件列表（严格模式打不开的图片）"""
    out = []
    for f in sorted(UPLOADS.rglob('*.jpg')):
        try:
            im = Image.open(f)
            im.load()
        except Exception:
            out.append(f)
    return out


def url_of(path):
    return '/' + path.relative_to(ROOT).as_posix()


def load_build_env():
    """执行 build_v2.py 的定义段，拿到 detail()/V/write() 等，不触发全站构建"""
    src = BUILD.read_text(encoding='utf-8').splitlines()
    code = '\n'.join(src[:INIT_LINE])
    ns = {'__file__': str(BUILD), '__name__': 'build_v2_partial'}
    exec(compile(code, str(BUILD), 'exec'), ns)
    return ns


def cmd_dry():
    broken = find_broken()
    idx = json.loads(INDEX.read_text(encoding='utf-8'))
    broken_urls = {url_of(f) for f in broken}
    hit_urls = {p for v in idx.values() for p in v if p in broken_urls}

    by_car = defaultdict(int)
    for u in hit_urls:
        by_car[u.split('/')[3]] += 1

    print(f'损坏文件        {len(broken)} 个')
    print(f'索引中引用      {len(hit_urls)} 条')
    print(f'涉及车辆        {len(by_car)} 台')
    print(f'需重建页面      {len(by_car) * len(LANGS)} 个（4 语言）')
    print(f'备份目录        {BACKUP}')
    print('\n各车损坏张数（前 10）:')
    for c in sorted(by_car, key=lambda x: int(x))[:10]:
        print(f'  car{c}: {by_car[c]} 张')
    print('\n[DRY] 未做任何改动')


def cmd_run():
    broken = find_broken()
    if not broken:
        print('没有损坏文件，无需修复')
        return

    broken_urls = {url_of(f) for f in broken}
    BACKUP.mkdir(parents=True, exist_ok=True)

    # 1) 备份
    for f in broken:
        dst = BACKUP / f'{f.parent.name}__{f.name}'
        if not dst.exists():
            shutil.copy2(f, dst)
    print(f'已备份 {len(broken)} 个文件 -> {BACKUP}')

    # 2) 清理索引
    idx = json.loads(INDEX.read_text(encoding='utf-8'))
    removed = 0
    for cid, photos in idx.items():
        kept = [p for p in photos if p not in broken_urls]
        removed += len(photos) - len(kept)
        idx[cid] = kept
    INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + '\n',
                     encoding='utf-8')
    print(f'索引清理 {removed} 条 -> {INDEX.name}')

    # 3) 删除损坏文件
    for f in broken:
        f.unlink()
    print(f'已删除 {len(broken)} 个损坏文件')

    # 4) 重建受影响车辆页
    env = load_build_env()
    V = env['V']
    detail = env['detail']
    write = env['write']
    R = env['R']
    BASE = env['BASE']
    esc = env['esc']
    title_for = env['title_for']

    affected = {u.split('/')[3] for u in broken_urls}
    published = [v for v in V if v.get('status') == 'published']
    rebuilt = 0
    for v in published:
        if str(v['id']) not in affected:
            continue
        for lang in LANGS:
            write(R / lang / f'cars/{v["id"]}/index.html', detail(lang, v))
            rebuilt += 1
    skipped = len(affected) - len({str(v['id']) for v in published} & affected)
    print(f'重建车辆页 {rebuilt} 个'
          + (f'（{skipped} 台未发布，跳过）' if skipped else ''))

    # 5) 重建 sitemap-images.xml（仅收录已发布车辆的现存图片）
    image_urls = ''.join(
        f'<url><loc>{BASE}/en/cars/{v["id"]}/</loc>'
        + ''.join(
            f'<image:image><image:loc>{BASE}{p}</image:loc>'
            f'<image:caption>{esc(title_for(v, "en"))}</image:caption></image:image>'
            for p in v['photos']
        )
        + '</url>'
        for v in published
    )
    write(R / 'sitemap-images.xml',
          '<?xml version="1.0" encoding="UTF-8"?><urlset '
          'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
          + image_urls + '</urlset>')
    print('重建 sitemap-images.xml')

    # 6) 回写 vehicles.json，保持数据源一致
    VEHICLES.write_text(json.dumps(V, ensure_ascii=False, indent=2) + '\n',
                        encoding='utf-8')
    left = sum(len(v['photos']) for v in V)
    print(f'回写 {VEHICLES.name}（剩余图片引用 {left} 条）')

    # 7) 复检
    still = find_broken()
    print(f'\n复检：剩余损坏文件 {len(still)} 个')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'dry'
    {'dry': cmd_dry, 'run': cmd_run}[cmd]()
