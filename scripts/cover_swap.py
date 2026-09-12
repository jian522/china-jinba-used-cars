#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按挑选表把指定车辆的封面换成合规外观图（正前脸 / 左前 45°）。

背景：2026-09-12 用户指出库存首页首图仍有内饰/车尾/局部特写。旧的自动
"外观分"启发式在 70 台库存上漏报 23 台（纯图像特征无法稳定区分"左前 45°
外观"与"车内视角"），因此改为：人工逐台目检挑选（picks 表）→ 本脚本机械换图。

**核心设计（吸取 2026-09-12 首版 bug 教训）**：
  只互换【物理文件内容】，完全不动 vehicles.json 的 photos 列表。
  photos[0] 恒为 /uploads/cars/<id>/primary.webp，因文件名语义与列表位置
  始终对齐，杜绝"列表换了、文件也换了"导致的二次颠倒。
  实现：内容互换（读 A 内容 + B 内容 → 写回），而非 rename（rename 需
  同时维护列表，易错）。

用法：
  "$PY" scripts/cover_swap.py --picks .workbuddy/cover_picks.json            # 预演
  "$PY" scripts/cover_swap.py --picks .workbuddy/cover_picks.json --commit   # 写盘
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vehicles.json"


def thumb_of(p: Path) -> Path:
    return p.with_name(p.name.replace(".webp", ".th.webp"))


def swap_content(a: Path, b: Path) -> None:
    """互换两文件的内容（含各自 .th.webp 缩略图）。文件名位置不变。"""
    for p, q in ((a, b), (thumb_of(a), thumb_of(b))):
        if not (p.is_file() and q.is_file()):
            continue
        pa, pb = p.read_bytes(), q.read_bytes()
        p.write_bytes(pb)
        q.write_bytes(pa)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", required=True, help="JSON: {vehicle_id: photo_index}")
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    picks = {int(k): int(v) for k, v in
             json.loads(Path(args.picks).read_text(encoding="utf-8")).items()}
    data = json.loads(DATA.read_text(encoding="utf-8"))
    byid = {v["id"]: v for v in data}

    n = 0
    for vid, idx in sorted(picks.items()):
        v = byid.get(vid)
        if v is None:
            print(f"!! id {vid} 不在库中")
            continue
        photos = v.get("photos") or []
        if idx == 0:
            print(f"   {v['stock_id']} (id {vid}) 已是目标封面，跳过")
            continue
        if idx >= len(photos):
            print(f"!! {v['stock_id']} (id {vid}) 序号 {idx} 越界（共 {len(photos)}）")
            continue
        cover = ROOT / photos[0].lstrip("/")
        target = ROOT / photos[idx].lstrip("/")
        if not target.is_file():
            print(f"!! {v['stock_id']} 候选缺失：{photos[idx]}")
            continue
        print(f"   {v['stock_id']} (id {vid}): 封面内容 ← {target.name}"
              f"  {'[写盘]' if args.commit else '[预演]'}")
        if args.commit:
            swap_content(cover, target)
            n += 1

    print(f"\n{'已换封面' if args.commit else '预演'} {n if args.commit else len(picks)} 台")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
