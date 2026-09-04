#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub API 推送（基于远程基线树 diff，不依赖本地存在基线 commit）

背景：push_batch.py 依赖 `git ls-tree <远程基线sha>`，但部署走 API 后本地
git 对象库并不含远程提交，基线 sha 会 cat-file 失败。本脚本改为：
  1) API 取远程 main 树（recursive）作为基线
  2) 本地 `git ls-tree HEAD` 作为目标
  3) diff 出 added/modified/removed，blob 逐个上传（断点续传缓存）
  4) finish 时链式分批建树 -> commit -> 更新 main

用法：
  python scripts/push_api.py plan           # 差异统计与进度
  python scripts/push_api.py upload [N]     # 传下一批 N 个（默认 150）
  python scripts/push_api.py finish [msg]   # 建树 -> commit -> 更新 main
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
CACHE = ROOT / '.workbuddy' / 'push_api_cache.json'
DIFF = ROOT / '.workbuddy' / 'push_diff.json'
TREE_CACHE = ROOT / '.workbuddy' / 'push_api_trees'

EXCLUDE_PREFIX = ('.workbuddy/', 'ZCode_Workspacecacheuv/', '.git/')
# admin/ 与 data/ 是运营目录（后台页、车辆原始数据含未发布与 VIN 片段），
# 不应出现在公开 Pages 站点上：本地保留但不随部署上传，并在下一次发布时从远端删除。
DEPLOY_DROP = ('admin/', 'data/')
WORKERS = 6
TIMEOUT = 60
MAX_RETRY = 7
TREE_CHUNK = 100


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
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))


def api(path, method='GET', payload=None):
    url = path if path.startswith('http') else BASE + path
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'token {TOKEN}')
    req.add_header('User-Agent', 'jinba-push')
    req.add_header('Accept', 'application/vnd.github+json')
    if payload is not None:
        req.add_header('Content-Type', 'application/json')
    last = None
    for attempt in range(MAX_RETRY):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = f'{e.code} {e.read().decode("utf-8", "ignore")[:150]}'
            # 建树接口在服务端过载时会返回 422 "request timed out"，
            # 这不是客户端错误，重试即可（建树是幂等的）。
            if e.code in (403, 422, 429) or e.code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f'{method} {path} -> {last}')
        except Exception as e:
            last = str(e)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f'{method} {path} 重试耗尽: {last}')


def local_tree():
    out = subprocess.run(['git', 'ls-tree', '-r', '-z', 'HEAD'],
                         cwd=ROOT, capture_output=True, timeout=300, check=True).stdout
    tree = {}
    for rec in out.split(b'\x00'):
        if not rec:
            continue
        meta, raw_path = rec.split(b'\t', 1)
        mode, _typ, sha = meta.split()
        p = raw_path.decode('utf-8')
        if p.startswith(EXCLUDE_PREFIX) or p.startswith(DEPLOY_DROP):
            continue
        tree[p] = (mode.decode(), sha.decode())
    return tree


def remote_tree(base_commit):
    tree_sha = api(f'/git/commits/{base_commit}')['tree']['sha']
    # 递归树响应约 1.1MB，GitHub 偶发 IncompleteRead。按 tree sha 缓存，
    # 这样重试 finish 时不必重拉，也能从上次失败中恢复。
    TREE_CACHE.mkdir(parents=True, exist_ok=True)
    cached = TREE_CACHE / f'{tree_sha}.json'
    if cached.exists():
        t = json.loads(cached.read_text(encoding='utf-8'))
    else:
        t = api(f'/git/trees/{tree_sha}?recursive=1')
        if t.get('truncated'):
            raise RuntimeError('远程树被截断，需分目录递归')
        cached.write_text(json.dumps(t), encoding='utf-8')
    return {x['path']: (x['mode'], x['sha']) for x in t['tree']
            if x['type'] == 'blob' and not x['path'].startswith(EXCLUDE_PREFIX)}


def build_diff():
    base = api(f'/git/refs/heads/{BRANCH}')['object']['sha']
    target = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                            capture_output=True, check=True).stdout.decode().strip()
    old, new = remote_tree(base), local_tree()
    added = [p for p in new if p not in old]
    removed = [p for p in old if p not in new]
    modified = [p for p in old if p in new and old[p][1] != new[p][1]]
    DIFF.parent.mkdir(parents=True, exist_ok=True)
    DIFF.write_text(json.dumps({'base': base, 'target': target,
                                'added': added, 'modified': modified,
                                'removed': removed}, ensure_ascii=False), encoding='utf-8')
    return base, target, new, added, modified, removed


def load_diff_cached(refresh=False):
    if refresh or not DIFF.exists():
        return build_diff()
    d = json.loads(DIFF.read_text(encoding='utf-8'))
    new = local_tree()
    return d['base'], d['target'], new, d['added'], d['modified'], d['removed']


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding='utf-8'))
    return {}


def valid_cache(new):
    """校验断点续传缓存是否仍可信。

    缓存原本按「路径」命中，而内容变了路径不变时，会沿用旧内容的 blob sha，
    导致改动被静默丢弃（2026-09-03 首页改版 4 个 html 白推一次即此因）。
    因此缓存条目必须记录当时的本地 git blob sha，只有与当前一致才可用。
    """
    cache = load_cache()
    keep, dropped = {}, 0
    for p, item in cache.items():
        if isinstance(item, dict) and p in new and item.get('git') == new[p][1]:
            keep[p] = item
        else:
            dropped += 1
    return keep, dropped


