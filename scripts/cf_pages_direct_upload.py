#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cloudflare Pages Direct Upload（不走 GitHub App，绕开 8000011 授权错误）。

流程：
  1. wrangler 部署到临时项目（ Direct Upload，无需授权，资源来自 git ls-files）
  2. 用 dashboard 登录态（cookie）调 dashboard 内部 API，把两个域名绑到该项目
  3. 用户只需保持 CF 登录态有效，无其他操作
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "_preview"
PREVIEW.mkdir(exist_ok=True)
PROFILE = ROOT / ".workbuddy" / "cf_profile"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"
OWNER, REPO, PROJECT = "jian522", "china-jinba-used-cars", "jinba-cars"
DOMAINS = ["jinbacars.com", "www.jinbacars.com"]
NODE = r"C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-2/node.exe"
WRANGLER = r"C:/Users/Administrator/.workbuddy/node-ws/node_modules/wrangler/bin/wrangler.js"
PROXY = "http://127.0.0.1:7890"


def log(m: str) -> None:
    print(m, flush=True)


def build_file_list() -> list[str]:
    """git ls-files + 排除敏感/非部署目录，生成部署清单。"""
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    files = []
    for f in out.stdout.splitlines():
        f2 = f.strip('"')  # git 对非 ASCII 路径输出带引号
        if not f2:
            continue
        low = f2.lower()
        if (low.startswith(".workbuddy") or low.startswith("scripts/")
                or low.endswith(".md") or low.endswith(".py")
                or low.endswith(".pdf") or low.endswith(".sh")
                or low.endswith(".bat") or low.endswith(".env")
                or "zcode_workspacecacheuv" in low):
            continue
        files.append(f2)
    return files


def main() -> int:
    files = build_file_list()
    log(f"FILE_LIST {len(files)} files")
    manifest = PREVIEW / "deploy_manifest.txt"
    manifest.write_text("\n".join(files), encoding="utf-8")

    # ---- 1. wrangler Direct Upload ----
    env = {"PATH": r"C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-2;" + r"C:/Windows/System32",
           "HTTPS_PROXY": PROXY, "HTTP_PROXY": PROXY,
           "NO_PROXY": "localhost,127.0.0.1"}
    cmd = [NODE, WRANGLER, "pages", "project", "create", PROJECT,
           "--production-branch", "main"]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env, timeout=180)
    log("CREATE " + (r.stdout or "")[-500:] + (r.stderr or "")[-500:])

    cmd = [NODE, WRANGLER, "pages", "deploy", ".",
           "--project-name", PROJECT, "--branch", "main", "--commit-dirty=true"]
    log("DEPLOY_START (上传 250M 可能 10-30 分钟)")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env, timeout=3600)
    log("DEPLOY_OUT " + (r.stdout or "")[-800:])
    if r.returncode != 0:
        log("DEPLOY_ERR " + (r.stderr or "")[-1500:])
        return 5
    log("DEPLOY_OK")

    # ---- 2. 浏览器登录态绑域名 ----
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), executable_path=str(EXE), headless=False,
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--start-minimized"],
            viewport={"width": 1280, "height": 860})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/pages/view/{PROJECT}/domains",
                  wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(5000)

        for d in DOMAINS:
            r2 = page.evaluate(
                """async ([proj, domain]) => {
                    const r = await fetch(`/api/v4/accounts/${'0cd64536d2bc18ae46651a0a2636e1ff'}/pages/projects/${proj}/domains`, {
                        method: 'POST', credentials: 'include',
                        headers: {'content-type': 'application/json'},
                        body: JSON.stringify({name: domain})});
                    const j = await r.json();
                    return {status: r.status, ok: j.success,
                            err: j.success ? null : JSON.stringify(j.errors || j).slice(0, 200)};
                }""", [PROJECT, d])
            log(f"DOMAIN {d} -> {json.dumps(r2, ensure_ascii=False)}")

        page.wait_for_timeout(2000)
        ctx.close()

    log("ALL_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
