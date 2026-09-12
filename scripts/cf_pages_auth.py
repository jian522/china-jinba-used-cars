#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打开 GitHub App 授权页 -> 等用户授权 -> 自动创建 Pages 项目并绑定域名。

错误码 8000011 = Cloudflare Pages 的 GitHub App 安装异常，需重新授权。
授权入口：https://github.com/apps/cloudflare-pages/installations/new
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
            user_data_dir=str(PROFILE), executable_path=str(EXE), headless=False,
            args=["--no-sandbox"], viewport={"width": 1400, "height": 950})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Cloudflare 页面（保持登录态，用于 API 调用）
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/workers-and-pages",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        # 新标签打开 GitHub 授权页
        gh = ctx.new_page()
        gh.goto("https://github.com/apps/cloudflare-pages/installations/new",
                wait_until="domcontentloaded", timeout=60000)
        gh.wait_for_timeout(3000)
        gh.bring_to_front()
        log("GITHUB_PAGE " + gh.url)
        gh.screenshot(path=str(PREVIEW / "gh_01_authorize.png"))
        log("SHOT gh_01_authorize.png")
        log("ACTION 请在 GitHub 页面完成授权：选择 jian522 账号 → 授权 china-jinba-used-cars → 点 Install/保存")

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
                            err: (j&&!j.success)? JSON.stringify(j.errors||j).slice(0,200) : null};
                }""", [ACCOUNT, BODY])

        res = try_create()
        log("CREATE_INITIAL " + json.dumps(res, ensure_ascii=False))

        ok = res.get("ok")
        if not ok:
            for i in range(240):  # 等 20 分钟
                time.sleep(5)
                try:
                    r2 = try_create()
                except Exception:
                    continue
                if r2.get("ok"):
                    res = r2
                    ok = True
                    log("CREATE_OK_AFTER_AUTH " + json.dumps(res, ensure_ascii=False))
                    break
                if i % 12 == 0:
                    log(f"WAIT {i*5}s last_err=" + str(r2.get("err"))[:100])
            else:
                log("AUTH_TIMEOUT")
                gh.screenshot(path=str(PREVIEW / "gh_timeout.png"))
                return 2

        log(f"CREATED name={res.get('name')} subdomain={res.get('sub')}")

        # 绑定自定义域
        for d in DOMAINS:
            r = page.evaluate(
                """async ([aid, proj, domain]) => {
                    const r = await fetch('/api/v4/accounts/' + aid + '/pages/projects/' + proj + '/domains', {
                        method:'POST', headers:{'content-type':'application/json'},
                        credentials:'include', body: JSON.stringify({name: domain})});
                    const txt = await r.text();
                    let j=null; try { j = JSON.parse(txt); } catch(e) {}
                    return {ok: j? j.success:false, status: j&&j.result? j.result.status : null,
                            err: (j&&!j.success)? JSON.stringify(j.errors||j).slice(0,180):null};
                }""", [ACCOUNT, PROJECT, d])
            log(f"DOMAIN {d} -> " + json.dumps(r, ensure_ascii=False))

        # 复核项目
        info = page.evaluate(
            """async ([aid, proj]) => {
                const r = await fetch('/api/v4/accounts/' + aid + '/pages/projects/' + proj,
                    {headers:{'content-type':'application/json'}, credentials:'include'});
                const j = await r.json();
                if (!j.success) return {err: JSON.stringify(j.errors||j).slice(0,200)};
                const p = j.result;
                return {name:p.name, subdomain:p.subdomain, domains:p.domains,
                        branch:p.production_branch, source:(p.source||{}).type,
                        latest:(p.latest_deployment||{}).url, status:(p.latest_deployment||{}).status};
            }""", [ACCOUNT, PROJECT])
        log("INFO " + json.dumps(info, ensure_ascii=False)[:800])

        page.bring_to_front()
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/workers-and-pages",
                  wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        page.screenshot(path=str(PREVIEW / "pages_final.png"))
        log("SHOT pages_final.png DONE")
        for _ in range(600):
            time.sleep(5)
        return 0


if __name__ == "__main__":
    sys.exit(main())
