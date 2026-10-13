#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金霸网站部署到 Cloudflare Pages（Direct Upload，替代 push_api.py 的 GitHub Pages 路线）。

用法：
    python scripts/deploy_pages.py            # 部署当前 git 已跟踪的静态文件
    python scripts/deploy_pages.py --dry-run      # 生成快照和刷新计划，不上传
    python scripts/deploy_pages.py --skip-stage --stage-dir <快照目录>

前提：
  - Token 在 .workbuddy/cf_token.txt（Pages Write；自动清缓存另需 Zone:Cache Purge）
  - 首次查找 zone_id 需 Zone:Read；已有 .workbuddy/cf_zone_id.txt 时不需查询
  - 代理 127.0.0.1:7890 可用
"""
from __future__ import annotations

import os
import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys
import argparse
import tempfile
import time
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
# 每次正常运行分配新的 snapshot_* 目录；旧目录不混入上传。
STAGE = ROOT / "_pages_deploy" / "site_shop_catalog_20261009"
TOKEN_FILE = ROOT / ".workbuddy" / "cf_token.txt"
WRANGLER = r"C:/Users/Administrator/node_modules/wrangler/bin/wrangler.js"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"
PROJECT = "jinba-cars"
HOST = "jinbacars.com"
PUBLIC_HOSTS = (HOST, "www." + HOST)

# 需要主动清缓存时（每天上新后要让访客立刻看到新车间）。
# 2026-10-08：CF 后台 Cache Rule 把 HTML 的 max-age 从 600 覆盖成了 14400，
# 部署后主域最长 4 小时仍返回旧版列表页（易误判为「部署失败」）。
# 部署后需使用 Zone:Cache Purge；当前权限不能只按历史 Pages Write 推断。
# 首页/列表/元文件固定刷新，其余按成功部署的文件内容差异清理。
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
]
ZONE_CACHE = ROOT / ".workbuddy" / "cf_zone_id.txt"
MANIFEST_FILE = ROOT / ".workbuddy" / "cf_deploy_manifest.json"
QUERY_REF = re.compile(r'''["'`(]\s*([^"'`()\s<>]*\?[^"'`()\s<>]*)''')


def _manifest_path(rel: str) -> bool:
    """只记录公开部署文件；不读取运营目录或本地凭据。"""
    path = pathlib.PurePosixPath(rel)
    return (bool(rel) and not path.is_absolute() and ".." not in path.parts
            and not rel.startswith((".", "admin/", "data/", "scripts/", "imports/",
                                    "_pages_deploy/", "_preview/", "ZCode_Workspacecacheuv/"))
            and not rel.lower().endswith((".md", ".py", ".pdf", ".pyc", ".sh", ".bat")))


def _file_urls(rel: str) -> set[str]:
    """Pages 的 index.html、无扩展 HTML 路由及原文件 URL 均须覆盖。"""
    if rel in ("_headers", "_redirects"):
        return set()
    path = "/" + quote(rel, safe="/-._~")
    paths = {path}
    if rel == "index.html" or rel.endswith("/index.html"):
        canonical = path[:-len("index.html")]
        paths.add(canonical)
        if canonical != "/":
            paths.add(canonical.rstrip("/"))
    elif rel.endswith(".html"):
        paths.add(path[:-len(".html")])
    return {f"https://{host}{p}" for host in PUBLIC_HOSTS for p in paths}


def build_manifest(keep: list[str] | None = None) -> dict:
    """对上传快照计算 hash，并收集实际引用的带查询参数资源 URL。"""
    paths = keep if keep is not None else [
        p.relative_to(STAGE).as_posix() for p in STAGE.rglob("*") if p.is_file()]
    files = {}
    for rel in sorted(paths):
        if _manifest_path(rel) and (STAGE / rel).is_file():
            with (STAGE / rel).open("rb") as source:
                files[rel] = hashlib.file_digest(source, "sha256").hexdigest()
    query_urls: dict[str, set[str]] = {}
    for rel in files:
        if pathlib.PurePosixPath(rel).suffix.lower() not in (
                ".html", ".css", ".js", ".svg", ".xml", ".json"):
            continue
        text = (STAGE / rel).read_text(encoding="utf-8", errors="replace")
        for ref in QUERY_REF.findall(text):
            url = urlsplit(urljoin(f"https://{HOST}/{rel}", html.unescape(ref)))
            if url.hostname not in PUBLIC_HOSTS or url.scheme not in ("http", "https") or not url.query:
                continue
            target = unquote(url.path).lstrip("/")
            for candidate in (target, target + "index.html", target + "/index.html", target + ".html"):
                if candidate in files:
                    # 保留完整 query；?v=旧版本与裸 URL 是不同缓存项。
                    for host in PUBLIC_HOSTS:
                        value = urlunsplit(("https", host, url.path, url.query, ""))
                        query_urls.setdefault(candidate, set()).add(value)
                    break
    return {"version": 1, "files": files,
            "query_urls": {rel: sorted(urls) for rel, urls in query_urls.items()}}


def load_manifest() -> dict | None:
    try:
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        if (manifest.get("version") != 1 or not isinstance(manifest.get("files"), dict)
                or not isinstance(manifest.get("query_urls"), dict)
                or any(not _manifest_path(rel) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                       for rel, digest in manifest["files"].items())):
            raise ValueError("invalid manifest")
        for rel, urls in manifest["query_urls"].items():
            if rel not in manifest["files"] or not isinstance(urls, list):
                raise ValueError("invalid query URL list")
            if any(not isinstance(url, str) or urlsplit(url).scheme != "https"
                   or urlsplit(url).netloc not in PUBLIC_HOSTS for url in urls):
                raise ValueError("invalid query URL")
        return manifest
    except FileNotFoundError:
        return None
    except (OSError, ValueError, TypeError, AttributeError):
        print("Cache manifest unavailable; refresh known public site URLs", flush=True)
        return None


def purge_plan(current: dict, previous: dict | None) -> tuple[bool, list[str]]:
    """仅刷新主站/www 已知 URL；不会清空整个 zone 的其他子域缓存。"""
    previous = previous or {"files": {}, "query_urls": {}}
    changed = {rel for rel in current["files"].keys() | previous["files"].keys()
               if current["files"].get(rel) != previous["files"].get(rel)}
    if changed & {"_headers", "_redirects"}:
        changed = current["files"].keys() | previous["files"].keys()
    urls = {url.replace("https://" + HOST, "https://" + host, 1)
            for url in PURGE_URLS for host in PUBLIC_HOSTS}
    for rel in changed:
        urls.update(_file_urls(rel))
        for value in previous["query_urls"].get(rel, []) + current["query_urls"].get(rel, []):
            parsed = urlsplit(value)
            urls.update(urlunsplit(("https", host, parsed.path, parsed.query, ""))
                        for host in PUBLIC_HOSTS)
    return False, sorted(urls)


def save_manifest(current: dict, previous: dict | None) -> None:
    # 同名资源以后再次改动时，也要清理更早的 ?v= 版本缓存。
    if previous:
        for rel, urls in previous["query_urls"].items():
            if rel in current["files"]:
                current["query_urls"][rel] = sorted(
                    set(urls) | set(current["query_urls"].get(rel, [])))
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    pending = MANIFEST_FILE.with_suffix(".json.tmp")
    pending.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending.replace(MANIFEST_FILE)


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


def purge_cache(current: dict | None = None) -> int:
    """部署后主动清 CF 边缘缓存，让新内容立刻对访客可见。

    purge API 需 ``Zone:Cache Purge``；首次查 zone 需 ``Zone:Read``。
    zone_id 缓存到 ``.workbuddy/cf_zone_id.txt``。全部清理成功后才保存
    文件清单；跳过/失败保留旧清单，让下次部署继续清理未完成的变化。
    """
    if "--no-purge" in sys.argv:
        print("SKIP cache purge (--no-purge): freshness not verified", flush=True)
        return 0
    try:
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        print("FAILED cache purge (no token file)", flush=True)
        return 1

    # 1) 取 zone_id：优先用缓存文件，避免每次部署多打一次 API
    zone = ""
    if ZONE_CACHE.is_file():
        zone = ZONE_CACHE.read_text(encoding="utf-8").strip()
    if not zone:
        st, out = _cf_api(f"/zones?name={HOST}", token)
        if st != 200:
            print(f"SKIP cache purge (zone lookup HTTP {st} — "
                  f"token 需 Zone:Read 权限)", flush=True)
            return 1
        try:
            arr = (json.loads(out).get("result") or [])
        except Exception:                          # noqa: BLE001
            arr = []
        if not arr:
            print("SKIP cache purge (zone not found — "
                  "token 无权列出 zone)", flush=True)
            return 1
        zone = arr[0]["id"]
        ZONE_CACHE.parent.mkdir(exist_ok=True)
        ZONE_CACHE.write_text(zone + "\n", encoding="utf-8")
        print(f"zone_id cached: {zone}", flush=True)

    # 2) 首次建立基线后，仅清变更 URL，不再无条件扫整个 sitemap。
    if current is None:
        current = build_manifest()
    previous = load_manifest()
    _, urls = purge_plan(current, previous)
    purged = 0
    for offset in range(0, len(urls), 30):
        if offset:
            time.sleep(0.25)
        batch = urls[offset:offset + 30]
        st, out = _cf_api(f"/zones/{zone}/purge_cache", token,
                          method="POST", body=json.dumps({"files":batch}), timeout=30)
        try:
            success = st == 200 and json.loads(out).get("success") is True
        except (ValueError, AttributeError):
            success = False
        if not success:
            print(f"Cache purge incomplete: HTTP {st}, {purged}/{len(urls)} URLs", flush=True)
            return 1
        purged += len(batch)
        print(f"purged {purged}/{len(urls)} URLs", flush=True)
    save_manifest(current, previous)
    return 0


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
        if not _manifest_path(rel2):
            continue
        # git 索引里可能有磁盘上已删除的文件：daily_upload.py 采集后会自动
        # 清掉 imports/<batch>/ 的中间素材，但索引条目仍留着（未 git rm）。
        # 这类悬空条目必须跳过，否则 copy2 直接 FileNotFoundError 中断部署。
        if not (ROOT / rel2).is_file():
            continue
        keep.append(rel2)
    return keep


def stage() -> None:
    """新建唯一快照；不复用、删除或覆盖历史暂存目录。"""
    import shutil
    global STAGE
    keep = build_keep()
    parent = ROOT / "_pages_deploy"
    parent.mkdir(parents=True, exist_ok=True)
    STAGE = pathlib.Path(tempfile.mkdtemp(prefix="snapshot_", dir=parent))
    print(f"STAGE {len(keep)} files", flush=True)

    n = 0
    for rel in keep:
        src, dst = ROOT / rel, STAGE / rel
        if src.is_symlink() or not src.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError(f"Deployment source escapes workspace: {rel}")
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


def verify_snapshot(manifest: dict) -> None:
    """上传目录与 hash 清单必须一致，拒绝残留文件、链接及上传前内容变动。"""
    actual = set()
    for path in STAGE.rglob("*"):
        if path.is_symlink():
            raise ValueError("Snapshot contains a symbolic link")
        if path.is_file():
            actual.add(path.relative_to(STAGE).as_posix())
    if actual != set(manifest["files"]):
        raise ValueError("Snapshot includes excluded or unrecorded files")
    if build_manifest()["files"] != manifest["files"]:
        raise ValueError("Snapshot changed after manifest creation")


def main() -> int:
    global STAGE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="仅生成干净快照和刷新计划，不上传")
    parser.add_argument("--skip-stage", action="store_true")
    parser.add_argument("--stage-dir", type=pathlib.Path)
    parser.add_argument("--no-purge", action="store_true")
    args = parser.parse_args()
    if args.skip_stage:
        if args.stage_dir is None:
            parser.error("--skip-stage 必须明确指定 --stage-dir，禁止默认重传旧目录")
        STAGE = args.stage_dir.resolve()
        parent = (ROOT / "_pages_deploy").resolve()
        if not STAGE.is_relative_to(parent) or STAGE == parent or not STAGE.is_dir():
            parser.error("--stage-dir 必须是 _pages_deploy 内现存快照子目录")
    elif args.stage_dir:
        parser.error("--stage-dir 只能与 --skip-stage 同时使用")
    else:
        stage()
    manifest = build_manifest()
    verify_snapshot(manifest)
    _, urls = purge_plan(manifest, load_manifest())
    print(f"Verified snapshot: {len(manifest['files'])} files; {len(urls)} purge URLs; {STAGE}", flush=True)
    if args.dry_run:
        print("DRY RUN: no deployment, no purge, no baseline update", flush=True)
        return 0
    rc = deploy()
    # 只有部署成功才清缓存（失败时清了也没意义，还会让旧内容被刷成 MISS）
    if rc == 0:
        rc = purge_cache(manifest)
        if rc:
            print("UPLOAD SUCCEEDED; CACHE REFRESH INCOMPLETE. Retry required.", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