def save_cache(c):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')


def upload_one(rel):
    data = (ROOT / rel).read_bytes()
    try:
        payload = {'content': data.decode('utf-8'), 'encoding': 'utf-8'}
    except UnicodeDecodeError:
        payload = {'content': base64.b64encode(data).decode('ascii'), 'encoding': 'base64'}
    return rel, api('/git/blobs', 'POST', payload)['sha']


def cmd_plan():
    base, target, new, added, modified, removed = load_diff_cached(refresh=True)
    cache, dropped = valid_cache(new)
    uploads = added + modified
    pending = [p for p in uploads if p not in cache]
    print(f'base   = {base[:12]}   target = {target[:12]}')
    print(f'新增 {len(added)}  修改 {len(modified)}  删除 {len(removed)}  共需上传 {len(uploads)}')
    print(f'已缓存(内容校验通过) {len(uploads) - len(pending)}  待传 {len(pending)}'
          f'  失效缓存 {dropped}')
    if pending:
        mb = sum((ROOT / p).stat().st_size for p in pending) / 1048576
        print(f'待传体积 {mb:.1f} MB')
    core = api('https://api.github.com/rate_limit')['resources']['core']
    print(f'API 配额 {core["remaining"]}/{core["limit"]}')


def cmd_upload(n=150):
    base, target, new, added, modified, removed = load_diff_cached()
    cache, dropped = valid_cache(new)
    uploads = added + modified
    pending = [p for p in uploads if p not in cache][:n]
    if dropped:
        print(f'  丢弃失效缓存 {dropped} 条（内容已变或旧格式）', flush=True)
    if not pending:
        print('本批无待传文件（全部已缓存）')
        return
    print(f'本批 {len(pending)} 个文件，'
          f'{sum((ROOT / p).stat().st_size for p in pending) / 1048576:.1f} MB', flush=True)
    t0 = time.time()
    done = 0
    failed = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(upload_one, p): p for p in pending}
        for f in as_completed(futs):
            rel = futs[f]
            try:
                r, sha = f.result()
                cache[r] = {'sha': sha, 'git': new[r][1]}
                done += 1
            except Exception as e:
                failed.append((rel, str(e)[:80]))
            if done % 25 == 0:
                el = time.time() - t0
                print(f'  {done}/{len(pending)}  {el:.0f}s  {done / max(el, 1):.1f}/s', flush=True)
    save_cache(cache)
    el = time.time() - t0
    print(f'完成 {done}/{len(pending)}，用时 {el:.0f}s（{done / max(el, 1):.1f}/s），'
          f'累计缓存 {len(cache)}/{len(uploads)}', flush=True)
    if failed:
        print(f'失败 {len(failed)} 个（下批自动重试）:')
        for p, e in failed[:5]:
            print(f'  {p} -> {e}')


def cmd_finish(msg=None):
    base, target, new, added, modified, removed = load_diff_cached()
    cache, dropped = valid_cache(new)
    uploads = added + modified
    missing = [p for p in uploads if p not in cache]
    if missing:
        print(f'还有 {len(missing)} 个文件未上传，请先跑 upload')
        return
    entries = [{'path': p, 'mode': new[p][0], 'type': 'blob', 'sha': cache[p]['sha']}
               for p in uploads]
    old_modes = remote_tree(base)
    for p in removed:
        entries.append({'path': p, 'mode': old_modes[p][0], 'type': 'blob', 'sha': None})
    print(f'树条目 {len(entries)} 个（含删除 {len(removed)}）', flush=True)

    base_tree = api(f'/git/commits/{base}')['tree']['sha']
    new_tree = base_tree
    for i in range(0, len(entries), TREE_CHUNK):
        chunk = entries[i:i + TREE_CHUNK]
        new_tree = api('/git/trees', 'POST', {'base_tree': new_tree, 'tree': chunk})['sha']
        print(f'  建树 {min(i + TREE_CHUNK, len(entries))}/{len(entries)} -> {new_tree[:12]}',
              flush=True)

    if not msg:
        msg = 'Deploy via push_api'
    commit = api('/git/commits', 'POST',
                 {'message': msg, 'tree': new_tree, 'parents': [base]})['sha']
    print(f'新提交 {commit}', flush=True)
    api(f'/git/refs/heads/{BRANCH}', 'PATCH', {'sha': commit, 'force': False})
    print(f'OK: {BRANCH} -> {commit}')
    CACHE.unlink(missing_ok=True)
    DIFF.unlink(missing_ok=True)

    # P4: 部署成功后自动提交 IndexNow（失败不阻断部署结果）
    try:
        import subprocess as _sp
        r = _sp.run([sys.executable, str(ROOT / 'scripts' / 'submit_indexnow.py')],
                    capture_output=True, text=True, timeout=120)
        print('IndexNow:', (r.stdout or r.stderr).strip()[:120])
    except Exception as e:
        print('IndexNow 提交失败（不影响部署）:', str(e)[:100])


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'plan'
    if cmd == 'plan':
        cmd_plan()
    elif cmd == 'upload':
        cmd_upload(int(sys.argv[2]) if len(sys.argv) > 2 else 150)
    elif cmd == 'finish':
        cmd_finish(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print(__doc__)
