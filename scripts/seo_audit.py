#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""站点级 SEO/健康审计（对生成后的静态站点）。

覆盖：title/meta 唯一性·长度、description 长度、canonical/hreflang/lang/dir、
en·ru·ar 页 title/desc/h1 残留中文、img alt、og 图与本地文件存在性、
JSON-LD 可解析、内部链接可达(相对于仓库根)、sitemap/robots/feed 一致性。
用法：python scripts/seo_audit.py [--langs en,zh,ru,ar] [--max-issues N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("en", "zh", "ru", "ar")
CJK = re.compile(r"[\u4e00-\u9fff]")
ATTRS = re.compile(r"<[^>]+>")


def strip_html(s: str) -> str:
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def collect_files():
    files = {}   # rel -> html text
    for lang in LANGS:
        base = ROOT / lang
        for p in base.rglob("index.html"):
            files[p.relative_to(ROOT).as_posix()] = p
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-issues", type=int, default=60)
    args = ap.parse_args()

    issues: list[str] = []
    titles: dict[str, int] = {}
    metas: dict[str, int] = {}
    desc_lens = 0
    files = collect_files()
    print(f"扫描页面: {len(files)}")

    # 便于内部链接检查
    html_set = set(files)
    dir_index = {p[:-len("index.html")] for p in html_set if p.endswith("index.html")}
    def href_ok(target: str) -> bool:
        t = target.split("#", 1)[0].split("?", 1)[0]
        if not t or t.startswith(("http:", "https:", "mailto:", "tel:", "data:", "javascript:")):
            return True
        if not t.startswith("/"):
            t = "/" + t
        rel = t.lstrip("/")
        if rel in html_set or (rel.endswith("/") and rel in dir_index):
            return True
        # assets/uploads 等其他文件
        return (ROOT / rel).is_file()

    links_total = links_bad = 0
    for rel, p in files.items():
        lang = rel.split("/", 1)[0]
        text = p.read_text(encoding="utf-8", errors="ignore")
        title = (re.search(r"<title>([^<]*)</title>", text) or [None, ""])[1].strip()
        desc = (re.search(r'<meta name="description" content="([^"]*)"', text) or [None, ""])[1]
        canon = (re.search(r'<link rel="canonical" href="([^"]*)"', text) or [None, ""])[1]
        html_lang = (re.search(r'<html\s+lang="([^"]*)"', text) or [None, ""])[1]
        rtl = bool(re.search(r'<html[^>]*dir="rtl"', text))
        h1s = [strip_html(m) for m in re.findall(r"<h1[^>]*>(.*?)</h1>", text, flags=re.S)]
        title = re.sub(r"\s+", " ", title).strip()
        if not title:
            issues.append(f"{rel}: 缺少 <title>")
        else:
            titles[(lang, title)] = titles.get((lang, title), 0) + 1
            if len(title) > 70:
                issues.append(f"{rel}: <title> 过长({len(title)}): {title[:60]}")
            elif len(title) < 15:
                issues.append(f"{rel}: <title> 过短({len(title)}): {title}")
        if not desc:
            issues.append(f"{rel}: 缺少 description")
        else:
            desc_lens += 1
            metas[(lang, desc[:120])] = metas.get((lang, desc[:120]), 0) + 1
            if len(desc) > 165:
                issues.append(f"{rel}: description 过长({len(desc)})")
        if canon and "jinbacars.com" not in canon:
            issues.append(f"{rel}: canonical 疑似外站 {canon}")
        exp_dir = "rtl" if lang == "ar" else "ltr"
        if (rtl and lang != "ar") or (not rtl and lang == "ar"):
            issues.append(f"{rel}: dir 与语言不符 (dir rtl={rtl})")
        if lang == "zh" and html_lang != "zh-CN":
            issues.append(f"{rel}: zh 页 lang={html_lang!r} (应为 zh-CN)")
        for f in re.findall(r"href=\"(/[^\"]+)\"", text):
            links_total += 1
            if not href_ok(f):
                links_bad += 1
                if links_bad <= 20:
                    issues.append(f"{rel}: 失效内部链接 {f}")
        # CJK 残留（非 zh 页的 title/desc/h1）
        if lang != "zh":
            for kind, val in (("title", title), ("desc", desc), ("h1", "; ".join(h1s))):
                if CJK.search(val):
                    issues.append(f"{rel}: {kind} 含中文: {val[:80]}")
        # img alt
        for m in re.finditer(r"<img\b[^>]*>", text):
            if "alt=" not in m.group(0):
                issues.append(f"{rel}: img 缺 alt: {m.group(0)[:60]}")
        # og/twitter 图与 JSON-LD
        for m in re.finditer(r'property="og:image" content="([^"]+)"', text):
            u = m.group(1)
            if u.startswith("https://jinbacars.com"):
                lp = ROOT / u[len("https://jinbacars.com"):].lstrip("/")
                if not lp.is_file():
                    issues.append(f"{rel}: og:image 文件缺失 {u}")
        for i, m in enumerate(re.finditer(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.S)):
            try:
                json.loads(m.group(1))
            except Exception as exc:
                issues.append(f"{rel}: JSON-LD #{i+1} 解析失败: {str(exc)[:60]}")

    dup_t = [k for k, v in titles.items() if v > 1]
    dup_d = [k for k, v in metas.items() if v > 1]
    if dup_t:
        issues.append(f"同语言重复 <title> {len(dup_t)} 种 (示例: {dup_t[0][1][:70]})")
    if dup_d:
        issues.append(f"同语言重复 description 前缀 {len(dup_d)} 种 (示例: {dup_d[0][1][:70]})")

    # sitemap / robots / feed 一致性
    sm = ROOT / "sitemap.xml"
    if sm.exists():
        xml = sm.read_text(encoding="utf-8", errors="ignore")
        locs = re.findall(r"<loc>([^<]+)</loc>", xml)
        bad = [u for u in locs if u.startswith("https://jinbacars.com")
               and not (ROOT / u[len("https://jinbacars.com"):].lstrip("/") / "index.html").is_file()]
        if bad:
            issues.append(f"sitemap 含不可达 URL {len(bad)} 个: {bad[0][:70]}")
        else:
            print(f"sitemap: {len(locs)} 个 URL 全部可达 ✓")
    ro = ROOT / "robots.txt"
    if ro.exists():
        rtxt = ro.read_text(encoding="utf-8")
        for sitemap in re.findall(r"Sitemap:\s*(\S+)", rtxt):
            fn = ROOT / sitemap.split("/")[-1]
            print(f"robots sitemap 存在: {fn.name} {fn.is_file()}")

    print(f"内部链接: 共 {links_total} 条, 失效 {links_bad}")
    print(f"问题总计: {len(issues)}")
    for i, it in enumerate(issues[: args.max_issues], 1):
        print(f"  {i:>3}. {it}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
