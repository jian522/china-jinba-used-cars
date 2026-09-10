#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切换 DNS 到 Cloudflare Pages：
  1. 检查 Pages 自定义域名验证状态
  2. 删除 @ 的 4 条 GitHub Pages A 记录（185.199.x.x）
  3. @ 建 CNAME -> jinba-cars.pages.dev（ apex 用 CNAME 打平）
  4. www CNAME 改指 -> jinba-cars.pages.dev
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path("d:/二手车出口网站")
PROFILE = ROOT / ".workbuddy" / "cf_profile"
EXE = pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe"
ACCOUNT = "0cd64536d2bc18ae46651a0a2636e1ff"
ZONE = "c9b48e5c76c121593eff18f6d9164795"
PROJECT = "jinba-cars"


def log(m):
    print(m, flush=True)


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE), executable_path=str(EXE), headless=False,
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--start-minimized"],
        viewport={"width": 1280, "height": 860})
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/pages/view/{PROJECT}/domains",
              wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(5000)

    # 1. Pages 域名验证状态
    st = page.evaluate("""async ([aid, proj]) => {
        const r = await fetch(`/api/v4/accounts/${aid}/pages/projects/${proj}/domains`, {credentials:'include'});
        const j = await r.json();
        return j.success ? j.result.map(d => ({name: d.name, status: d.status,
            verification: d.verification_data ? d.verification_data.status : null})) : j.errors;
    }""", [ACCOUNT, PROJECT])
    log("DOMAIN_STATUS " + json.dumps(st, ensure_ascii=False))

    # 2. 列出 DNS A/CNAME 记录
    recs = page.evaluate("""async (zone) => {
        const r = await fetch(`/api/v4/zones/${zone}/dns_records?type=A&per_page=50`, {credentials:'include'});
        const j = await r.json();
        const a = j.success ? j.result : [];
        const r2 = await fetch(`/api/v4/zones/${zone}/dns_records?type=CNAME&per_page=50`, {credentials:'include'});
        const j2 = await r2.json();
        const c = j2.success ? j2.result : [];
        return a.concat(c).map(x => ({id: x.id, type: x.type, name: x.name, content: x.content, proxied: x.proxied}));
    }""", ZONE)
    log("DNS_RECORDS " + json.dumps(recs, ensure_ascii=False))

    # 3. 删除指向 GitHub Pages 的记录（@ A 记录 185.199.* + www CNAME -> *.github.io）
    for x in recs:
        hit = (x["type"] == "A" and x["name"].startswith(("jinbacars.com", "www.jinbacars.com"))
               and x["content"].startswith("185.199.")) or \
              (x["type"] == "CNAME" and x["name"].startswith("www.jinbacars.com")
               and "github.io" in x["content"])
        if not hit:
            continue
        d = page.evaluate("""async ([zone, id, name, content]) => {
            const r = await fetch(`/api/v4/zones/${zone}/dns_records/${id}`, {method:'DELETE', credentials:'include'});
            const j = await r.json();
            return {ok: j.success, name, content};
        }""", [ZONE, x["id"], x["name"], x["content"]])
        log(f"DELETE {x['type']} {x['name']} {x['content']} -> {json.dumps(d, ensure_ascii=False)}")

    # 4. 建 @ CNAME -> jinba-cars.pages.dev（apex CNAME flattening）
    apex = page.evaluate("""async ([zone, proj]) => {
        const r = await fetch(`/api/v4/zones/${zone}/dns_records`, {method:'POST', credentials:'include',
            headers:{'content-type':'application/json'},
            body: JSON.stringify({type:'CNAME', name:'jinbacars.com', content:'jinba-cars.pages.dev',
                                  proxied:true, ttl:1})});
        const j = await r.json();
        return {ok: j.success, err: j.success?null:JSON.stringify(j.errors).slice(0,200)};
    }""", [ZONE, PROJECT])
    log("CREATE_APEX_CNAME " + json.dumps(apex, ensure_ascii=False))

    # 5. www CNAME -> jinba-cars.pages.dev
    www = page.evaluate("""async ([zone, proj]) => {
        const r = await fetch(`/api/v4/zones/${zone}/dns_records`, {method:'POST', credentials:'include',
            headers:{'content-type':'application/json'},
            body: JSON.stringify({type:'CNAME', name:'www', content:'jinba-cars.pages.dev',
                                  proxied:true, ttl:1})});
        const j = await r.json();
        return {ok: j.success, err: j.success?null:JSON.stringify(j.errors).slice(0,200)};
    }""", [ZONE, PROJECT])
    log("CREATE_WWW_CNAME " + json.dumps(www, ensure_ascii=False))

    page.wait_for_timeout(1500)
    ctx.close()

log("DNS_SWITCH_DONE")
