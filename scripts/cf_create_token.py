#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 dashboard 登录态创建 API Token（wrangler Direct Upload 用），并验证 token 有效性。"""
import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path("d:/二手车出口网站")
PROFILE = ROOT / ".workbuddy" / "cf_profile"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
TOKEN_FILE = ROOT / ".workbuddy" / "cf_token.txt"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE), executable_path=str(EXE), headless=False,
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--start-minimized"],
        viewport={"width": 1280, "height": 860})
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://dash.cloudflare.com/profile/api-tokens",
              wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(5000)

    # 1. 列权限组，找 Cloudflare Pages
    groups = page.evaluate("""async () => {
        const r = await fetch('/api/v4/user/tokens/permission_groups', {credentials:'include'});
        const j = await r.json();
        if (!j.success) return {err: JSON.stringify(j.errors||j).slice(0,200)};
        return j.result.map(g => ({id:g.id, name:g.name}))
                      .filter(g => /pages|worker/i.test(g.name));
    }""")
    print("GROUPS", json.dumps(groups, ensure_ascii=False), flush=True)
    if isinstance(groups, dict) and "err" in groups:
        raise SystemExit(2)

    gid = None
    for g in groups:
        if "pages" in g["name"].lower():
            gid = g["id"]
            break
    if not gid:
        raise SystemExit(3)

    # 2. 创建 token（Pages 编辑权限 + 用户详情读，wrangler 需要）
    res = page.evaluate("""async ([gid]) => {
        const body = {
            name: 'jinba-wrangler-upload',
            policies: [{
                effect: 'allow',
                resources: {'com.cloudflare.api.account.*': '*'},
                permission_groups: [{id: gid}]
            }]
        };
        const r = await fetch('/api/v4/user/tokens', {
            method:'POST', credentials:'include',
            headers:{'content-type':'application/json'}, body: JSON.stringify(body)});
        const j = await r.json();
        return {ok: j.success, value: j.result ? j.result.value : null,
                err: j.success ? null : JSON.stringify(j.errors||j).slice(0,250)};
    }""", [gid])
    print("TOKEN", json.dumps({k: v for k, v in res.items() if k != "value"}, ensure_ascii=False), flush=True)
    if not res.get("value"):
        raise SystemExit(4)

    TOKEN_FILE.write_text(res["value"], encoding="utf-8")
    print(f"TOKEN_SAVED len={len(res['value'])}", flush=True)

    # 3. 用 token 验证 Pages 项目访问
    v = page.evaluate("""async ([token]) => {
        const r = await fetch('https://api.cloudflare.com/client/v4/accounts/0cd64536d2bc18ae46651a0a2636e1ff/pages/projects', {
            headers: {'Authorization': 'Bearer ' + token}});
        const j = await r.json();
        return {ok: j.success, names: j.result ? j.result.map(x=>x.name) : null,
                err: j.success ? null : JSON.stringify(j.errors).slice(0,200)};
    }""", [res["value"]])
    print("VERIFY", json.dumps(v, ensure_ascii=False), flush=True)

    page.wait_for_timeout(1500)
    ctx.close()
