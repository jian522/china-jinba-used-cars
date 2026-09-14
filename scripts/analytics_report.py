#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jinbacars.com 访问统计报告（Cloudflare Web Analytics + 边缘流量 + 爬虫）。

用法：
    python scripts/analytics_report.py              # 最近 30 天
    python scripts/analytics_report.py --days 7
    python scripts/analytics_report.py --realtime   # 近 30 分钟（含 1 分钟粒度）
    python scripts/analytics_report.py --all        # 全部可查区间（13 周）

依赖：.workbuddy/cf_analytics_token.txt（Account Analytics Read + Zone Analytics Read）
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / ".workbuddy" / "cf_analytics_token.txt"
ACC = "0cd64536d2bc18ae46651a0a2636e1ff"
ZONE = "c9b48e5c76c121593eff18f6d9164795"
SITE = "4a64f395c5574cacac8e750e029f6573"
API = "https://api.cloudflare.com/client/v4/graphql"
PROXY = os.environ.get("CF_PROXY", "http://127.0.0.1:7890")
CN = {}


def load_token() -> str:
    if not TOKEN_FILE.exists():
        print("缺少 token 文件：%s" % TOKEN_FILE, file=sys.stderr)
        print("运行 .workbuddy/wb_cf_http.py 可重新生成。", file=sys.stderr)
        sys.exit(2)
    return TOKEN_FILE.read_text(encoding="utf-8").strip()


def gql(token: str, query: str) -> dict:
    s = requests.Session()
    s.proxies = {"http": PROXY, "https": PROXY}
    r = s.post(API, headers={"Authorization": "Bearer " + token,
                             "Content-Type": "application/json"},
               data=json.dumps({"query": query}), timeout=90)
    if r.status_code != 200:
        return {"_status": r.status_code, "_body": r.text[:300]}
    return r.json()


def unwrap(res: dict, key: str) -> list:
    """从 graphql 响应里取出第一个 data 数组。"""
    if res.get("errors"):
        msg = res["errors"][0].get("message", "")
        if "13w2d" in msg:
            return []
        print("  [!] %s" % msg[:120], file=sys.stderr)
    d = res.get("data") or {}
    v = d.get("viewer") or {}
    for bucket in ("accounts", "zones"):
        for item in (v.get(bucket) or []):
            if key in item:
                return item[key] or []
    return []


def fmt_int(n) -> str:
    try:
        return "{:,}".format(int(n))
    except Exception:
        return str(n)


