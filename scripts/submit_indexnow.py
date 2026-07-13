#!/usr/bin/env python3
"""Submit the generated canonical URL set to IndexNow."""
from pathlib import Path
from urllib.request import Request, urlopen
import json
import re

ROOT=Path(__file__).resolve().parents[1]
BASE='https://jinbacars.com'
KEY='6d9a7c2e4f8b41a39c5d7e0b2f6a8c14'
text=(ROOT/'sitemap.xml').read_text()
urls=re.findall(r'<loc>(https://jinbacars\.com/[^<]+)</loc>',text)
payload=json.dumps({'host':'jinbacars.com','key':KEY,'keyLocation':f'{BASE}/{KEY}.txt','urlList':urls}).encode()
request=Request('https://api.indexnow.org/indexnow',data=payload,headers={'Content-Type':'application/json; charset=utf-8','User-Agent':'Jinba-SEO-Bot/1.0'},method='POST')
with urlopen(request,timeout=45) as response:
    if response.status not in (200,202):raise SystemExit(f'IndexNow returned {response.status}')
print(f'submitted {len(urls)} URLs to IndexNow')
