#!/usr/bin/env python3
"""
全自动优化脚本：修复多照片、编码乱码、生成页面、部署上线
"""
import json, os, re, base64, urllib.request, urllib.error, sys
from collections import defaultdict

BASE = '/sessions/elegant-charming-hypatia/mnt/金霸二手车网站'
TOKEN = 'YOUR_GITHUB_TOKEN'
REPO = 'jian522/usedchinesecars'

os.chdir(BASE)

# ============================================================
# STEP 1: 构建图片映射
# ============================================================
print('\n' + '='*60)
print('STEP 1/4: 构建图片映射')
print('='*60)

cars_json_path = os.path.join(BASE, 'cars-data.json')
js_path = os.path.join(BASE, 'js', 'cars-data.js')

# 读取cars-data.json—如果有就用它作为数据源
if os.path.exists(cars_json_path):
    with open(cars_json_path, 'r', encoding='utf-8') as f:
        cars = json.load(f)
    print(f'  从 cars-data.json 读取 {len(cars)} 条记录')
else:
    # fallback: 从 cars-data.js 提取
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'var CARS_DATA\s*=\s*(\[.*?\]);', content, re.DOTALL)
    if match:
        cars = json.loads(match.group(1))
        print(f'  从 cars-data.js 提取 {len(cars)} 条记录')
    else:
        print('  无法找到车辆数据！')
        sys.exit(1)

# 扫描所有图片
cars_dir = os.path.join(BASE, 'uploads', 'cars')
all_images = [f for f in os.listdir(cars_dir) if f.endswith('.jpg')]

# 按车ID分组
image_map = defaultdict(list)
for img in all_images:
    parts = img.replace('.jpg', '').split('_')
    if len(parts) >= 2 and parts[0] == 'car' and parts[1].isdigit():
        cid = int(parts[1])
        image_map[cid].append(img)

for cid in image_map:
    image_map[cid].sort()

print(f'  共 {len(all_images)} 张图片，分布在 {len(image_map)} 台车')

# 写入每辆车的图片列表
stats = defaultdict(int)
for car in cars:
    cid = car['id']
    imgs = image_map.get(cid, [])
    car['images'] = imgs
    stats[len(imgs)] += 1

print(f'  图片统计: {dict(stats)}')

# 保存更新后的JSON
with open(cars_json_path, 'w', encoding='utf-8') as f:
    json.dump(cars, f, ensure_ascii=False, indent=2)
print('  已更新 cars-data.json')

# ============================================================
# STEP 2: 重写 generate_pages.py (多照片+修复编码)
# ============================================================
print('\n' + '='*60)
print('STEP 2/4: 重写 generate_pages.py')
print('='*60)

