#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站替换 Google Analytics 衡量 ID（默认 G-3SVJ44HVKC → G-NR49LE183C）。

覆盖两类目标：
  1. 已生成的 HTML 页面（zh/ en/ ru/ ar/ 四语 + 根目录散页）
  2. 页面构建脚本中的模板字符串（build_v2*.py / rebuild_home_v*.py 等）

不传 --commit 即预演（默认），只报告改动数量，不写盘。
用法：
  python scripts/set_ga_id.py
  python scripts/set_ga_id.py --commit
  python scripts/set_ga_id.py --from G-XXXX --to G-YYYY --commit
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_DEFAULT = "G-3SVJ44HVKC"
NEW_DEFAULT = "G-NR49LE183C"

# 页面目录（部署范围）
HTML_DIRS = ["zh", "en", "ru", "ar"]
# 根目录散页（不含 _pages_deploy / _preview / .workbuddy 等本地产物）
HTML_ROOT_GLOB = "*.html"
# 构建脚本（模板），避免下次重新构建又写回旧 ID
SCRIPT_GLOBS = ["scripts/*.py"]


def collect_html() -> list[Path]:
    files: list[Path] = []
    for d in HTML_DIRS:
        p = ROOT / d
        if p.is_dir():
            files.extend(sorted(p.rglob("*.html")))
    files.extend(sorted(ROOT.glob(HTML_ROOT_GLOB)))
    return files


def collect_scripts() -> list[Path]:
    files: list[Path] = []
    me = Path(__file__).resolve()
    for g in SCRIPT_GLOBS:
        for f in sorted(ROOT.glob(g)):
            if f.resolve() == me:      # 排除自身，避免改掉默认常量
                continue
            files.append(f)
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="old", default=OLD_DEFAULT)
    ap.add_argument("--to", dest="new", default=NEW_DEFAULT)
    ap.add_argument("--commit", action="store_true", help="真正写盘（缺省=预演）")
    args = ap.parse_args()

    old, new = args.old, args.new
    if old == new:
        print("新旧 ID 相同，无需操作")
        return 2
    pat = re.compile(re.escape(old))

    html_files = collect_html()
    script_files = collect_scripts()

    changed_html: list[tuple[Path, int]] = []
    changed_scripts: list[tuple[Path, int]] = []
    total_hits = 0

    for f in html_files:
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        n = len(pat.findall(txt))
        if not n:
            continue
        total_hits += n
        changed_html.append((f, n))
        if args.commit:
            f.write_text(pat.sub(new, txt), encoding="utf-8")

    for f in script_files:
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        n = len(pat.findall(txt))
        if not n:
            continue
        changed_scripts.append((f, n))
        if args.commit:
            f.write_text(pat.sub(new, txt), encoding="utf-8")

    mode = "已写入" if args.commit else "预演（未写盘）"
    print(f"=== GA 衡量 ID 替换 {mode} ===")
    print(f"{old}  →  {new}")
    print()
    print(f"[HTML 页面] 命中文件 {len(changed_html)} 个，替换点 {sum(n for _, n in changed_html)} 处")
    by_dir: dict[str, int] = {}
    for f, n in changed_html:
        rel = f.relative_to(ROOT)
        key = rel.parts[0] if len(rel.parts) > 1 else "(根目录)"
        by_dir[key] = by_dir.get(key, 0) + 1
    for k in sorted(by_dir):
        print(f"    {k:12s} {by_dir[k]:4d} 个文件")
    print()
    print(f"[构建脚本] 命中文件 {len(changed_scripts)} 个")
    for f, n in changed_scripts:
        print(f"    {f.relative_to(ROOT)}  ({n} 处)")
    print()
    print(f"合计替换点：{total_hits + sum(n for _, n in changed_scripts)}")

    # 校验：写盘后确认旧 ID 已清空
    if args.commit:
        left = 0
        for f in html_files + script_files:
            try:
                if old in f.read_text(encoding="utf-8"):
                    left += 1
            except Exception:
                pass
        print(f"校验：仍含旧 ID 的文件数 = {left}（应为 0）")
        if left:
            return 1
    else:
        print("（预演模式：加 --commit 才会真正写盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
