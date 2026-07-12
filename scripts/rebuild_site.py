from pathlib import Path
import re
import json

root=Path(__file__).resolve().parents[1]
inventory=(root/'cars/index.html').read_text(errors='ignore')

# Publish an exact manifest of the real local photos available for every vehicle.
photo_manifest={}
for folder in sorted((root/'uploads/cars').iterdir(),key=lambda p:int(p.name)):
    photos=[]
    primary=folder/'primary.jpg'
    if primary.exists(): photos.append(f'/uploads/cars/{folder.name}/primary.jpg')
    photos.extend('/'+str(p.relative_to(root)).replace('\\','/') for p in sorted(folder.iterdir()) if p.is_file() and p.name!='primary.jpg')
    photo_manifest[folder.name]=photos
(root/'assets/vehicle-images.json').write_text(json.dumps(photo_manifest,ensure_ascii=False,separators=(',',':')))

# Build a reliable mapping from every legacy remote vehicle image to its locally stored real primary photo.
mapping={}
cards=re.findall(r'<a[^>]+href="/cars/(\d+)/?"[\s\S]*?<img[^>]+src="(https://[^"]*autoimg\.cn[^"]*)"',inventory)
for car_id,url in cards:
    local=f'/uploads/cars/{car_id}/primary.jpg'
    if (root/local.lstrip('/')).exists(): mapping[url]=local

# The first OG/main image in each vehicle page is authoritative for that vehicle.
for page in (root/'cars').glob('*/index.html'):
    car_id=page.parent.name
    text=page.read_text(errors='ignore')
    urls=re.findall(r'https://[^"\']*autoimg\.cn[^"\']*',text)
    local=f'/uploads/cars/{car_id}/primary.jpg'
    if urls and (root/local.lstrip('/')).exists(): mapping.setdefault(urls[0],local)

changed=0
remaining=set()
for page in root.rglob('*.html'):
    text=page.read_text(errors='ignore')
    old=text
    text=text.replace('info@jinbacars.com','jian5222@gmail.com').replace('+86 139 XXXX XXXX','+86 180 7908 9999').replace('© 2025 jinbacars.com','© 2026 Jinba Auto Export')
    for url,local in mapping.items(): text=text.replace(url,local)
    # Any remaining third-party vehicle image on a specific car page falls back to that car's real local primary.
    m=re.search(r'/cars/(\d+)(?:/index\.html|\.html)$',str(page).replace('\\','/'))
    if m:
        local=f'/uploads/cars/{m.group(1)}/primary.jpg'
        if (root/local.lstrip('/')).exists(): text=re.sub(r'https://[^"\']*autoimg\.cn[^"\']*',local,text)
    if 'jinba-global.css' not in text: text=text.replace('</head>','  <link rel="stylesheet" href="/assets/jinba-global.css?v=20260712g2">\n</head>')
    else: text=re.sub(r'/assets/jinba-global\.css(?:\?v=[^"\']*)?', '/assets/jinba-global.css?v=20260712g3', text)
    if 'jinba-global.js' not in text: text=text.replace('</body>','  <script src="/assets/jinba-global.js?v=20260712g2" defer></script>\n</body>')
    else: text=re.sub(r'/assets/jinba-global\.js(?:\?v=[^"\']*)?', '/assets/jinba-global.js?v=20260712g3', text)
    for u in re.findall(r'https://[^"\']*autoimg\.cn[^"\']*',text): remaining.add(u)
    if text!=old: page.write_text(text);changed+=1

print(f'pages_changed={changed}')
print(f'image_mappings={len(mapping)}')
print(f'remaining_external_vehicle_images={len(remaining)}')
