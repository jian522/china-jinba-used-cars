#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断登录态：检查是否被登出 + 尝试恢复 + 清缓存。"""
import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path("d:/二手车出口网站")
PROFILE = ROOT / ".workbuddy" / "cf_profile"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
ZONE = "c9b48e5c76c121593eff18f6d9164795"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE), executable_path=str(EXE), headless=False,
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 860})
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://dash.cloudflare.com/", wait_until="load", timeout=90000)
    page.wait_for_timeout(6000)
    path = page.evaluate("() => location.pathname")
    print("LANDING", path, flush=True)

    if "/login" in path:
        # 尝试邮箱魔法链接/记住登录：等用户看一眼窗口。先检查是否有记住会话自动恢复按钮
        page.wait_for_timeout(2000)
        path2 = page.evaluate("() => location.pathname")
        print("STILL", path2, flush=True)
        # 截图给用户看状态
        page.screenshot(path=str(ROOT / "_preview" / "cf_login_state.png"))
        print("SCREENSHOT saved _preview/cf_login_state.png", flush=True)
    else:
        r = page.evaluate("""async (zone) => {
            const res = await fetch(`/api/v4/zones/${zone}/purge_cache`, {
                method:'POST', credentials:'include',
                headers:{'content-type':'application/json'},
                body: JSON.stringify({purge_everything:true})});
            const j = await res.json();
            return {status: res.status, success: j.success, errors: j.errors};
        }""", ZONE)
        print("PURGE", json.dumps(r, ensure_ascii=False), flush=True)

    ctx.close()
