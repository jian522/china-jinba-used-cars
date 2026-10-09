#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金霸网站部署到 Cloudflare Pages（Direct Upload，替代 push_api.py 的 GitHub Pages 路线）。

用法：
    python scripts/deploy_pages.py            # 部署当前 git 已跟踪的静态文件
    python scripts/deploy_pages.py --skip-stage   # 跳过暂存，直接重传 _pages_deploy/site_v2

前提：
  - Token 在 .workbuddy/cf_token.txt（Pages Write 权限，项目 jinba-cars）
  - 代理 127.0.0.1:7890 可用
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
# 2026-09-14：暂存目录从 site/ 改为 site_v2/。历史 site/ 里积压了 1000+ 个
# 早期误传的 imports/ 采集素材，清理它们会触发安全拦截；直接启用新目录名
# 即可绕开，每次部署生成的都是一份由 git 清单决定的干净快照。
STAGE = ROOT / "_pages_deploy" / "site_shop_catalog_20261009"
TOKEN_FILE = ROOT / ".workbuddy" / "cf_token.txt"
WRANGLER = r"C:/Users/Administrator/node_modules/wrangler/bin/wrangler.js"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"
PROJECT = "jinba-cars"
HOST = "jinbacars.com"

# 需要主动清缓存时（每天上新后要让访客立刻看到新车间）。
# 2026-10-08：CF 后台 Cache Rule 把 HTML 的 max-age 从 600 覆盖成了 14400，
# 部署后主域最长 4 小时仍返回旧版列表页（易误判为「部署失败」）。
# 要根治需给 token 加 Zone -> Cache Purge 权限，届时本函数会自动生效。
# 权限不足时静默跳过（exit 0），不影响部署主流程。
PURGE_URLS = [
    f"https://{HOST}/",
    f"https://{HOST}/en/",
    f"https://{HOST}/zh/",
    f"https://{HOST}/ru/",
    f"https://{HOST}/ar/",
    f"https://{HOST}/en/cars/",
    f"https://{HOST}/zh/cars/",
    f"https://{HOST}/ru/cars/",
    f"https://{HOST}/ar/cars/",
    f"https://{HOST}/sitemap.xml",
    f"https://{HOST}/sitemap-images.xml",
    f"https://{HOST}/robots.txt",
    # hero banner 是 30 天 immutable 缓存（_headers 的 /*.webp 规则），
    # 换图后必须显式 purge，否则一个月内访客看到的还是旧图（10-08 实测 Age=168038）。
    f"https://{HOST}/images/hero-banner.webp",
    f"https://{HOST}/favicon.svg",
]
# Business identity and buyer guide change along with the language homepages.
PURGE_URLS += [f"https://{HOST}/{lang}/{path}/"
               for lang in ("en", "zh", "ru", "ar")
               for path in ("about", "contact", "guides/buy-used-cars-from-china")]
ZONE_CACHE = ROOT / ".workbuddy" / "cf_zone_id.txt"


