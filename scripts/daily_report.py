#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金霸二手车出口站 · 每日上架结果核对 + 飞书报告

用途：不依赖上架任务本身，独立核对「今天到底上架了几台」，再推飞书。
因此它既能被上架任务在结束时调用，也能作为独立的「看门狗」定时任务
（上架任务在启动阶段就崩溃时，也只有它能发出报告）。

判定口径（按优先级）：
  1. 今日 git 提交里含 "daily:" 的提交 → 从提交信息解析 JB- 编号 = 成功台数
  2. 无当日提交 → 判定为「未执行 / 失败」，成功 0 台
目标区间默认 3~5 台。

用法：
  python scripts/daily_report.py                 # 核对今天并推送飞书
  python scripts/daily_report.py --no-send       # 只核对不推送
  python scripts/daily_report.py --extra-file .workbuddy/logs/report_extra.json
退出码：0 已推送；1 推送失败；2 参数/环境错误。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import notify_feishu  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REASON_HINT = (
    "未发现当日 daily 提交，上架任务未产生任何车辆。"
    "最常见原因是任务根本没跑起来（WorkBuddy 定时任务启动失败），"
    "其次是采集 0 台或闸门校验未通过。请查 .workbuddy/logs 与今日记忆日志。"
)


def already_sent_today(date_str: str) -> bool:
    """今天是否已成功推送过一次报告（供兜底任务去重，避免重复打扰）。"""
    log = notify_feishu.LOG_PATH
    if not log.exists():
        return False
    try:
        with log.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("ok") and str(rec.get("ts", "")).startswith(date_str):
                    return True
    except OSError:
        return False
    return False


def _git(args: list[str]) -> str:
    try:
        p = subprocess.run(["git"] + args, cwd=str(PROJECT_ROOT), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        return (p.stdout or "").strip()
    except Exception:  # noqa: BLE001
        return ""


def today_daily_commit(date_str: str) -> tuple[str, list[str], str]:
    """返回 (commit_sha, [stock_ids], subject)。"""
    out = _git(["log", "--since=%s 00:00" % date_str, "--until=%s 23:59" % date_str,
                "--grep=daily:", "--pretty=format:%H\x1f%s"])
    if not out:
        return "", [], ""
    first = out.splitlines()[0]
    sha, _, subject = first.partition("\x1f")
    ids = re.findall(r"JB-\d+", subject)
    return sha, ids, subject


def build(date_str: str, expect_min: int, expect_max: int, extra: dict,
          planned: int = 4) -> dict:
    sha, ids, subject = today_daily_commit(date_str)
    ok = len(ids)
    data = {
        "date": date_str,
        "planned": planned,
        "success": ok,
        "target": "%d~%d" % (expect_min, expect_max),
        "stock_ids": ids,
        "commit": sha[:9] if sha else "",
    }
    if ok == 0:
        data["reasons"] = list(extra.get("reasons") or [REASON_HINT])
        data["advice"] = list(extra.get("advice") or [
            "确认定时任务为何未执行（查 .workbuddy/logs/<日期>/sdk/conversations/）",
            "重启 WorkBuddy 客户端后手动补跑 scripts/daily_upload.py",
        ])
    else:
        if ok < expect_min:
            data["reasons"] = ["上架 %d 台，低于目标下限 %d 台" % (ok, expect_min)]
        data["advice"] = []
    if extra.get("summary"):
        data["summary"] = extra["summary"]
    if sha:
        data["summary"] = (data.get("summary", "") +
                           (" ｜ git %s" % sha[:9])).strip(" ｜")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="金霸 · 每日上架结果核对并推送飞书")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--expect-min", type=int, default=3)
    ap.add_argument("--expect-max", type=int, default=5)
    ap.add_argument("--planned", type=int, default=4, help="今日计划上架台数")
    ap.add_argument("--extra-file", default=None, help="补充 reasons/advice 的 JSON")
    ap.add_argument("--no-send", action="store_true")
    ap.add_argument("--skip-if-sent-today", action="store_true",
                    help="今天已成功推送过则直接跳过（兜底任务去重用）")
    ap.add_argument("--retries", type=int, default=4)
    args = ap.parse_args()

    if args.skip_if_sent_today and already_sent_today(args.date):
        print("[daily_report] %s 已推送过报告，跳过（去重）" % args.date)
        return 0

    extra: dict = {}
    if args.extra_file and Path(args.extra_file).exists():
        try:
            extra = json.loads(Path(args.extra_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            extra = {}

    data = build(args.date, args.expect_min, args.expect_max, extra, args.planned)
    title, content = notify_feishu.render_report(data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("----- 飞书报告正文 -----")
    print(title)
    print(content)

    if args.no_send:
        return 0
    return 0 if notify_feishu.notify(title, content, retries=args.retries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
