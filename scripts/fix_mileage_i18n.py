#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""止血：把 vehicles.json 中中文 'X万公里' 的 mileage 显示字段规范化为
站点约定格式 '{km} km'（与车辆 1..160 一致），并同步修正已生成页面里
原样输出的 'X万公里' 文本（en/zh/ru/ar 四处一律替换，保证后续全量重建
与本次修复结果一致）。

安全：纯文本/JSON 值替换；不改动 HTML 结构、不动生成器逻辑。
运行：python scripts/fix_mileage_i18n.py   （先 git status 确认工作区干净）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANG_DIRS = ("en", "zh", "ru", "ar")
RE_MILEAGE_CN = re.compile(r"^(\d+)\s*万公里$")


def cn_to_km(text: str):
    m = RE_MILEAGE_CN.match(text.strip())
    if not m:
        return None
    return f"{int(m.group(1)) * 10000} km"


def main() -> int:
    data_path = ROOT / "data" / "vehicles.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))

    changed_records = 0
    replacements = {}  # zh-text -> canonical-text
    for v in data:
        mi = (v.get("mileage") or "").strip()
        canon = cn_to_km(mi)
        if not canon:
            continue
        expect = int(mi[:-3]) * 10000
        if v.get("mileage_km") is None or int(v["mileage_km"]) != expect:
            print(f"  !! 不一致: id={v.get('id')} {v.get('stock_id')} "
                  f"mileage={mi!r} mileage_km={v.get('mileage_km')} -> 跳过, 需人工处理")
            continue
        replacements[mi] = canon
        if v["mileage"] != canon:
            v["mileage"] = canon
            changed_records += 1

    if not replacements:
        print("数据里没有中文里程显示串，无需修复。")
        return 0

    data_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"vehicles.json 已更新 {changed_records} 条: "
          + ", ".join(f"{k}->{replacements[k]}" for k in sorted(replacements)))

    # 同步修正已生成 HTML 中原样输出的中文里程（值替换）
    for lang in LANG_DIRS:
        hits = 0
        for f in (ROOT / lang).rglob("*.html"):
            try:
                text = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            new = text
            for zh, canon in replacements.items():
                new = new.replace(zh, canon)
            if new != text:
                f.write_text(new, encoding="utf-8")
                hits += 1
        print(f"{lang}/ 修正 {hits} 个页面")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