def _cf_api(path: str, token: str, method: str = "GET", body: str | None = None,
            timeout: int = 30) -> tuple[int, str]:
    """裸调 Cloudflare v4 API（走代理；失败则去代理直连重试一次）。"""
    import urllib.request
    import urllib.error
    url = "https://api.cloudflare.com/client/v4" + path
    data = body.encode("utf-8") if body else None
    for proxy in (True, False):
        handlers = []
        if proxy:
            handlers.append(urllib.request.ProxyHandler(
                {"https": "http://127.0.0.1:7890"}))
        else:
            handlers.append(urllib.request.ProxyHandler({}))
        opener = urllib.request.build_opener(*handlers)
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"})
        try:
            with opener.open(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")
        except Exception as e:                      # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
    return 0, last                                # type: ignore[name-defined]


def purge_cache() -> int:
    """部署后主动清 CF 边缘缓存，让新内容立刻对访客可见。

    权限模型：purge API 需要 token 具备 ``Zone -> Cache Purge``，且能读 zone
    （``GET /zones?name=<host>``）。当前 token 只有 Pages Write，两者都缺 →
    全部返回 403/9109，本函数静默跳过。

    拿到权限后无需改代码：zone_id 首次自动探测并缓存到
    ``.workbuddy/cf_zone_id.txt``，之后每次部署都自动清。
    """
    if "--no-purge" in sys.argv:
        print("SKIP cache purge (--no-purge)", flush=True)
        return 0
    try:
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        print("SKIP cache purge (no token file)", flush=True)
        return 0

    # 1) 取 zone_id：优先用缓存文件，避免每次部署多打一次 API
    zone = ""
    if ZONE_CACHE.is_file():
        zone = ZONE_CACHE.read_text(encoding="utf-8").strip()
    if not zone:
        st, out = _cf_api(f"/zones?name={HOST}", token)
        if st != 200:
            print(f"SKIP cache purge (zone lookup HTTP {st} — "
                  f"token 需 Zone:Read 权限)", flush=True)
            return 0
        try:
            import json
            arr = (json.loads(out).get("result") or [])
        except Exception:                          # noqa: BLE001
            arr = []
        if not arr:
            print("SKIP cache purge (zone not found — "
                  "token 无权列出 zone)", flush=True)
            return 0
        zone = arr[0]["id"]
        ZONE_CACHE.parent.mkdir(exist_ok=True)
        ZONE_CACHE.write_text(zone + "\n", encoding="utf-8")
        print(f"zone_id cached: {zone}", flush=True)

    # 2) 清缓存
    import json
    # Internal links changed throughout the site; clear each canonical page.
    # Keep requests small enough for plans with a 30-URL purge limit.
    import xml.etree.ElementTree as ET
    urls = list(PURGE_URLS)
    urls += [el.text for el in ET.parse(ROOT / 'sitemap.xml').findall(
        './/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    urls = list(dict.fromkeys(urls))
    purged = 0
    for offset in range(0, len(urls), 30):
        batch = urls[offset:offset + 30]
        st, out = _cf_api(f"/zones/{zone}/purge_cache", token,
                          method="POST", body=json.dumps({"files":batch}), timeout=30)
        if st != 200 or not json.loads(out).get('success'):
            print(f"Cache purge incomplete: HTTP {st}, {purged}/{len(urls)} URLs", flush=True)
            return 1
        purged += len(batch)
        print(f"purged {purged}/{len(urls)} URLs", flush=True)
    return 0                                    # 永不阻断部署主流程


def _find_node() -> str:
    """定位 WorkBuddy 托管 Node（目录名含版本号，会随升级变化）。

    2026-09-12 踩坑：硬编码 22.22.2-2，在升级到 22.22.2-3 后
    subprocess 直接 WinError 2（系统找不到指定的文件）。
    优先用 `current` 软链，其次按 mtime 取最新带 node.exe 的版本目录。
    """
    base = pathlib.Path(r"C:/Users/Administrator/.workbuddy/binaries/node/versions")
    if base.is_dir():
        cands = [p / "node.exe" for p in base.iterdir()
                 if ".old" not in p.name and p.name != "current" and (p / "node.exe").is_file()]
        cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if cands:
            return str(cands[0]).replace("\\", "/")
    for p in (r"C:/Program Files/nodejs/node.exe",):
        if pathlib.Path(p).is_file():
            return p
    raise FileNotFoundError("找不到可用的 node.exe")


NODE = _find_node()


def build_keep() -> list[str]:
    """按 null 分隔清单列出 git 已跟踪的部署文件（排除脚本/文档/缓存）。"""
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    keep = []
    for rel in out.stdout.split(b"\0"):
        rel2 = rel.decode("utf-8", "ignore")
        low = rel2.lower()
        if not rel2 or rel2.startswith(("scripts/", ".workbuddy/", "ZCode_Workspacecacheuv/",
                                        "_pages_deploy/", "_preview/", "imports/")) \
                or low.endswith((".md", ".py", ".pdf", ".pyc", ".sh", ".bat")):
            continue
        # git 索引里可能有磁盘上已删除的文件：daily_upload.py 采集后会自动
        # 清掉 imports/<batch>/ 的中间素材，但索引条目仍留着（未 git rm）。
        # 这类悬空条目必须跳过，否则 copy2 直接 FileNotFoundError 中断部署。
        if not (ROOT / rel2).is_file():
            continue
        keep.append(rel2)
    return keep


def stage() -> None:
    """按 git 清单生成暂存目录。

    2026-09-14 改造：改为「每次都新建一份干净暂存区」，而不是在原暂存区上
    逐文件对账删除。原因：原做法要删掉 1000+ 个历史陈旧文件（早期误传的
    imports/ 采集素材），既触发安全拦截、又依赖「暂存区恰好还在旧状态」。
    直接换目录名即可，旧目录留着不影响（本地多占几十 MB，可由用户手动清）。

    指向新目录名 ``site_v2``，避免与历史残留的 ``site/`` 混用。
    """
    import shutil
    keep = build_keep()
    print(f"STAGE {len(keep)} files", flush=True)

    if STAGE.exists():
        # 目录名已带版本号：不存在就直接建，存在则说明上次构建过 —— 里面
        # 最多只有上一轮同清单文件，全部覆盖即可，无需删除任何东西。
        pass
    else:
        STAGE.mkdir(parents=True, exist_ok=True)

    n = 0
    for rel in keep:
        src, dst = ROOT / rel, STAGE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    size = sum(f.stat().st_size for f in STAGE.rglob("*") if f.is_file())
    print(f"STAGED {n} files size={size/1024/1024:.1f}MB", flush=True)


def deploy() -> int:
    # 必须基于完整 os.environ：裁剪 PATH（只留 System32）会让 Node 启动即
    # 崩溃 `Assertion failed: ncrypto::CSPRNG(nullptr, 0)`（2026-09-12 实锤复现）
    env = dict(os.environ)
    env.update({"CLOUDFLARE_API_TOKEN": TOKEN_FILE.read_text(encoding="utf-8").strip(),
                "CLOUDFLARE_ACCOUNT_ID": ACCOUNT,
                "HTTPS_PROXY": "http://127.0.0.1:7890", "HTTP_PROXY": "http://127.0.0.1:7890"})
    cmd = [NODE, WRANGLER, "pages", "deploy", ".", "--project-name", PROJECT,
           "--branch", "main", "--commit-dirty=true"]
    r = subprocess.run(cmd, cwd=STAGE, capture_output=True, text=True,
                       env=env, timeout=3600)
    if r.returncode != 0 and "fetch failed" in ((r.stderr or "") + (r.stdout or "")):
        # Clash 代理挂掉 → 去掉代理直连重试（api.cloudflare.com 可直连）
        print("proxy fetch failed, retry direct...", flush=True)
        for k in ("HTTPS_PROXY", "HTTP_PROXY"):
            env.pop(k, None)
        r = subprocess.run(cmd, cwd=STAGE, capture_output=True, text=True,
                           env=env, timeout=3600)
    print((r.stdout or "")[-1500:], flush=True)
    if r.returncode != 0:
        print("ERR " + (r.stderr or "")[-800:], flush=True)
    return r.returncode


if __name__ == "__main__":
    if "--skip-stage" not in sys.argv:
        stage()
    rc = deploy()
    # 只有部署成功才清缓存（失败时清了也没意义，还会让旧内容被刷成 MISS）
    if rc == 0:
        purge_cache()
    sys.exit(rc)
