#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jinbacars.com 真实访问统计（GA4 Data API 官方口径，替代失真的 CF RUM）。

前置（一次性）：
  1. GA4 → 管理 → 属性设置 → 数据收集和修改 → API 凭据服务账号 → 创建服务账号
  2. 下载 JSON 私钥，存到 .workbuddy/ga4-service-account.json
  3. 把 JSON 里的 client_email 加到 GA4 属性「属性访问权限管理」并授予「查看者」
  4. 记下 property_id（GA4 → 管理 → 属性设置 → 属性 ID，纯数字，如 123456789）

用法：
  python scripts/ga4_report.py --property-id 123456789 --days 30
  python scripts/ga4_report.py --property-id 123456789 --days 7 --json

依赖：google-analytics-data（首次运行自动提示安装命令）
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
CRED = ROOT / ".workbuddy" / "ga4-service-account.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--property-id", required=True, help="GA4 属性 ID（纯数字）")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not CRED.exists():
        print("缺少凭证：%s" % CRED, file=sys.stderr)
        print("按本文件顶部「前置」4 步操作后重试。", file=sys.stderr)
        return 2
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Dimension, Metric,
        )
    except ImportError:
        print("缺依赖，先运行：", file=sys.stderr)
        print('  "%s" -m pip install google-analytics-data' % sys.executable, file=sys.stderr)
        return 3

    import os
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CRED)
    client = BetaAnalyticsDataClient()
    pid = "properties/" + str(args.property_id)
    start = (date.today() - timedelta(days=args.days)).isoformat()
    req_base = dict(property=pid, date_ranges=[DateRange(start_date=start, end_date="today")])

    def run(dims, mets, limit=30, order=None):
        r = RunReportRequest(
            **req_base,
            dimensions=[Dimension(name=d) for d in dims],
            metrics=[Metric(name=m) for m in mets],
            limit=limit,
            **({"order_bys": order} if order else {}),
        )
        return client.run_report(r)

    def table(resp, dim_label="维度", met_label="值"):
        rows = []
        hd = [d.name for d in resp.dimension_headers]
        hm = [m.name for m in resp.metric_headers]
        for row in resp.rows:
            d = " / ".join(v.value for v in row.dimension_values)
            m = [v.value for v in row.metric_values]
            rows.append((d, m))
        return hd, hm, rows

    out: dict = {}
    print("=" * 60)
    print("jinbacars.com GA4 真实统计 | 近 %d 天 | 属性 %s" % (args.days, args.property_id))
    print("=" * 60)

    # 总览
    ov = run([], ["activeUsers", "sessions", "screenPageViews", "bounceRate",
                  "averageSessionDuration", "conversions"])
    m = ov.rows[0].metric_values if ov.rows else []
    names = [x.name for x in ov.metric_headers]
    vals = dict(zip(names, [v.value for v in m]))
    print("\n[总览]")
    for k in names:
        v = vals.get(k, "")
        if k == "bounceRate":
            v = "%.1f%%" % (float(v or 0) * 100)
        elif k == "averageSessionDuration":
            v = "%.0f 秒" % float(v or 0)
        print("  %-28s %s" % (k, v))
    out["overview"] = vals

    # 分维度
    for key, dims, label in (
        ("country", ["country"], "国家/地区"),
        ("city", ["city"], "城市 Top15"),
        ("device", ["deviceCategory"], "设备"),
        ("source", ["sessionDefaultChannelGroup"], "获客渠道"),
        ("page", ["pagePath"], "热门页面 Top20"),
        ("lang", ["language"], "浏览器语言"),
    ):
        resp = run(dims, ["activeUsers", "sessions"], limit=20)
        _, _, rows = table(resp)
        print("\n[%s]" % label)
        for d, mv in rows[:15]:
            print("  %-40s 用户 %-8s 会话 %s" % (d[:40], mv[0], mv[1]))
        out[key] = rows

    # 每日趋势
    resp = RunReportRequest(
        property=pid,
        date_ranges=[DateRange(start_date=start, end_date="today")],
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="activeUsers"), Metric(name="sessions")],
        limit=400,
    )
    daily = client.run_report(resp)
    print("\n[每日趋势]")
    for row in daily.rows:
        print("  %s  用户 %-6s 会话 %s" % (
            row.dimension_values[0].value,
            row.metric_values[0].value, row.metric_values[1].value))
    out["daily"] = [(r.dimension_values[0].value, r.metric_values[0].value)
                    for r in daily.rows]

    if args.json:
        p = ROOT / ".workbuddy" / "ga4_report.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\n原始 JSON ->", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
