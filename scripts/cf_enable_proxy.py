#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cloudflare：用已登录的浏览器会话调用官方 API，开启 A 记录代理 + SSL 设 Full。

复用 .workbuddy/cf_profile 的登录态（如未登录会自动打开登录页等待）。
API 调用在页面上下文执行，天然携带 Cloudflare 认证 cookie。
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
DOMAIN = "jinbacars.com"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"


def log(m: str) -> None:
    print(m, flush=True)


def main() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            executable_path=str(EXE),
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            viewport={"width": 1500, "height": 950},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/{DOMAIN}/dns/records",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        log("URL " + page.url)

        if "/login" in page.url:
            log("NEED_LOGIN 请在浏览器中登录")
            for _ in range(180):
                time.sleep(5)
                if "/login" not in page.url:
                    log("LOGIN_OK")
                    break
            else:
                log("LOGIN_TIMEOUT")
                return 2
            page.wait_for_timeout(3000)

        # ---------- 1. 取 zone id ----------
        zone = page.evaluate(
            """async (domain) => {
                const r = await fetch('/api/v4/zones?name=' + domain, {
                    headers: {'content-type':'application/json'}, credentials:'include'});
                const j = await r.json();
                if (!j.success || !j.result.length) return {err: JSON.stringify(j).slice(0,300)};
                const z = j.result[0];
                return {id: z.id, name: z.name, status: z.status, plan: (z.plan||{}).legacy_id};
            }""", DOMAIN)
        log("ZONE " + json.dumps(zone, ensure_ascii=False))
        if "err" in zone or "id" not in zone:
            log("ZONE_FAILED")
            return 3
        zone_id = zone["id"]

        # ---------- 2. 列出 A 记录 ----------
        recs = page.evaluate(
            """async (zid) => {
                const r = await fetch('/api/v4/zones/' + zid + '/dns_records?type=A&per_page=100', {
                    headers: {'content-type':'application/json'}, credentials:'include'});
                const j = await r.json();
                if (!j.success) return {err: JSON.stringify(j).slice(0,300)};
                return j.result.map(x => ({id:x.id, name:x.name, content:x.content, proxied:x.proxied, ttl:x.ttl}));
            }""", zone_id)
        log("RECS_BEFORE " + json.dumps(recs, ensure_ascii=False))
        if isinstance(recs, dict) and "err" in recs:
            log("RECS_FAILED")
            return 4

        # ---------- 3. 逐条开启代理 ----------
        todo = [r for r in recs if not r.get("proxied")]
        log(f"TO_PROXY {len(todo)} 条")
        for r in todo:
            res = page.evaluate(
                """async ([zid, rid, name, content]) => {
                    const r = await fetch('/api/v4/zones/' + zid + '/dns_records/' + rid, {
                        method: 'PATCH',
                        headers: {'content-type':'application/json'},
                        credentials:'include',
                        body: JSON.stringify({type:'A', name:name, content:content, proxied:true, ttl:1})
                    });
                    const j = await r.json();
                    return {ok: j.success, proxied: j.result ? j.result.proxied : null,
                            err: j.success ? null : JSON.stringify(j.errors||j).slice(0,200)};
                }""", [zone_id, r["id"], r["name"], r["content"]])
            log(f"PATCH {r['name']} -> {json.dumps(res, ensure_ascii=False)}")

        # CNAME (www) 也一并开启代理
        cnames = page.evaluate(
            """async (zid) => {
                const r = await fetch('/api/v4/zones/' + zid + '/dns_records?type=CNAME&per_page=100', {
                    headers:{'content-type':'application/json'}, credentials:'include'});
                const j = await r.json();
                return j.success ? j.result.map(x=>({id:x.id,name:x.name,content:x.content,proxied:x.proxied})) : {err:1};
            }""", zone_id)
        log("CNAMES " + json.dumps(cnames, ensure_ascii=False)[:400])
        if isinstance(cnames, list):
            for c in cnames:
                if not c.get("proxied"):
                    res = page.evaluate(
                        """async ([zid, rid, name, content]) => {
                            const r = await fetch('/api/v4/zones/' + zid + '/dns_records/' + rid, {
                                method:'PATCH', headers:{'content-type':'application/json'},
                                credentials:'include',
                                body: JSON.stringify({type:'CNAME', name:name, content:content, proxied:true, ttl:1})});
                            const j = await r.json();
                            return {ok:j.success, proxied:j.result?j.result.proxied:null,
                                    err:j.success?null:JSON.stringify(j.errors||j).slice(0,200)};
                        }""", [zone_id, c["id"], c["name"], c["content"]])
                    log(f"PATCH_CNAME {c['name']} -> {json.dumps(res, ensure_ascii=False)}")

        # ---------- 4. SSL/TLS 设为 Full ----------
        ssl = page.evaluate(
            """async (zid) => {
                const r = await fetch('/api/v4/zones/' + zid + '/settings/ssl', {
                    method:'PATCH', headers:{'content-type':'application/json'},
                    credentials:'include', body: JSON.stringify({value:'full'})});
                const j = await r.json();
                return {ok:j.success, value:j.result?j.result.value:null,
                        err:j.success?null:JSON.stringify(j.errors||j).slice(0,200)};
            }""", zone_id)
        log("SSL " + json.dumps(ssl, ensure_ascii=False))

        # ---------- 5. 复核 ----------
        after = page.evaluate(
            """async (zid) => {
                const r = await fetch('/api/v4/zones/' + zid + '/dns_records?per_page=100', {
                    headers:{'content-type':'application/json'}, credentials:'include'});
                const j = await r.json();
                return j.success ? j.result.map(x=>({type:x.type,name:x.name,content:x.content,proxied:x.proxied}))
                                 : {err:1};
            }""", zone_id)
        log("RECS_AFTER " + json.dumps(after, ensure_ascii=False))

        # 刷新 DNS 页面截图
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/{DOMAIN}/dns/records",
                  wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        page.screenshot(path=str(PREVIEW / "cf_20_dns_done.png"))
        log("SHOT cf_20_dns_done.png")
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/{DOMAIN}/ssl-tls",
                  wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        page.screenshot(path=str(PREVIEW / "cf_21_ssl.png"))
        log("SHOT cf_21_ssl.png")
        log("DONE")

        for _ in range(600):  # 保持 50 分钟后退出
            time.sleep(5)
        return 0


if __name__ == "__main__":
    sys.exit(main())
