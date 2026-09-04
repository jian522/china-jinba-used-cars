#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 GitHub 仓库 main 分支恢复 assets/design-system.css 与 assets/app.js 到工作区。
原因：这两个文件之前从未进入本地 git commit，被 push_api 的 diff 误判为删除，
导致线上 404。本脚本用与 push_api 相同的 token 来源直接调 REST API 拉回。
"""
import base64
import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = 'jian522/china-jinba-used-cars'
BASE = f'https://api.github.com/repos/{REPO}'


def get_token():
    if os.environ.get('GH_TOKEN'):
        return os.environ['GH_TOKEN']
    cred = Path.home() / '.git-credentials'
    if cred.exists():
        m = re.search(r'https://[^:/]+:([A-Za-z0-9_]{30,})@github\.com',
                      cred.read_text(encoding='utf-8', errors='ignore'))
        if m:
            return m.group(1)
    raise SystemExit('未找到 GitHub token')


TOKEN = get_token()
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def api(path):
    req = urllib.request.Request(
        BASE + path,
        headers={'Authorization': f'token {TOKEN}',
                 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'restore-assets'})
    return json.loads(OP.open(req, timeout=60).read())


def main():
    print('fetching main tree ...')
    tree = api('/git/trees/main?recursive=1')
    assets = [t for t in tree.get('tree', [])
              if t['type'] == 'blob' and t['path'].startswith('assets/')]
    print('assets blobs in remote main:', len(assets))
    for a in assets:
        print('  ', a['path'], a['sha'][:10])
    want = {'assets/design-system.css', 'assets/app.js'}
    found = False
    for a in assets:
        if a['path'] in want:
            found = True
            print('downloading', a['path'], '...')
            blob = api(f'/git/blobs/{a["sha"]}')
            data = base64.b64decode(blob['content'])
            out = ROOT / a['path']
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            print('  restored', a['path'], len(data), 'bytes')
    if not found:
        print('WARN: 远程 main 也未包含目标 assets，需要重建')
    else:
        print('DONE')


if __name__ == '__main__':
    main()
