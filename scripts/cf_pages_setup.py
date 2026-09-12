#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全自动创建 Cloudflare Pages 项目并绑定自定义域。

策略：
  1) 优先用已登录会话调 Cloudflare API 创建 Pages 项目（最可靠）
  2) 若返回 GitHub 未授权 -> 打开 UI 引导页，等待用户完成 OAuth（轮询重试 API）
  3) 创建成功后绑定 jinbacars.com 与 www.jinbacars.com
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
REPO_OWNER = "jian522"
REPO_NAME = "china-jinba-used-cars"
PROJECT = "jinba-cars"
DOMAINS = ["jinbacars.com", "www.jinbacars.com"]


def log(m: str) -> None:
    print(m, flush=True)


CREATE_BODY = {
    "name": PROJECT,
    "production_branch": "main",
    "build_config": {
        "build_command": "",
        "destination_dir": "/",
        "root_dir": "",
    },
    "source": {
        "type": "github",
        "config": {
            "owner": REPO_OWNER,
            "repo_name": REPO_NAME,
            "production_branch": "main",
            "pr_comments_enabled": True,
            "deployments_enabled": True,
            "preview_branch_includes": ["*"],
            "preview_branch_excludes": [],
        },
    },
}


def main() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), executable_path=str(EXE), headless=False,
            args=["--no-sandbox"], viewport={"width": 1500, "height": 980})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/workers-and-pages",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        log("URL " + page.url)

        # ---------- 尝试 API 创建 ----------
        def try_create():
            return page.evaluate(
                """async ([aid, body]) => {
                    const r = await fetch('/accounts/' + aid + '/pages/projects', {
                        method:'POST', headers:{'content-type':'application/json'},
                        credentials:'include', body: JSON.stringify(body)});
                    let j; try { j = await r.json(); } catch(e) { return {ok:false, err:'nonjson', status:r.status}; }
                    return {status:r.status, ok:j.success,
                            name:j.result?j.result.name:null,
                            domains:j.result?j.result.domains:null,
                            subdomain:j.result?j.result.subdomain:null,
                            err:j.success?null:JSON.stringify(j.errors||j).slice(0,300)};
                }""", [ACCOUNT, CREATE_BODY])

        res = try_create()
        log("CREATE_1 " + json.dumps(res, ensure_ascii=False))

        if not res.get("ok"):
            # GitHub 未授权 -> 打开引导页等用户操作，同时轮询重试
            log("NEED_GITHUB 请在浏览器中完成 GitHub 授权（选择仓库后告诉我，或授权完静候）")
            page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/workers-and-pages/create",
                      wait_until="domcontentloaded")
            page.wait_for_timeout(6000)
            page.screenshot(path=str(PREVIEW / "cfp_need_github.png"))
            log("SHOT cfp_need_github.png")

            # 尝试穿透 shadow DOM 点击"连接到 Git"/"GitHub"
            clicked = page.evaluate(
                """() => {
                    const texts = ['连接到 Git','Connect to Git','GitHub','连接 GitHub'];
                    function walk(root, out) {
                        if (!root) return;
                        for (const el of root.querySelectorAll('*')) {
                            if (el.shadowRoot) walk(el.shadowRoot, out);
                            const t = (el.innerText || el.textContent || '').trim();
                            if (!t || t.length > 80) continue;
                            for (const kw of texts) {
                                if (t.includes(kw)) {
                                    // 向上找可点击祖先
                                    let n = el, tag = '';
                                    for (let i = 0; i < 5 && n; i++) {
                                        tag = (n.tagName || '').toLowerCase();
                                        if (tag === 'button' || tag === 'a' ||
                                            n.getAttribute?.('role') === 'button') {
                                            n.click();
                                            return {clicked: kw, tag: tag};
                                        }
                                        n = n.parentElement || n.getRootNode()?.host;
                                    }
                                    el.click();
                                    return {clicked: kw, tag: 'self'};
                                }
                            }
                        }
                    }
                    const out = [];
                    walk(document, out);
                    return out.length ? out[0] : {clicked: null};
                }"""
            )
            log("CLICK " + json.dumps(clicked, ensure_ascii=False))
            page.wait_for_timeout(4000)
            page.screenshot(path=str(PREVIEW / "cfp_after_click.png"))
            log("SHOT cfp_after_click.png")
            log("URL_AFTER_CLICK " + page.url)

            # 轮询等待用户完成授权并重试创建（最多 20 分钟）
            for i in range(240):
                time.sleep(5)
                try:
                    if "github.com" in page.url:
                        continue  # 用户在 GitHub 授权页
                    r2 = try_create()
                except Exception as e:
                    continue
                if r2.get("ok"):
                    log("CREATE_2_OK " + json.dumps(r2, ensure_ascii=False))
                    res = r2
                    break
                if i % 12 == 0:  # 每分钟输出一次状态
                    log(f"WAITING_GITHUB {i*5}s err=" + str(r2.get("err"))[:120])
            else:
                log("GITHUB_TIMEOUT 未完成授权")
                return 2

        if not res.get("ok"):
            log("CREATE_FAILED " + json.dumps(res, ensure_ascii=False))
            return 3

        log(f"PROJECT_CREATED name={res.get('name')} subdomain={res.get('subdomain')}")

        # ---------- 绑定自定义域 ----------
        for d in DOMAINS:
            r = page.evaluate(
                """async ([aid, proj, domain]) => {
                    const r = await fetch('/accounts/' + aid + '/pages/projects/' + proj + '/domains', {
                        method:'POST', headers:{'content-type':'application/json'},
                        credentials:'include', body: JSON.stringify({name: domain})});
                    let j; try { j = await r.json(); } catch(e) { return {ok:false, err:'nonjson', status:r.status}; }
                    return {ok:j.success, name:j.result?j.result.name:null, status:j.result?j.result.status:null,
                            err:j.success?null:JSON.stringify(j.errors||j).slice(0,220)};
                }""", [ACCOUNT, PROJECT, d])
            log(f"DOMAIN {d} -> " + json.dumps(r, ensure_ascii=False))

        # ---------- 复核 ----------
        info = page.evaluate(
            """async ([aid, proj]) => {
                const r = await fetch('/accounts/' + aid + '/pages/projects/' + proj, {
                    headers:{'content-type':'application/json'}, credentials:'include'});
                const j = await r.json();
                if (!j.success) return {err: JSON.stringify(j.errors||j).slice(0,200)};
                const p = j.result;
                return {name:p.name, subdomain:p.subdomain, domains:p.domains,
                        production_branch:p.production_branch,
                        build:p.build_config, source:(p.source||{}).type,
                        latest:(p.latest_deployment||{}).url};
            }""", [ACCOUNT, PROJECT])
        log("PROJECT_INFO " + json.dumps(info, ensure_ascii=False)[:900])

        page.goto(f"https://dash.cloudflare.com/{ACCOUNT}/workers-and-pages",
                  wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        page.screenshot(path=str(PREVIEW / "cfp_final.png"))
        log("SHOT cfp_final.png DONE")

        for _ in range(600):
            time.sleep(5)
        return 0


if __name__ == "__main__":
    sys.exit(main())
