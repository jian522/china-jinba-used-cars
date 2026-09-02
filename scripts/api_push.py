#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub REST API 推送（优化版）

背景：本机 git 协议走代理必失败（github.com 直连被 reset），但 api.github.com 可达。
本脚本绕过 git 协议，用 Git Data API 完成推送。

优化点（相比 v1）：
  1. 用 `git ls-tree -r -z` 比对两棵树，只传差异文件（v1 全量遍历，3366 blobs 需 2h+）
  2. 并发上传 blob（8 线程），v1 串行 15 blobs/min
  3. 删除项用 {"sha": null} 树条目，v1 曾误把删除当空文件新增
  4. 不硬编码 token，从 GH_TOKEN 环境变量或 ~/.git-credentials 读取

用法：
  python scripts/api_push.py [base_rev] [target_rev]
默认 base=origin/main, target=HEAD。
"""
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = 'jian522/china-jinba-used-cars'
BASE = f'https://api.github.com/repos/{REPO}'
BRANCH = 'main'

# 永不推送的路径前缀（工作区内部数据 / 编辑器缓存）
EXCLUDE_PREFIX = ('.workbuddy/', 'ZCode_Workspacecacheuv/', '.git/')

WORKERS = 8
MAX_RETRY = 4


def get_token():
    if os.environ.get('GH_TOKEN'):
        return os.environ['GH_TOKEN']
    cred = Path.home() / '.git-credentials'
    if cred.exists():
        m = re.search(r'https://[^:/]+:([A-Za-z0-9_]{30,})@github\.com',
                      cred.read_text(encoding='utf-8', errors='ignore'))
        if m:
            return m.group(1)
    raise SystemExit('未找到 GitHub token，请设置 GH_TOKEN 或 ~/.git-credentials')


TOKEN = get_token()
# 系统代理已死但环境变量仍注入，必须绕过
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))


def api(path, method='GET', payload=None):
    # path 以 http 开头时按绝对 URL 处理（如 /rate_limit 属根端点，不在 /repos/{repo} 下）
    url = path if path.startswith('http') else BASE + path
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'token {TOKEN}')
    req.add_header('User-Agent', 'jinba-push')  # 必须，否则 GitHub 返回 404 而非 401
    req.add_header('Accept', 'application/vnd.github+json')
    if payload is not None:
        req.add_header('Content-Type', 'application/json')
    last = None
    for attempt in range(MAX_RETRY):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = f'{method} {path} -> {e.code} {e.read().decode("utf-8", "ignore")[:200]}'
            if e.code in (403, 429):  # 主限速 / secondary limit
                time.sleep(20 * (attempt + 1))
                continue
            if e.code >= 500:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(last)
        except Exception as e:
            last = f'{method} {path} -> {e}'
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f'retry exhausted: {last}')


def ls_tree(rev):
    """只读 tree 对象，不读 blob —— 本仓库是 partial clone(blob:none)，
    这条命令秒级返回；而 git diff 需要按需拉 blob，会卡死数分钟。"""
    out = subprocess.run(['git', 'ls-tree', '-r', '-z', rev],
                         cwd=ROOT, capture_output=True, timeout=300, check=True).stdout
    tree = {}
    for rec in out.split(b'\x00'):
        if not rec:
            continue
        meta, raw_path = rec.split(b'\t', 1)
        mode, _typ, sha = meta.split()
        tree[raw_path.decode('utf-8')] = (mode.decode(), sha.decode())
    return tree


def upload_blob(rel_path):
    data = (ROOT / rel_path).read_bytes()
    try:
        payload = {'content': data.decode('utf-8'), 'encoding': 'utf-8'}
    except UnicodeDecodeError:
        payload = {'content': base64.b64encode(data).decode('ascii'), 'encoding': 'base64'}
    sha = api('/git/blobs', 'POST', payload)['sha']
    return rel_path, sha


def main():
    base_rev = sys.argv[1] if len(sys.argv) > 1 else f'origin/{BRANCH}'
    target_rev = sys.argv[2] if len(sys.argv) > 2 else 'HEAD'

    base_sha = subprocess.run(['git', 'rev-parse', base_rev], cwd=ROOT,
                              capture_output=True, check=True).stdout.decode().strip()
    target_sha = subprocess.run(['git', 'rev-parse', target_rev], cwd=ROOT,
                                capture_output=True, check=True).stdout.decode().strip()
    print(f'[base]   {base_rev} = {base_sha}', flush=True)
    print(f'[target] {target_rev} = {target_sha}', flush=True)

    old = ls_tree(base_sha)
    new = ls_tree(target_sha)
    print(f'[tree] 远程 {len(old)} 文件 / 本地 {len(new)} 文件', flush=True)

    added, modified, removed = [], [], []
    for p in set(old) | set(new):
        if p.startswith(EXCLUDE_PREFIX):
            continue
        if p not in old:
            added.append(p)
        elif p not in new:
            removed.append(p)
        elif old[p][1] != new[p][1]:
            modified.append(p)
    uploads = added + modified
    print(f'[diff] 新增 {len(added)} / 修改 {len(modified)} / 删除 {len(removed)} '
          f'→ 需上传 {len(uploads)} 个 blob', flush=True)

    total_bytes = sum((ROOT / p).stat().st_size for p in uploads)
    print(f'[size] 待上传 {total_bytes / 1024 / 1024:.1f} MB', flush=True)

    core = api('https://api.github.com/rate_limit')['resources']['core']
    print(f'[rate] 剩余 {core["remaining"]}/{core["limit"]}', flush=True)
    if core['remaining'] < len(uploads) + 50:
        wait = core['reset'] - time.time()
        print(f'[rate] 配额不足，等待 {max(wait, 0) / 60:.1f} 分钟', flush=True)
        if wait > 0:
            time.sleep(min(wait + 30, 3700))

    t0 = time.time()
    entries = []
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(upload_blob, p): p for p in uploads}
        for f in as_completed(futs):
            rel, sha = f.result()
            entries.append({'path': rel, 'mode': new[rel][0], 'type': 'blob', 'sha': sha})
            done += 1
            if done % 100 == 0 or done == len(uploads):
                el = time.time() - t0
                speed = done / max(el, 1)
                print(f'[blob] {done}/{len(uploads)}  {el:.0f}s  {speed:.1f}/s  '
                      f'ETA {(len(uploads) - done) / max(speed, 0.01) / 60:.1f}min', flush=True)

    for p in removed:  # 删除项必须显式置 sha=null，不能当空文件新增
        entries.append({'path': p, 'mode': old[p][0], 'type': 'blob', 'sha': None})
    print(f'[tree] 树条目 {len(entries)} 个', flush=True)

    base_tree = api(f'/git/commits/{base_sha}')['tree']['sha']
    new_tree = api('/git/trees', 'POST', {'base_tree': base_tree, 'tree': entries})['sha']
    print(f'[tree] 新树 {new_tree}', flush=True)

    msg = ('feat: v6 homepage redesign (zh/en/ru/ar) + 110 new vehicle pages + 486 photos; '
           'fix multilingual CN leftovers; remove obsolete root reports')
    commit = api('/git/commits', 'POST',
                 {'message': msg, 'tree': new_tree, 'parents': [base_sha]})['sha']
    print(f'[commit] {commit}', flush=True)

    api(f'/git/refs/heads/{BRANCH}', 'PATCH', {'sha': commit, 'force': False})
    print(f'[push] {BRANCH} -> {commit} 完成，用时 {(time.time() - t0) / 60:.1f} 分钟', flush=True)


if __name__ == '__main__':
    main()