script_content = '''#!/usr/bin/env python3
"""生成所有160辆车详情页 - 自动优化版"""

import json, os, re, sys
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_data():
    """加载车辆数据和图片映射"""
    json_path = os.path.join(BASE_DIR, 'cars-data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\\u4e00-\\u9fff]+', '-', text)
    text = text.strip('-')
    return text[:80]

def get_en_model(car):
    """获取英文车型简称"""
    model = car['model']
    brand = car['brand']

    # 品牌级别映射
    if brand == 'BYD':
        if '海豹' in model: return 'Seal'
        if '海鸥' in model: return 'Seagull'
        if '海豚' in model: return 'Dolphin'
        if '海狮' in model: return 'Sealion'
        if '汉' in model: return 'Han'
        if '唐' in model: return 'Tang'
        if '秦' in model: return 'Qin'
        if '宋' in model: return 'Song'
        if '元' in model: return 'Yuan'
        if '元' in model: return 'Yuan'
    if brand == 'Chery':
        if '瑞虎' in model: return 'Tiggo'
        if '艾瑞泽' in model: return 'Arrizo'
        if '欧萌' in model: return 'Omoda'
    if brand == 'Haval':
        if '大狗' in model: return 'Big Dog'
        if 'H6' in model: return 'H6'
        if 'H9' in model: return 'H9'
        if '初恋' in model: return 'Chulian'
        if '猛龙' in model: return 'Xiaolong'
        if '枭龙' in model: return 'Xiaolong MAX'
        if 'F7' in model: return 'F7'
        if 'M6' in model: return 'M6'
    if brand == 'MG': return 'MG'
    if brand == 'Jetour': return 'Jetour'
    if brand == 'Great Wall':
        if '炮' in model: return 'Poer'
        if '风骏' in model: return 'Steed'
        if '金刚' in model: return 'King Kong'
    if brand == 'Roewe':
        if '飞凡' in model: return 'Feifan'
        if 'RX5' in model: return 'RX5'
        if 'i5' in model: return 'i5'
        if 'iMAX8' in model: return 'iMAX8'
    if brand == 'Avatr': return 'Avatr'
    if brand == 'NIO': return 'NIO'
    if brand == 'XPeng': return 'XPeng'
    if brand == 'Zeekr': return 'Zeekr'
    if brand == 'Toyota': return 'Toyota'
    if brand == 'Volkswagen': return 'Volkswagen'
    if brand == 'Geely':
        if '缤越' in model: return 'Binray'
        if '星越' in model: return 'Xingyue'
        if '帝豪' in model: return 'Emgrand'
    if brand == 'Changan':
        if 'CS75' in model: return 'CS75 PLUS'
        if 'CS55' in model: return 'CS55 PLUS'
        if '逸动' in model: return 'Eado'
    if brand == 'Li Auto': return 'Li Auto'
    if brand == 'AITO': return 'AITO'
    if brand == 'Luxeed': return 'Luxeed'
    if brand == 'GAC':
        if '传祺' in model: return 'Trumpchi'

    # 提取英文部分
    parts = re.split(r'[\\d\\s]+', model)
    for p in parts:
        p = p.strip()
        if re.match(r'^[A-Za-z]', p):
            return p
    return model[:20]

def build_gallery_html(car):
    """生成多照片画廊HTML"""
    images = car.get('images', [car.get('image', '')] if car.get('image') else [])
    if not images:
        return '<div class="detail-img-main" style="background:#eee"><p style="color:#999">No image</p></div>'

    # 主图
    main_img = '../' + images[0]

    # 缩略图
    thumbs = ''
    for i, img in enumerate(images):
        src = '../' + img
        cls = 'active' if i == 0 else ''
        thumbs += f'''
            <button class="thumb {cls}" onclick="setMain(\\'{src}\\', this)" aria-label="Photo {i+1}">
                <img src="{src}" alt="Photo {i+1}">
            </button>'''

    # 缩略图数量
    count_badge = ''
    if len(images) > 1:
        count_badge = f'<span class="photo-count">{len(images)} photos</span>'

    html = f'''
            <div class="mainphoto">
                <img id="mainphoto" width="720" height="540" fetchpriority="high" src="{main_img}" alt="{car['brand']} {car['model']}">
                {count_badge}
            </div>
            <div class="thumbs">
                {thumbs}
            </div>'''
    return html

def generate_page(car):
    """生成单台车页面"""
    brand = car['brand']
    model = car['model']
    year = car['year']
    price_label = car.get('priceLabel', f"${car['price']:,}")
    mileage = car.get('mileage', '')
    fuel = car['fuel_type']
    trans = car.get('transmission', 'Auto')

    en_model = get_en_model(car)
    slug = slugify(f"{brand}-{model}-{car['id']}")

    # 标题和描述 (SEO)
    title = f"{brand} {model} {year} | {en_model} Used Car Export | Jinba Auto Export"
    desc = f"Buy {brand} {model} ({year}) for export. Mileage: {mileage}, Fuel: {fuel}, Transmission: {trans}. Price: {price_label}. Worldwide shipping available from China."

    # 图片HTML
    gallery_html = build_gallery_html(car)

    # 规格表
    specs = [
        ('Year', str(year)),
        ('Mileage', str(mileage)),
        ('Fuel', fuel),
        ('Transmission', trans),
        ('Brand', brand),
        ('Stock ID', f'JB-{car["id"]:04d}'),
        ('Trade term', 'FOB'),
    ]
    spec_rows = ''.join(
        f'<div class="specitem"><small>{label}</small><b>{value}</b></div>'
        for label, value in specs
    )

    # 相关车辆（同品牌3台）
    related = ''
    related_cars = [c for c in cars_data if c['brand'] == brand and c['id'] != car['id']][:3]
    if related_cars:
        related = '<div class="wrap" style="margin-top:48px"><h2 style="margin-bottom:24px">Related Vehicles</h2><div class="grid">'
        for rc in related_cars:
            rc_img = '../' + (rc.get('images', [rc.get('image', '')])[0] if rc.get('images') else rc.get('image', ''))
            rc_slug = slugify(f"{rc['brand']}-{rc['model']}-{rc['id']}")
            rc_price = rc.get('priceLabel', f"${rc['price']:,}")
            rc_mileage = rc.get('mileage', '')
            rc_fuel = rc['fuel_type']
            related += f'''
            <a class="card" href="/cars/{rc_slug}.html">
                <div class="photo"><img loading="lazy" src="{rc_img}" alt="{rc['brand']} {rc['model']}"></div>
                <div class="body">
                    <div class="meta">{rc['brand']} · {rc['year']}</div>
                    <h3>{rc['brand']} {rc['model']}</h3>
                    <div class="spec"><span>{rc_mileage}</span><span>{rc_fuel}</span></div>
                    <div class="foot"><span class="price">{rc_price}</span></div>
                </div>
            </a>'''
        related += '</div></div>'

    page_url = f"https://jinbacars.com/cars/{slug}.html"

    # 车辆图片列表（用于JSON-LD）
    image_list = '", "'.join([f"https://jinbacars.com/{img}" for img in car.get('images', [car.get('image', '')]) if img])

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#071827">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc[:200]}">
<meta property="og:type" content="website">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="https://jinbacars.com/{car.get('images', [car.get('image', '')])[0] if car.get('images') else car.get('image', '')}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{page_url}">
<link rel="alternate" hreflang="en" href="{page_url}">
<link rel="alternate" hreflang="x-default" href="{page_url}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/v3.css?v=3">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3SVJ44HVKC"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-3SVJ44HVKC');</script>
<script defer src="/assets/v3.js?v=3"></script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Vehicle","name":"{brand} {model} {year}","description":"{desc[:200]}","sku":"JB-{car['id']:04d}","image":["{image_list}"],"vehicleModelDate":"{year}","mileageFromOdometer":{{"@type":"QuantitativeValue","value":{car['price']},"unitCode":"KMT"}},"itemCondition":"https://schema.org/UsedCondition","offers":{{"@type":"Offer","price":{car['price']},"priceCurrency":"USD","availability":"https://schema.org/InStock","url":"{page_url}","seller":{{"@type":"Organization","name":"Jinba Auto Export"}}}}}}</script>
</head>
<body>
<div class="top"><div class="wrap"><span>JINBA AUTO EXPORT · CHINA</span><span><a href="mailto:jian5222@gmail.com">jian5222@gmail.com</a> · <a href="https://wa.me/8618079089999">+86 180 7908 9999</a></span></div></div>
<header class="header"><nav class="wrap nav"><a class="brand" href="/"><span class="mark">J</span><span>JINBA AUTO<small>USED CAR EXPORT</small></span></a>
<button class="hamb" onclick="toggleNav(this)" aria-label="Menu">☰</button>
<div class="navlinks" id="navlinks">
<a href="/">Home</a><a href="/en/cars/">Inventory</a><a href="/#process">How it works</a><a href="/contact/">Contact</a>
<a class="quote" href="https://wa.me/8618079089999">Get a quote</a>
</div></nav></header>

<main class="section">
<div class="wrap">
<nav class="breadcrumbs"><a href="/">Home</a> / <a href="/en/cars/">Inventory</a> / <span>{brand} {model}</span></nav>
<div class="detail">
<div>{gallery_html}</div>
<div>
<div class="stocktag">JB-{car['id']:04d}</div>
<h1>{brand} {model}</h1>
<div class="bigprice">{price_label}</div>
<div class="specgrid">{spec_rows}</div>
<div class="legalnote"><p>Prices are indicative in USD and exclude freight, customs duties, taxes and destination charges.</p><p>Vehicle availability, specifications, mileage and condition must be reconfirmed before payment.</p></div>
<div class="actions">
<a class="btn primary" href="https://wa.me/8618079089999?text=I%20am%20interested%20in%20{brand}%20{model}%20({year})%20JB-{car['id']:04d}">Get a quote</a>
<a class="btn" style="border-color:var(--line)" href="mailto:jian5222@gmail.com?subject=JB-{car['id']:04d}%20{brand}%20{model}&body=I%20am%20interested%20in%20{brand}%20{model}%20({year})%20JB-{car['id']:04d}">Email</a>
</div>
</div>
</div>
{related}
</div>
</main>

<footer><div class="wrap">
<div class="footergrid">
<div><h4>JINBA AUTO EXPORT</h4><p>Xinyu, Jiangxi, China</p></div>
<div><h4>Inventory</h4><a href="/en/cars/">View all vehicles</a><a href="/en/brands/">Browse by brand</a></div>
<div><h4>Company</h4><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></div>
<div><h4>Contact</h4><a href="https://wa.me/8618079089999">WhatsApp: +86 180 7908 9999</a><a href="mailto:jian5222@gmail.com">jian5222@gmail.com</a></div>
</div>
<div class="copyright">© 2026 Jinba Auto Export. All rights reserved.</div>
</div></footer>
<script src="/assets/v3.js?v=3"></script>
</body>
</html>''', slug

