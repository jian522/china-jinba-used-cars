#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金霸二手车出口站 · 飞书报告推送器（带重试 + 失败日志）

用途：把每日上架任务的执行结果推送给店主（飞书私聊）。
通道：复用 WorkBuddy 已授权的 feishu 连接器（lark-cli，bot 身份 → 店主 open_id）。
特性：
  - 失败自动重试（指数退避，默认 4 次）
  - 每次尝试都落日志 .workbuddy/logs/feishu_notify.log（JSONL，成功/失败都记）
  - 支持 --report-file 直接吃 daily_upload.py 的 JSON 结果，自动渲染成中文报告
  - 仅用标准库，无第三方依赖

用法示例：
  python scripts/notify_feishu.py --title "金霸上架" --content "今日上架 4 台"
  python scripts/notify_feishu.py --report-file _pages_deploy/last_daily.json
  python scripts/notify_feishu.py --selftest
退出码：0 成功；1 全部重试仍失败；2 参数/环境错误。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / ".workbuddy" / "logs" / "feishu_notify.log"

# 店主飞书 open_id（user 身份 = 电商用户9999，2026-10-04 核实）
DEFAULT_USER_ID = "ou_befe14f7350ea6642500f8ee61363f48"

_PKG = Path.home() / ".workbuddy" / "binaries" / "node" / "cli-connector-packages"
# Windows 下 .cmd 才能被 subprocess 直接执行（无扩展名的那个是 sh 脚本）
LARK_CANDIDATES = (
    [_PKG / "lark-cli.cmd", _PKG / "lark-cli.exe", _PKG / "lark-cli"]
    if os.name == "nt"
    else [_PKG / "lark-cli"]
)


def find_lark() -> str | None:
    for c in LARK_CANDIDATES:
        if c.exists():
            return str(c)
    return shutil.which("lark-cli.cmd") or shutil.which("lark-cli")


def log(record: dict) -> None:
    record = dict(record)
    record.setdefault("ts", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # 日志失败不影响发送


def render_report(data: dict) -> tuple[str, str]:
    """把任务结果 JSON 渲染成 (标题, 正文)。"""
    date = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    ok = data.get("success", data.get("ok", 0)) or 0
    fail = data.get("failed", data.get("fail", 0)) or 0
    if isinstance(ok, list):
        ok = len(ok)
    if isinstance(fail, list):
        fail = len(fail)
    reasons = data.get("reasons") or data.get("fail_reasons") or []
    if isinstance(reasons, str):
        reasons = [reasons]
    stock = data.get("stock_ids") or data.get("stock_id") or []
    if isinstance(stock, str):
        stock = [stock]

    planned = data.get("planned")
    target = str(data.get("target", "3~5"))
    tmin = int(target.split("~")[0]) if "~" in target else 3
    title = "【金霸每日上架】执行报告 %s" % date
    lines = ["日期：%s" % date]
    if planned:
        lines.append("计划上架：%s 台" % planned)
    lines.append("成功上架：%s 台" % ok)
    if planned:
        lines.append("未上架：%s 台" % max(int(planned) - int(ok), 0))
    elif fail:
        lines.append("失败/遗漏：%s 台" % fail)
    if stock:
        lines.append("车辆编号：%s" % "、".join(str(s) for s in stock))
    lines.append("目标区间：%s 台 ｜ %s" % (target, "达标" if int(ok) >= tmin else "未达标"))
    if reasons:
        lines.append("失败原因：")
        lines.extend("  · %s" % r for r in reasons)
    advice = data.get("advice") or data.get("suggestions") or []
    if isinstance(advice, str):
        advice = [advice]
    if advice:
        lines.append("处理建议：")
        lines.extend("  · %s" % a for a in advice)
    extra = data.get("summary") or data.get("detail")
    if extra:
        lines.append(str(extra))
    return title, "\n".join(lines)


def send_once(lark: str, user_id: str, text: str, identity: str = "bot") -> tuple[bool, str]:
    cmd = [lark, "im", "+messages-send", "--as", identity,
           "--user-id", user_id, "--text", text]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60)
    except Exception as exc:  # noqa: BLE001
        return False, "调用 lark-cli 异常: %s" % exc
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    try:
        payload = json.loads(out) if out else {}
    except json.JSONDecodeError:
        payload = {}
    if proc.returncode == 0 and payload.get("ok") is True:
        mid = ""
        data = payload.get("data") or {}
        if isinstance(data, dict):
            mid = data.get("message_id") or (data.get("message") or {}).get("message_id", "")
        return True, mid or "ok"
    return False, (err or out or "returncode=%s" % proc.returncode)[:500]


def notify(title: str, content: str, user_id: str = DEFAULT_USER_ID,
           retries: int = 4, identity: str = "bot",
           backoff: tuple[int, ...] = (5, 15, 30, 60)) -> bool:
    lark = find_lark()
    if not lark:
        log({"ok": False, "error": "lark-cli not found", "title": title})
        print("[feishu] 未找到 lark-cli，发送失败", file=sys.stderr)
        return False
    text = "%s\n%s" % (title, content)
    last_err = ""
    for attempt in range(1, retries + 1):
        ok, detail = send_once(lark, user_id, text, identity)
        log({"ok": ok, "attempt": attempt, "retries": retries,
             "title": title, "detail": detail,
             "len": len(text)})
        if ok:
            print("[feishu] 已发送（第 %d 次尝试）message_id=%s" % (attempt, detail))
            return True
        last_err = detail
        print("[feishu] 第 %d/%d 次发送失败：%s" % (attempt, retries, detail), file=sys.stderr)
        if attempt < retries:
            wait = backoff[min(attempt - 1, len(backoff) - 1)]
            time.sleep(wait)
    print("[feishu] 全部 %d 次重试均失败，已记录日志 %s" % (retries, LOG_PATH), file=sys.stderr)
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="金霸 · 飞书报告推送器（带重试与失败日志）")
    ap.add_argument("--title", default=None)
    ap.add_argument("--content", default=None)
    ap.add_argument("--report-file", default=None, help="任务结果 JSON 路径")
    ap.add_argument("--user-id", default=DEFAULT_USER_ID)
    ap.add_argument("--as", dest="identity", default="bot", choices=["bot", "user"])
    ap.add_argument("--retries", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="检查 lark-cli 与登录态")
    args = ap.parse_args()

    if args.selftest:
        lark = find_lark()
        print("lark-cli:", lark or "未找到")
        if not lark:
            return 2
        st = subprocess.run([lark, "auth", "status"], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=60)
        print(st.stdout[:1200])
        print("日志文件:", LOG_PATH)
        return 0 if st.returncode == 0 else 2

    if args.report_file:
        p = Path(args.report_file)
        if not p.exists():
            print("报告文件不存在：%s" % p, file=sys.stderr)
            return 2
        data = json.loads(p.read_text(encoding="utf-8"))
        title, content = render_report(data)
        if args.title:
            title = args.title
    else:
        if not (args.title and args.content):
            print("需要 --title 与 --content，或 --report-file", file=sys.stderr)
            return 2
        title, content = args.title, args.content

    if args.dry_run:
        print("== DRY RUN ==")
        print(title)
        print(content)
        return 0

    return 0 if notify(title, content, args.user_id, args.retries, args.identity) else 1


if __name__ == "__main__":
    raise SystemExit(main())
