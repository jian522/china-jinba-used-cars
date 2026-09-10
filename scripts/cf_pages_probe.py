#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测 Cloudflare dashboard 内部 API 中 Pages 相关端点的正确路径与 GitHub 授权状态。"""
from __future__ import annotations

import json
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILE = ROOT / ".workbuddy" / "cf_profile"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"


def log(m: str) -> None:
    print(m, flush=True)


PATHS = [
    "/api/v4/accounts/{a}/pages/projects",
    "/api/v4/accounts/{a}/pages/projects?per_page=50",
    "/accounts/{a}/pages/projects",
    "/api/v4/accounts/{a}/pages",
]


def main() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), executable_path=str(EXE), headless=False,
            args=["--no-sandbox"], viewport={"width": 1400, "height": 900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/workers-and-pages",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        for tpl in PATHS:
            path = tpl.format(a=ACCOUNT)
            r = page.evaluate(
                """async (path) => {
                    const r = await fetch(path, {headers:{'content-type':'application/json'},
                                                 credentials:'include'});
                    const txt = await r.text();
                    let j = null; try { j = JSON.parse(txt); } catch(e) {}
                    return {status: r.status, ok: j ? j.success : null,
                            n: j && j.result ? (Array.isArray(j.result) ? j.result.length : 1) : null,
                            head: txt.slice(0, 200)};
                }""", path)
            log(f"GET {path} -> {json.dumps(r, ensure_ascii=False)[:400]}")

        # 尝试创建（正确前缀）
        body = {
            "name": "jinba-cars",
            "production_branch": "main",
            "build_config": {"build_command": "", "destination_dir": "/", "root_dir": ""},
            "source": {"type": "github", "config": {
                "owner": "jian522", "repo_name": "china-jinba-used-cars",
                "production_branch": "main", "pr_comments_enabled": True,
                "deployments_enabled": True}},
        }
        res = page.evaluate(
            """async ([aid, body]) => {
                const r = await fetch('/api/v4/accounts/' + aid + '/pages/projects', {
                    method:'POST', headers:{'content-type':'application/json'},
                    credentials:'include', body: JSON.stringify(body)});
                const txt = await r.text();
                let j=null; try { j = JSON.parse(txt); } catch(e) {}
                return {status:r.status, ok: j? j.success : null,
                        name: j&&j.result? j.result.name : null,
                        sub: j&&j.result? j.result.subdomain : null,
                        err: (j&&!j.success)? JSON.stringify(j.errors||j).slice(0,300) : null,
                        raw: txt.slice(0,220)};
            }""", [ACCOUNT, body])
        log("CREATE " + json.dumps(res, ensure_ascii=False)[:700])

        log("HOLDING")
        for _ in range(600):
            time.sleep(5)
        return 0


if __name__ == "__main__":
    sys.exit(main())
