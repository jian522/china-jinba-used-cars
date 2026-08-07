#!/usr/bin/env python3
"""Weekly public SEO and availability checks for the production site."""
from urllib.request import Request,urlopen
from urllib.parse import urlparse
import json
import re
import sys

BASE='https://jinbacars.com'
UA={'User-Agent':'Jinba-SEO-Health/1.0'}
def get(url,method='GET'):
    request=Request(url,headers=UA,method=method)
    with urlopen(request,timeout=30) as response:return response.status,response.read() if method=='GET' else b''

errors=[]
for path,needle in [('/robots.txt',b'Sitemap:'),('/sitemap.xml',b'<urlset'),('/sitemap-images.xml',b'<image:image'),('/feed.xml',b'<rss'),('/en/',b'JINBA AUTO'),('/en/cars/',b'data-car')]:
    try:
        status,body=get(BASE+path)
        if status!=200 or needle not in body:errors.append(f'{path}: status/content check failed')
    except Exception as exc:errors.append(f'{path}: {exc}')
status,sitemap=get(BASE+'/sitemap.xml')
urls=re.findall(rb'<loc>(https://jinbacars\.com/[^<]+)</loc>',sitemap)
for raw in urls[::max(1,len(urls)//25)][:25]:
    url=raw.decode()
    try:
        status,_=get(url,'HEAD')
        if status!=200:errors.append(f'{url}: HTTP {status}')
    except Exception as exc:errors.append(f'{url}: {exc}')
data=json.loads((__import__('pathlib').Path(__file__).resolve().parents[1]/'data/vehicles.json').read_text())
photos=[p for v in data if v.get('status')=='published' for p in v.get('photos',[])]
for path in photos:
    try:
        status,_=get(BASE+path,'HEAD')
        if status!=200:errors.append(f'{path}: HTTP {status}')
    except Exception as exc:errors.append(f'{path}: {exc}')
summary=f'URLs: {len(urls)} | Published image checks: {len(photos)} | Errors: {len(errors)}'
print(summary)
if errors:
    print('\n'.join(errors[:50]),file=sys.stderr);raise SystemExit(1)
