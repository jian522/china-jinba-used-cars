#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cloudflare 站点加速优化：Always HTTPS / Brotli / Minify / 浏览器缓存 TTL。"""
from __future__ import annotations

import json
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "_preview"
PROFILE = ROOT / ".workbuddy" / "cf_profile"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
DOMAIN = "jinbacars.com"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"
ZONE = "c9b48e5c76c121593eff18f6d9164795"


def log(m: str) -> None:
    print(m, flush=True)


SETTINGS = [
    ("always_use_https", {"value": "on"}),
    ("brotli", {"value": "on"}),
    ("minify", {"value": {"css": "on", "html": "on", "js": "on"}}),
    ("browser_cache_ttl", {"value": 14400}),          # 4 小时
    ("cache_level", {"value": "aggressive"}),         # 静态资源激进缓存
    ("security_level", {"value": "medium"}),
    ("ssl", {"value": "full"}),
    ("opportunistic_encryption", {"value": "on"}),
    ("http2", {"value": "on"}),
    ("http3", {"value": "on"}),
    ("0rtt", {"value": "on"}),
]


def main() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), executable_path=str(EXE), headless=False,
            args=["--no-sandbox"], viewport={"width": 1500, "height": 950})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/{DOMAIN}", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        log("URL " + page.url)
        if "/login" in page.url:
            log("NEED_LOGIN")
            for _ in range(180):
                time.sleep(5)
                if "/login" not in page.url:
                    log("LOGIN_OK"); break
            else:
                log("LOGIN_TIMEOUT"); return 2

        for name, body in SETTINGS:
            res = page.evaluate(
                """async ([zid, name, body]) => {
                    const r = await fetch('/api/v4/zones/' + zid + '/settings/' + name, {
                        method:'PATCH', headers:{'content-type':'application/json'},
                        credentials:'include', body: JSON.stringify(body)});
                    let j; try { j = await r.json(); } catch(e) { return {ok:false, err:'json'}; }
                    return {ok: j.success, value: j.result ? j.result.value : null,
                            err: j.success ? null : JSON.stringify(j.errors||j).slice(0,160)};
                }""", [ZONE, name, body])
            log(f"SET {name} -> {json.dumps(res, ensure_ascii=False)}")

        # 复核关键设置
        check = page.evaluate(
            """async (zid) => {
                const names = ['ssl','always_use_https','brotli','browser_cache_ttl','cache_level'];
                const out = {};
                for (const n of names) {
                    const r = await fetch('/api/v4/zones/' + zid + '/settings/' + n, {
                        headers:{'content-type':'application/json'}, credentials:'include'});
                    const j = await r.json();
                    out[n] = j.success ? j.result.value : 'ERR';
                }
                return out;
            }""", ZONE)
        log("VERIFY " + json.dumps(check, ensure_ascii=False))

        # 清一次 Cloudflare 缓存，确保访客拿到最新页面
        purge = page.evaluate(
            """async (zid) => {
                const r = await fetch('/api/v4/zones/' + zid + '/purge_cache', {
                    method:'POST', headers:{'content-type':'application/json'},
                    credentials:'include', body: JSON.stringify({purge_everything:true})});
                const j = await r.json();
                return {ok: j.success, err: j.success?null:JSON.stringify(j.errors||j).slice(0,160)};
            }""", ZONE)
        log("PURGE " + json.dumps(purge, ensure_ascii=False))

        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/{DOMAIN}", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        page.screenshot(path=str(PREVIEW / "cf_30_overview.png"))
        log("SHOT cf_30_overview.png DONE")
        for _ in range(300):
            time.sleep(5)
        return 0


if __name__ == "__main__":
    sys.exit(main())
