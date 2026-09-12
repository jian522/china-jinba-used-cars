#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""后台轮询：等待 GitHub App 授权完成后自动创建 Pages 项目并绑定自定义域。

headless 运行（不占用户屏幕），每 5 秒尝试创建一次，成功即继续。
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "_preview"
PREVIEW.mkdir(exist_ok=True)
PROFILE = ROOT / ".workbuddy" / "cf_profile"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"
OWNER, REPO, PROJECT = "jian522", "china-jinba-used-cars", "jinba-cars"
DOMAINS = ["jinbacars.com", "www.jinbacars.com"]
PROXY = "http://127.0.0.1:7890"

BODY = {
    "name": PROJECT,
    "production_branch": "main",
    "build_config": {"build_command": "", "destination_dir": "/", "root_dir": ""},
    "source": {"type": "github", "config": {
        "owner": OWNER, "repo_name": REPO, "production_branch": "main",
        "pr_comments_enabled": True, "deployments_enabled": True}},
}


def log(m: str) -> None:
    print(m, flush=True)


def main() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), executable_path=str(EXE),
            headless=False,
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                  "--disable-features=IsolateOrigins,site-per-process",
                  "--start-minimized"],
            viewport={"width": 1280, "height": 860})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/workers-and-pages",
                  wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(4000)
        log("CF_READY " + page.url)

        def try_create():
            return page.evaluate(
                """async ([aid, body]) => {
                    const r = await fetch('/api/v4/accounts/' + aid + '/pages/projects', {
                        method:'POST', headers:{'content-type':'application/json'},
                        credentials:'include', body: JSON.stringify(body)});
                    const txt = await r.text();
                    let j=null; try { j = JSON.parse(txt); } catch(e) {}
                    return {status:r.status, ok: j? j.success : false,
                            name: j&&j.result? j.result.name : null,
                            sub: j&&j.result? j.result.subdomain : null,
                            err: (j&&!j.success)? JSON.stringify(j.errors||j).slice(0,180) : null};
                }""", [ACCOUNT, BODY])

        res = try_create()
        log("TRY_0 " + json.dumps(res, ensure_ascii=False))

        ok = res.get("ok")
        waited = 0
        while not ok and waited < 1800:  # 最多 30 分钟
            time.sleep(5)
            waited += 5
            try:
                r = try_create()
            except Exception:
                continue
            if r.get("ok"):
                res, ok = r, True
                log("CREATED " + json.dumps(res, ensure_ascii=False))
                break
            if waited % 60 == 0:
                log(f"WAIT {waited}s err=" + str(r.get("err"))[:90])
        if not ok:
            log("TIMEOUT 仍未授权")
            return 2

        # 绑定自定义域
        for d in DOMAINS:
            r = page.evaluate(
                """async ([aid, proj, domain]) => {
                    const r = await fetch('/api/v4/accounts/' + aid + '/pages/projects/' + proj + '/domains', {
                        method:'POST', headers:{'content-type':'application/json'},
                        credentials:'include', body: JSON.stringify({name: domain})});
                    const txt = await r.text();
                    let j=null; try { j = JSON.parse(txt); } catch(e) {}
                    return {ok: j? j.success:false, status: j&&j.result? j.result.status:null,
                            err:(j&&!j.success)?JSON.stringify(j.errors||j).slice(0,180):null};
                }""", [ACCOUNT, PROJECT, d])
            log(f"DOMAIN {d} -> " + json.dumps(r, ensure_ascii=False))

        info = page.evaluate(
            """async ([aid, proj]) => {
                const r = await fetch('/api/v4/accounts/' + aid + '/pages/projects/' + proj,
                    {headers:{'content-type':'application/json'}, credentials:'include'});
                const j = await r.json();
                if (!j.success) return {err: JSON.stringify(j.errors||j).slice(0,200)};
                const p = j.result;
                return {name:p.name, subdomain:p.subdomain, domains:p.domains,
                        branch:p.production_branch, source:(p.source||{}).type,
                        latest_url:(p.latest_deployment||{}).url,
                        latest_status:(p.latest_deployment||{}).status};
            }""", [ACCOUNT, PROJECT])
        log("INFO " + json.dumps(info, ensure_ascii=False)[:800])
        log("ALL_DONE")
        return 0


if __name__ == "__main__":
    sys.exit(main())