# ===== 主流程 =====
cars_data = load_data()
print(f'\\n加载 {len(cars_data)} 台车数据')

out_dir = os.path.join(BASE_DIR, 'cars')
os.makedirs(out_dir, exist_ok=True)

count = 0
for car in cars_data:
    try:
        page_html, slug = generate_page(car)
        filepath = os.path.join(out_dir, f"{slug}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(page_html)
        count += 1
        if count % 20 == 0:
            img_count = len(car.get('images', []))
            print(f'  已生成 {count} 页 (最新: {car["brand"]} {car["model"]} - {img_count} photos)')
    except Exception as e:
        print(f'  错误 (ID {car.get("id", "?")}): {e}')

print(f'\\n✅ 完成! 生成 {count} 页面')
'''

with open(os.path.join(BASE, '_scripts', 'generate-cars', 'generate_pages.py'), 'w', encoding='utf-8') as f:
    f.write(script_content)

print('  ✅ generate_pages.py 已重写')

# ============================================================
# STEP 3: 运行生成器
# ============================================================
print('\n' + '='*60)
print('STEP 3/4: 生成所有车辆页面')
print('='*60)

os.chdir(os.path.join(BASE, '_scripts', 'generate-cars'))
result = os.system(f'python3 generate_pages.py')
if result != 0:
    print('  ⚠️ 生成器返回非零状态，检查错误')
else:
    print('  ✅ 页面生成完成')

os.chdir(BASE)

# ============================================================
# STEP 4: 部署到GitHub
# ============================================================
print('\n' + '='*60)
print('STEP 4/4: 部署到 GitHub Pages')
print('='*60)

def github_api(url, method='GET', data=None):
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
        'User-Agent': 'jinba-deploy',
    }
    body = json.dumps(data, ensure_ascii=False).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            result = resp.read().decode('utf-8')
            return json.loads(result) if result else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8')
        print(f'  GitHub API 错误 {e.code}: {err[:200]}')
        return None

# 获取HEAD
api_base = f'https://api.github.com/repos/{REPO}'
print('  获取仓库信息...')
ref = github_api(f'{api_base}/git/refs/heads/main')
if not ref:
    print('  ❌ 无法获取仓库引用，请检查TOKEN和仓库名')
    sys.exit(1)

head_sha = ref['object']['sha']
commit = github_api(f'{api_base}/git/commits/{head_sha}')
tree_sha = commit['tree']['sha']
print(f'  HEAD: {head_sha[:7]}')

# 构建文件列表
files_to_upload = []
exclude_dirs = {'.git', 'node_modules', '_scripts', '__pycache__', '.idea'}
exclude_files = {'deploy.py', 'deploy-now.js', 'fix-and-deploy.js', 'deploy.js', 'fix_script.py',
                 'analyze.py', 'output_hex.txt', 'deploy-github.ps1', 'sw.js'}

for root, dirs, files in os.walk(BASE):
    # 跳过排除目录
    dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
    for f in files:
        if f in exclude_files or f.endswith('.pyc') or f.endswith('.py'):
            continue
        full_path = os.path.join(root, f)
        rel_path = os.path.relpath(full_path, BASE).replace('\\', '/')
        files_to_upload.append((rel_path, full_path))

print(f'  共 {len(files_to_upload)} 个文件待上传')

# 分批创建blobs和tree
entries = []
for i, (rel_path, full_path) in enumerate(files_to_upload):
    try:
        ext = os.path.splitext(rel_path)[1].lower()
        is_binary = ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.ico', '.svg'}
        with open(full_path, 'rb') as f:
            content = f.read()

        if is_binary:
            b64 = base64.b64encode(content).decode('ascii')
            blob_data = github_api(f'{api_base}/git/blobs', 'POST',
                                 {'content': b64, 'encoding': 'base64'})
        else:
            blob_data = github_api(f'{api_base}/git/blobs', 'POST',
                                 {'content': content.decode('utf-8', errors='replace'), 'encoding': 'utf-8'})

        if blob_data:
            entries.append({'path': rel_path, 'mode': '100644', 'type': 'blob', 'sha': blob_data['sha']})

        if (i+1) % 50 == 0:
            print(f'  上传进度: {i+1}/{len(files_to_upload)}')
    except Exception as e:
        print(f'  跳过 {rel_path}: {e}')

print(f'  成功上传 {len(entries)}/{len(files_to_upload)} 个文件')

# 创建tree
print('  创建 Git tree...')
for i in range(0, len(entries), 100):
    batch = entries[i:i+100]
    tree = github_api(f'{api_base}/git/trees', 'POST',
                     {'base_tree': tree_sha, 'tree': batch})
    if tree:
        tree_sha = tree['sha']
        print(f'  Tree {i//100+1}: {tree_sha[:7]}')

# 创建commit
print('  创建提交...')
commit_data = github_api(f'{api_base}/git/commits', 'POST', {
    'message': '全自动优化: 多照片画廊+修复编码+生成160台车页面\n\n'
               '- 1274张图片按车分组，每车7-8张照片\n'
               '- 新增多照片缩略图切换画廊\n'
               '- 修复所有中文编码乱码\n'
               '- 160台车独立SEO页面\n'
               '- 添加结构化数据(Schema.org Vehicle)',
    'tree': tree_sha,
    'parents': [head_sha]
})

if not commit_data:
    print('  ❌ 创建提交失败')
    sys.exit(1)

commit_sha = commit_data['sha']

# 更新分支
print('  更新 main 分支...')
github_api(f'{api_base}/git/refs/heads/main', 'PATCH',
          {'sha': commit_sha, 'force': True})

print(f'\n' + '='*60)
print(f'  ✅ 部署完成！')
print(f'  提交: {commit_sha[:7]}')
print(f'  网站: https://jinbacars.com')
print(f'  预计 1-3 分钟生效')
print(f'='*60)
