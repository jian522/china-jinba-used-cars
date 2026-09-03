"""评估截断 JPEG 的实际可用比例。

先以严格模式找出打开失败的文件，再开启容错重新解码，
统计"有效图像高度 / 声明高度"来判断残缺程度。
"""
import collections
import pathlib

from PIL import Image, ImageFile

UP = pathlib.Path(__file__).resolve().parent.parent / 'uploads' / 'cars'

# 1) 严格模式找损坏
ImageFile.LOAD_TRUNCATED_IMAGES = False
broken = []
for f in sorted(UP.rglob('*.jpg')):
    try:
        im = Image.open(f)
        im.load()
    except Exception:
        broken.append(f)
print(f'严格模式损坏: {len(broken)} 个')

# 2) 容错模式评估
ImageFile.LOAD_TRUNCATED_IMAGES = True
buckets = collections.Counter()
sizes = []
detail = []
for f in broken:
    try:
        im = Image.open(f).convert('L')
        im.load()
        w, h = im.size
        px = im.getdata()
        last = 0
        # 从底部往上找第一行有内容的扫描行
        for y in range(h - 1, -1, -1):
            row = px[y * w:(y + 1) * w]
            if len(set(row)) > 4:
                last = y + 1
                break
        r = last / h if h else 0
        sizes.append(f.stat().st_size)
        detail.append((r, f))
        buckets['完整 ≥98%' if r >= 0.98 else
                 '95-98%' if r >= 0.95 else
                 '90-95%' if r >= 0.90 else
                 '80-90%' if r >= 0.80 else
                 '<80% 严重'] += 1
    except Exception as e:
        buckets['无法解码'] += 1
        detail.append((0, f))

n = len(broken)
print(f'\n容错解码结果（共 {n} 个）:')
for k in ['完整 ≥98%', '95-98%', '90-95%', '80-90%', '<80% 严重', '无法解码']:
    if buckets[k]:
        print(f'  {k:12} {buckets[k]:4} 个  ({buckets[k]/n*100:.0f}%)')

ok = buckets['完整 ≥98%'] + buckets['95-98%']
print(f'\n基本完整可用(≥95%): {ok}/{n} ({ok/n*100:.0f}%)')
if sizes:
    print(f'损坏文件平均体积: {sum(sizes)/len(sizes)/1024:.0f} KB')

bad = sorted([d for d in detail if d[0] < 0.9], key=lambda x: x[0])[:10]
if bad:
    print('\n残缺最严重的 10 个:')
    for r, f in bad:
        print(f'  {r*100:5.1f}%  {f.relative_to(UP.parent)}')
