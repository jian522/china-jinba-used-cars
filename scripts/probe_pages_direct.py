#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测 Pages Direct Upload API 可行性（用 dashboard cookie 会话）。"""
import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path("d:/二手车出口网站")
PROFILE = ROOT / ".workbuddy" / "cf_profile"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"

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
    page.wait_for_timeout(5000)

    # 1. 创建 Direct Upload 类型项目（不带 source 字段）
    r = page.evaluate("""async () => {
        const res = await fetch('/api/v4/accounts/0cd64536d2bc18ae46651a0a2636e1ff/pages/projects', {
            method: 'POST', credentials: 'include',
            headers: {'content-type': 'application/json'},
            body: JSON.stringify({name: 'jinba-cars', production_branch: 'main'})});
        const j = await res.json();
        return {status: res.status, ok: j.success,
                name: j.result ? j.result.name : null,
                subdomain: j.result ? j.result.subdomain : null,
                err: j.success ? null : JSON.stringify(j.errors || j).slice(0, 300)};
    }""")
    print("CREATE_DIRECT", json.dumps(r, ensure_ascii=False), flush=True)

    # 2. 列出项目验证
    r2 = page.evaluate("""async () => {
        const res = await fetch('/api/v4/accounts/0cd64536d2bc18ae46651a0a2636e1ff/pages/projects', {credentials: 'include'});
        const j = await res.json();
        return {ok: j.success, names: j.result ? j.result.map(x => x.name) : null,
                err: j.success ? null : JSON.stringify(j.errors).slice(0, 200)};
    }""")
    print("LIST", json.dumps(r2, ensure_ascii=False), flush=True)

    page.wait_for_timeout(1500)
    ctx.close()
