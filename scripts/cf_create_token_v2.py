#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建 token：精确匹配 Pages Write 权限组（上次误选 Custom Pages Read）。"""
import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path("d:/二手车出口网站")
PROFILE = ROOT / ".workbuddy" / "cf_profile"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
TOKEN_FILE = ROOT / ".workbuddy" / "cf_token.txt"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"

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

    # 精确找 Pages Write
    gid = page.evaluate("""async () => {
        const r = await fetch('/api/v4/user/tokens/permission_groups', {credentials:'include'});
        const j = await r.json();
        if (!j.success) return null;
        const g = j.result.find(x => x.name === 'Pages Write');
        return g ? g.id : null;
    }""")
    print("PAGES_WRITE_GID", gid, flush=True)
    if not gid:
        raise SystemExit(3)

    res = page.evaluate("""async ([gid, aid]) => {
        const body = {
            name: 'jinba-wrangler-upload-v2',
            policies: [{
                effect: 'allow',
                resources: {['com.cloudflare.api.account.' + aid]: '*'},
                permission_groups: [{id: gid}]
            }]
        };
        const r = await fetch('/api/v4/user/tokens', {
            method:'POST', credentials:'include',
            headers:{'content-type':'application/json'}, body: JSON.stringify(body)});
        const j = await r.json();
        return {ok: j.success, value: j.result ? j.result.value : null,
                err: j.success ? null : JSON.stringify(j.errors||j).slice(0,250)};
    }""", [gid, ACCOUNT])
    print("TOKEN", json.dumps({k: v for k, v in res.items() if k != "value"}, ensure_ascii=False), flush=True)
    if not res.get("value"):
        raise SystemExit(4)

    TOKEN_FILE.write_text(res["value"], encoding="utf-8")
    print(f"TOKEN_SAVED len={len(res['value'])}", flush=True)

    page.wait_for_timeout(1500)
    ctx.close()
