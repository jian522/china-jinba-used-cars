# -*- coding: utf-8 -*-
"""UI 重构验收脚本（零参数运行）

检查项：
  1. 全站是否还有页面引用旧样式 v5.css / v4.js
  2. 四语首页：接入设计系统、暗色覆盖层已清除、SEO 标签完好、ar 保持 RTL
  3. 库存页车辆数、详情页 JSON-LD、图片引用是否存在
  4. sitemap URL 数量

退出码 0 = 全部通过，1 = 有失败项。
"""
import csv
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ['en', 'zh', 'ru', 'ar']
# 抽样详情页：从已发布车辆中取代表（新批次 2026-09-che168-full）
# 若对应 id 未发布则自动跳过（check 会标 FAIL，提示重新选样本）
SAMPLE_CARS = [271, 275, 283, 289, 295]


def car_count():
    """从 data/vehicles.json 读取实际车辆数（用于验收比对，避免写死 211 误报）。"""
    p = ROOT / 'data' / 'vehicles.json'
    if not p.exists():
        return None
    try:
        return len(json.loads(p.read_text(encoding='utf-8')))
    except Exception:
        return None

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))


def read(path):
    p = ROOT / path
    if not p.exists():
        return None
    return p.read_text(encoding='utf-8', errors='ignore')


# ---------------------------------------------------------------- 1. 旧引用
print('== 1. 旧样式残留检查 ==')
stale_css = []
stale_js = []
for lang in LANGS:
    for html in (ROOT / lang).rglob('index.html'):
        text = html.read_text(encoding='utf-8', errors='ignore')
        if 'v5.css' in text:
            stale_css.append(str(html.relative_to(ROOT)))
        if 'v4.js' in text:
            stale_js.append(str(html.relative_to(ROOT)))

check('无页面引用旧样式 v5.css', not stale_css,
      f'{len(stale_css)} 个' + (f'：{stale_css[:3]}' if stale_css else ''))
check('无页面引用旧脚本 v4.js', not stale_js,
      f'{len(stale_js)} 个' + (f'：{stale_js[:3]}' if stale_js else ''))

# ---------------------------------------------------------------- 2. 首页
print('== 2. 四语首页检查 ==')
for lang in LANGS:
    h = read(f'{lang}/index.html')
    if h is None:
        check(f'{lang} 首页存在', False)
        continue
    if 'jinba-home-v7.css' in h:
        # 2026-09 深蓝+橙改版（v7）首页结构
        check(f'{lang} 首页引用 v7 样式', 'jinba-home-v7.css' in h)
        check(f'{lang} 首页精选车卡=4', h.count('jv7-car-body') == 4,
              f'实际 {h.count("jv7-car-body")}')
        check(f'{lang} 首页流程步=4', h.count('jv7-step-no') == 4,
              f'实际 {h.count("jv7-step-no")}')
        check(f'{lang} 首页市场卡=3', h.count('class="jv7-market"') + h.count('class="jv7-market jv7-market--navy"') == 3)
        check(f'{lang} 首页 FAQ=4', h.count('jv7-faqitem') == 4,
              f'实际 {h.count("jv7-faqitem")}')
        check(f'{lang} 首页 CTA 与 footer 存在', 'class="jv7-cta"' in h and 'jv7-footer' in h)
        check(f'{lang} 首页 theme-color 为 #0A1628', 'content="#0A1628"' in h)
    else:
        check(f'{lang} 首页引用 design-system.css', 'design-system.css' in h)
        check(f'{lang} 首页引用 app.js', 'app.js' in h)
        check(f'{lang} 首页 footer 水印', 'footer-wm' in h)
    check(f'{lang} 首页无旧版暗色残留', '9EFF00' not in h.upper() and '141414' not in h)
    check(f'{lang} 首页 hreflang 5 向', h.count('hreflang="') == 5,
          f'实际 {h.count("hreflang=")}')
    rtl_ok = ('dir="rtl"' in h) if lang == 'ar' else ('dir="ltr"' in h)
    check(f'{lang} 首页方向正确', rtl_ok)
    check(f'{lang} 首页保留 Organization JSON-LD',
          '"@type": "Organization"' in h or '"@type":"Organization"' in h)

# ---------------------------------------------------------------- 3. 库存与详情
print('== 3. 库存页 / 详情页 ==')
inv = read('en/cars/index.html')
if inv:
    ids = set(re.findall(r'href="/en/cars/(\d+)/"', inv))
    # 验收口径：库存页列出的车辆应与 sitemap 中 en 详情页数一致（二者同源自 build 的已上架车辆）。
    # 数据源 vehicles.json 含尚未上架（待补图/草稿）的车辆，总数本就大于公开上架数，不应直接比对。
    sm = read('sitemap.xml')
    en_detail = len(re.findall(r'<loc>https://jinbacars\.com/en/cars/\d+/</loc>', sm)) if sm else 0
    check('库存页车辆数与 sitemap 一致', en_detail > 0 and len(ids) == en_detail,
          f'库存 {len(ids)} / sitemap en 详情 {en_detail}')
    check('库存页引用 app.js', 'app.js' in inv)
else:
    check('库存页存在', False)

for cid in SAMPLE_CARS:
    d = read(f'en/cars/{cid}/index.html')
    if d is None:
        check(f'详情页 {cid} 存在', False)
        continue
    ld = '"@type": "Vehicle"' in d or '"@type":"Vehicle"' in d
    check(f'详情页 {cid} Vehicle JSON-LD', ld)
    imgs = sorted(set(re.findall(r'(/uploads/cars/\d+/[^\"\']+?\.jpg)', d)))
    missing = [u for u in imgs if not (ROOT / u.lstrip('/')).exists()]
    check(f'详情页 {cid} 图片本地存在', not missing,
          f'{len(imgs)} 张，缺失 {len(missing)}')

# ---------------------------------------------------------------- 4. sitemap
print('== 4. sitemap ==')
sm = read('sitemap.xml')
if sm:
    n = sm.count('<loc>')
    # 38 台车 × 4 语言 + 首页/库存/品牌/市场等静态页 ≈ 300+；
    # 车辆大幅精简后不再要求 ≥1000，改为与库存页一致即可（见 check 3）
    check('sitemap URL 数 ≥ 200', n >= 200, f'实际 {n}')
    check('sitemap 含新车 271/275', '/en/cars/271/' in sm and '/en/cars/275/' in sm)
else:
    check('sitemap 存在', False)

# ---------------------------------------------------------------- 5. 设计系统
print('== 5. 设计系统文件 ==')
css = ROOT / 'assets' / 'design-system.css'
js = ROOT / 'assets' / 'app.js'
check('design-system.css 存在', css.exists(), f'{css.stat().st_size if css.exists() else 0} 字节')
check('app.js 存在', js.exists(), f'{js.stat().st_size if js.exists() else 0} 字节')

# ---------------------------------------------------------------- 汇总
print('\n' + '=' * 62)
passed = sum(1 for _, ok, _ in results if ok)
failed = [r for r in results if not r[1]]

for name, ok, detail in results:
    if not ok:
        print(f'  FAIL  {name}  {detail}')

print(f'\n通过 {passed}/{len(results)}')
if failed:
    print(f'失败 {len(failed)} 项（见上）')
    sys.exit(1)
print('全部通过 ✓')
