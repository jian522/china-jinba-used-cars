#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 dashboard 会话创建 Cloudflare API Token（Pages 权限），再用该 Token 建 Pages 项目。

Pages API 不接受 cookie 认证（错误 10000），必须走 API Token。
Token 保存在 .workbuddy/cf_token.txt（已 gitignore 范畴，勿外泄）。
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
TOKEN_FILE = ROOT / ".workbuddy" / "cf_token.txt"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"
OWNER, REPO, PROJECT = "jian522", "china-jinba-used-cars", "jinba-cars"
DOMAINS = ["jinbacars.com", "www.jinbacars.com"]


def log(m: str) -> None:
    print(m, flush=True)


def main() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), executable_path=str(EXE), headless=False,
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--start-minimized"],
            viewport={"width": 1280, "height": 860})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/workers-and-pages",
                  wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(4000)
        log("CF_READY")

        # ---- 1. 获取权限组 ----
        groups = page.evaluate(
            """async () => {
                const r = await fetch('/api/v4/user/tokens/permission_groups',
                    {headers:{'content-type':'application/json'}, credentials:'include'});
                const j = await r.json();
                if (!j.success) return {err: JSON.stringify(j.errors||j).slice(0,200)};
                return j.result.map(g => ({id:g.id, name:g.name}))
                              .filter(g => /page|worker|dns|zone/i.test(g.name));
            }"""
        )
        log("PERM_GROUPS " + json.dumps(groups, ensure_ascii=False)[:1200])
        if isinstance(groups, dict) and "err" in groups:
            log("PERM_FAILED 无法列出权限组（可能需要 UI 创建 token）")
            return 2

        gid = None
        for g in groups:
            if g["name"].lower().startswith("cloudflare pages"):
                gid = g["id"]
                log("USE_GROUP " + json.dumps(g, ensure_ascii=False))
                break
        if not gid:
            log("NO_PAGES_GROUP")
            return 3

        # ---- 2. 创建 Token ----
        res = page.evaluate(
            """async ([gid, aid]) => {
                const body = {
                    name: 'jinba-pages-automation',
                    policies: [{
                        effect: 'allow',
                        resources: {['com.cloudflare.api.account.' + aid]: '*'},
                        permission_groups: [{id: gid}]
                    }]
                };
                const r = await fetch('/api/v4/user/tokens', {
                    method:'POST', headers:{'content-type':'application/json'},
                    credentials:'include', body: JSON.stringify(body)});
                const txt = await r.text();
                let j=null; try { j = JSON.parse(txt); } catch(e) {}
                return {status:r.status, ok: j? j.success:false,
                        value: j&&j.result? j.result.value : null,
                        err: (j&&!j.success)? JSON.stringify(j.errors||j).slice(0,250):null};
            }""", [gid, ACCOUNT])
        log("TOKEN_CREATE " + json.dumps({k: v for k, v in res.items() if k != "value"}, ensure_ascii=False))
        if not res.get("value"):
            log("TOKEN_FAILED")
            return 4

        token = res["value"]
        TOKEN_FILE.write_text(token, encoding="utf-8")
        log(f"TOKEN_SAVED len={len(token)} -> {TOKEN_FILE}")

        # ---- 3. 用 Token 调 Pages API：先列出现有项目 ----
        api = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/pages/projects"
        lst = page.evaluate(
            """async ([api, token]) => {
                const r = await fetch(api, {headers:{
                    'Authorization':'Bearer ' + token, 'content-type':'application/json'}});
                const j = await r.json();
                return {status:r.status, ok:j.success,
                        n: j.result? j.result.length : null,
                        names: j.result? j.result.map(x=>x.name) : null,
                        err: j.success?null:JSON.stringify(j.errors||j).slice(0,200)};
            }""", [api, token])
        log("PAGES_LIST " + json.dumps(lst, ensure_ascii=False)[:600])

        # ---- 4. 创建项目 ----
        body = {
            "name": PROJECT,
            "production_branch": "main",
            "build_config": {"build_command": "", "destination_dir": "", "root_dir": ""},
            "source": {"type": "github", "config": {
                "owner": OWNER, "repo_name": REPO, "production_branch": "main",
                "pr_comments_enabled": True, "deployments_enabled": True}},
        }
        cr = page.evaluate(
            """async ([api, token, body]) => {
                const r = await fetch(api, {method:'POST', headers:{
                    'Authorization':'Bearer ' + token, 'content-type':'application/json'},
                    body: JSON.stringify(body)});
                const j = await r.json();
                return {status:r.status, ok:j.success,
                        name:j.result?j.result.name:null, sub:j.result?j.result.subdomain:null,
                        err:j.success?null:JSON.stringify(j.errors||j).slice(0,250)};
            }""", [api, token, body])
        log("CREATE " + json.dumps(cr, ensure_ascii=False)[:700])

        if not cr.get("ok"):
            log("CREATE_FAILED 需要 GitHub 授权（错误 8000011 需重装 App）")
        else:
            for d in DOMAINS:
                r = page.evaluate(
                    """async ([api, token, proj, domain]) => {
                        const r = await fetch(api + '/' + proj + '/domains', {method:'POST', headers:{
                            'Authorization':'Bearer ' + token, 'content-type':'application/json'},
                            body: JSON.stringify({name: domain})});
                        const j = await r.json();
                        return {ok:j.success, status:j.result?j.result.status:null,
                                err:j.success?null:JSON.stringify(j.errors||j).slice(0,180)};
                    }""", [api, token, PROJECT, d])
                log(f"DOMAIN {d} -> " + json.dumps(r, ensure_ascii=False))

        log("HOLDING")
        for _ in range(360):
            time.sleep(5)
        return 0


if __name__ == "__main__":
    sys.exit(main())