def bar(n: int, total: int, width: int = 22) -> str:
    if total <= 0:
        return ""
    k = max(1, int(round(n / total * width)))
    return "█" * k


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--all", action="store_true", help="用满 13 周可查区间")
    ap.add_argument("--realtime", action="store_true", help="近 30 分钟")
    ap.add_argument("--json", action="store_true", help="输出原始 JSON")
    ap.add_argument("--save", action="store_true", help="同时保存 Markdown 报告")
    args = ap.parse_args()

    token = load_token()
    now = datetime.now(timezone.utc)

    if args.realtime:
        since = (now - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        days_label = "近 30 分钟"
        filt = 'siteTag: "%s", datetime_geq: "%s"' % (SITE, since)
    else:
        if args.all:
            since = (now - timedelta(days=90)).strftime("%Y-%m-%d")
            days_label = "近 90 天（可查上限）"
        else:
            since = (now - timedelta(days=args.days)).strftime("%Y-%m-%d")
            days_label = "近 %d 天" % args.days
        filt = 'siteTag: "%s", date_geq: "%s"' % (SITE, since)
    out = {}
    lines: list[str] = []

    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    # ---------- 1. 总览 ----------
    q = """{ viewer { accounts(filter: {accountTag: "%s"}) {
      pv: rumPageloadEventsAdaptiveGroups(limit: 5000, filter: {%s}) {
        count dimensions { siteTag } }
      uv: rumPageloadEventsAdaptiveGroups(limit: 5000, filter: {%s}) {
        sum { visits } dimensions { siteTag } }
    } } }""" % (ACC, filt, filt)
    res = gql(token, q)
    out["overview"] = res
    pv_rows = unwrap(res, "pv")
    uv_rows = unwrap(res, "uv")
    pv = sum(int(r.get("count") or 0) for r in pv_rows)
    uv = sum(int((r.get("sum") or {}).get("visits") or 0) for r in uv_rows)

    emit("═" * 62)
    emit("jinbacars.com 访问统计  |  %s" % days_label)
    emit("统计口径：Cloudflare Web Analytics（真实浏览器，不含爬虫）")
    emit("═" * 62)
    emit("")
    emit("浏览量 pageviews : %s" % fmt_int(pv))
    emit("访问数 visits    : %s" % fmt_int(uv))
    emit("人均浏览         : %.2f 页/次" % (pv / uv if uv else 0))
    emit("")

    # ---------- 2. 每日趋势 ----------
    q = """{ viewer { accounts(filter: {accountTag: "%s"}) {
      rumPageloadEventsAdaptiveGroups(limit: 400, orderBy: [date_ASC], filter: {%s}) {
        count sum { visits } dimensions { date }
      } } } }""" % (ACC, filt)
    res = gql(token, q)
    out["daily"] = res
    daily = unwrap(res, "rumPageloadEventsAdaptiveGroups")
    emit("── 每日明细 ──────────────────────────────────")
    if not daily:
        emit("  （该区间无数据）")
    else:
        mx = max(int(r.get("count") or 0) for r in daily) or 1
        for r in daily[-45:]:
            d = r["dimensions"]["date"]
            c = r.get("count") or 0
            v = (r.get("sum") or {}).get("visits") or 0
            emit("  %s  %-4s 浏览  %-4s 访问  %s" % (d, fmt_int(c), fmt_int(v), bar(c, mx, 18)))
    emit("")

    # ---------- 3. 国家/地区 ----------
    q = """{ viewer { accounts(filter: {accountTag: "%s"}) {
      rumPageloadEventsAdaptiveGroups(limit: 60, orderBy: [count_DESC], filter: {%s}) {
        count sum { visits } dimensions { countryName }
      } } } }""" % (ACC, filt)
    res = gql(token, q)
    out["country"] = res
    rows = unwrap(res, "rumPageloadEventsAdaptiveGroups")
    emit("── 国家 / 地区 ───────────────────────────────")
    if not rows:
        emit("  （无数据）")
    else:
        tot = sum(int(r.get("count") or 0) for r in rows) or 1
        for r in rows[:25]:
            c = r.get("count") or 0
            v = (r.get("sum") or {}).get("visits") or 0
            nm = r["dimensions"].get("countryName") or "未知"
            emit("  %-22s %-5s 浏览 %-5s 访问  %5.1f%%  %s"
                 % (nm, fmt_int(c), fmt_int(v), c / tot * 100, bar(c, tot, 16)))
    emit("")

    # ---------- 4. 热门页面 ----------
    q = """{ viewer { accounts(filter: {accountTag: "%s"}) {
      rumPageloadEventsAdaptiveGroups(limit: 60, orderBy: [count_DESC], filter: {%s}) {
        count sum { visits } dimensions { requestPath }
      } } } }""" % (ACC, filt)
    res = gql(token, q)
    out["path"] = res
    rows = unwrap(res, "rumPageloadEventsAdaptiveGroups")
    emit("── 热门页面 ──────────────────────────────────")
    if not rows:
        emit("  （无数据）")
    else:
        for r in rows[:20]:
            c = r.get("count") or 0
            p = r["dimensions"].get("requestPath") or "/"
            emit("  %-46s %s 浏览" % (p[:46], fmt_int(c)))
    emit("")

    # ---------- 5. 访客环境 ----------
    for key, label, dim in (("device", "设备类型", "deviceType"),
                            ("browser", "浏览器", "userAgentBrowser"),
                            ("os", "操作系统", "userAgentOS"),
                            ("referer", "来源站点", "refererHost")):
        q = """{ viewer { accounts(filter: {accountTag: "%s"}) {
          rumPageloadEventsAdaptiveGroups(limit: 30, orderBy: [count_DESC], filter: {%s}) {
            count dimensions { %s }
          } } } }""" % (ACC, filt, dim)
        res = gql(token, q)
        out[key] = res
        rows = unwrap(res, "rumPageloadEventsAdaptiveGroups")
        emit("── %s ──────────────────────────────" % label)
        if not rows:
            emit("  （无数据）")
        else:
            tot = sum(int(r.get("count") or 0) for r in rows) or 1
            for r in rows[:12]:
                c = r.get("count") or 0
                nm = r["dimensions"].get(dim) or "未知"
                emit("  %-26s %-5s (%4.1f%%)" % (str(nm)[:26], fmt_int(c), c / tot * 100))
        emit("")

    # ---------- 6. 边缘层（含爬虫） ----------
    q = """{ viewer { zones(filter: {zoneTag: "%s"}) {
      httpRequests1dGroups(limit: 40, orderBy: [date_DESC], filter: {date_geq: "%s"}) {
        dimensions { date } sum { requests pageViews bytes threats } uniq { uniques }
      } } } }""" % (ZONE, since[:10])
    res = gql(token, q)
    out["edge"] = res
    rows = unwrap(res, "httpRequests1dGroups")
    emit("── 边缘层流量（含搜索引擎爬虫，仅供参考）──────")
    if not rows:
        emit("  （无数据或超出免费版可查区间）")
    else:
        treq = sum(int((r.get("sum") or {}).get("requests") or 0) for r in rows)
        tpv = sum(int((r.get("sum") or {}).get("pageViews") or 0) for r in rows)
        tuni = sum(int((r.get("uniq") or {}).get("uniques") or 0) for r in rows)
        emit("  总请求 %s  |  页面浏览 %s  |  去重访客(逐日相加) %s"
             % (fmt_int(treq), fmt_int(tpv), fmt_int(tuni)))
        for r in rows[:14]:
            s = r.get("sum") or {}
            emit("  %s  请求 %-6s 浏览 %-6s 威胁 %s"
                 % (r["dimensions"]["date"], fmt_int(s.get("requests")),
                    fmt_int(s.get("pageViews")), fmt_int(s.get("threats"))))
    emit("")
    emit("─" * 62)
    malformed = [k for k, v in out.items() if isinstance(v, dict) and v.get("_status")]
    if malformed:
        emit("提示：以下查询未成功：%s" % ", ".join(malformed))
    emit("数据源：Cloudflare Web Analytics（站点 %s）" % SITE[:8])

    if args.json:
        (ROOT / ".workbuddy" / "analytics_raw.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\n原始 JSON → .workbuddy/analytics_raw.json")
    if args.save:
        p = ROOT / "data" / ("analytics_%s.md" % now.strftime("%Y%m%d_%H%M"))
        p.parent.mkdir(exist_ok=True)
        p.write_text("\n".join(lines), encoding="utf-8")
        print("\n报告已保存 → %s" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
