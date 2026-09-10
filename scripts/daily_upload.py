#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金霸每日自动上架编排：每天采集 3~5 台热销车型 → 图片修复 → 入库 → 校验 → 部署。

由 WorkBuddy 定时任务每日调用（也可手动跑）。设计要点：
  1. 车型轮换：TARGETS_POOL 20 个热销车型，按"日期序号 × 步长"轮换起点，
     每天取 4 个相邻车型（3~5 台），约 5 天轮完一圈，避免连续两天推同车型。
  2. 号段避让：起始 stock 从 data/vehicles.json 现有最大号 + 大间隔推算，
     不与历史批次冲突。
  3. 幂等：批次名含日期（daily-YYYYMMDD）；当天重跑时先清掉当日半成品目录。
  4. 全链路校验：入库后必跑 photo_check + validate_inventory，不过不部署。
  5. 输出结构化结果（最后一行 JSON），供定时任务转述给用户。

用法：
  "$PY" scripts/daily_upload.py              # 默认 4 台
  "$PY" scripts/daily_upload.py --count 3    # 指定台数（3~5）
  "$PY" scripts/daily_upload.py --dry-run    # 只打印计划不执行
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
DATA = ROOT / "data" / "vehicles.json"

# 每日轮换池（俄/中亚 + 中东 + 高端 + 走量，来自 scrape_wap.TARGETS 的关键词）
TARGETS_POOL = [
    "哈弗H6", "哈弗大狗", "坦克300", "长城炮",
    "宋PLUS DM-i", "元PLUS", "比亚迪海豚", "比亚迪海鸥",
    "比亚迪汉", "比亚迪海豹", "秦PLUS DM-i",
    "理想L6", "理想L7", "问界M7",
    "长安CS75 PLUS", "瑞虎7", "瑞虎8", "博越L", "星越L",
    "哈弗初恋",
]
STEP = 5          # 轮换步长（20 车型 / 4 台每天 = 5 天一圈）
STOCK_START = 9000  # 新批次起始号段（现有最大 JB-8902，留足间隔）


def run(cmd: list[str], **kw) -> tuple[int, str]:
    """跑子命令，返回 (exit, 合并输出)。"""
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=3600, **kw)
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def max_stock_num() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    nums = [int(re.sub(r"\D", "", v["stock_id"])) for v in data if v.get("stock_id")]
    return max(nums) if nums else 0


def pick_targets(n: int) -> list[str]:
    """按日期轮换取 n 个车型：起点 = (当年第几天 × STEP) % len(pool)。"""
    doy = date.today().timetuple().tm_yday
    start = (doy * STEP) % len(TARGETS_POOL)
    return [TARGETS_POOL[(start + i) % len(TARGETS_POOL)] for i in range(n)]


def main() -> int:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    count = 4
    if "--count" in args:
        count = int(args[args.index("--count") + 1])
    count = max(3, min(5, count))

    today = date.today().isoformat()
    batch = f"daily-{today.replace('-', '')}"
    batch_dir = ROOT / "imports" / batch
    csv_path = batch_dir / "vehicles.csv"

    picks = pick_targets(count)
    next_stock = max(max_stock_num() + 1, STOCK_START)
    plan = (f"批次 {batch}｜车型: {', '.join(picks)}｜"
            f"起始库存 JB-{next_stock}｜采集上限 {count} 台")

    if dry:
        print(plan)
        return 0

    print(f"=== 金霸每日上架 {today} ===")
    print(plan)

    # 幂等：清掉当天半成品
    if batch_dir.exists():
        shutil.rmtree(batch_dir)

    # 1) 采集（逐车型跑，共享同一批次目录；stock 号接续递增）
    ok_cars = 0
    for i, kw_ in enumerate(picks):
        prefix = f"JB-{next_stock + i * 10:04d}"
        code, out = run([PY, str(ROOT / ".workbuddy/scrape/scrape_wap.py"),
                         "--kw", kw_, "--n", "1", "--pages", "1",
                         "--batch", batch, "--stock-prefix", prefix])
        m = re.search(r"入库 (\d+) 台|accepted[:=]\s*(\d+)|✅.*?JB-(\d{4})",
                      out)
        got = 1 if (m or "✅" in out or "primary.jpg" in out) else 0
        tail = out.strip().splitlines()[-3:]
        print(f"[采集] {kw_} (prefix {prefix}): {'OK' if got else 'EMPTY'}")
        for line in tail:
            if line.strip():
                print("   ", line.strip()[:120])
        if not got:
            # 该车型当天无符合条件车源，跳过不影响整体
            continue
    if not csv_path.exists():
        print("!! 当天所有车型都未采到符合条件的车源，结束（不算失败）")
        print(json.dumps({"date": today, "batch": batch, "uploaded": 0,
                          "status": "no-stock"}, ensure_ascii=False))
        return 0

    # 2) 入库（预演 → 正式）
    code, out = run([PY, str(ROOT / "scripts/ingest_batch.py"),
                     "--batch", batch, "--csv", str(csv_path)])
    if code != 0:
        print(f"!! 入库预演失败 exit={code}\n{out[-800:]}")
        return 1
    code, out = run([PY, str(ROOT / "scripts/ingest_batch.py"),
                     "--batch", batch, "--csv", str(csv_path), "--commit"])
    if code != 0:
        print(f"!! 正式入库失败 exit={code}\n{out[-800:]}")
        return 1
    m = re.findall(r"\[(add|update)\] (JB-\d{3,4})", out)
    added = [s for _, s in m]
    if not added:
        # 兼容 ingest 输出格式变化：从计划行提取（[更新] JB-xxxx / [新增] JB-xxxx）
        added = re.findall(r"\[(?:更新|add|新增|update)\] (JB-\d{3,4})", out)
    print(f"[入库] 新增/更新 {len(added)} 台: {', '.join(added) or '无'}")

    # 3) 图片合规修复（新车全部过一遍：条带裁剪 + 封面校正）
    code, out = run([PY, str(ROOT / "scripts/photo_fix.py"), "--all", "--commit"])
    print(f"[图片修复] exit={code}")
    if code != 0:
        print(out[-600:])

    # 4) 缩略图 + 重建 + 双校验
    for script, label in [("make_thumbs.py", "缩略图"),
                          ("build_v2.py", "重建页面")]:
        code, out = run([PY, str(ROOT / "scripts" / script)])
        print(f"[{label}] exit={code}")
        if code != 0:
            print(f"!! {label}失败\n{out[-600:]}")
            return 1

    code, out = run([PY, str(ROOT / "scripts/photo_check.py")])
    print(f"[图片校验] exit={code} {out.strip().splitlines()[-1] if out.strip() else ''}")
    if code != 0:
        print(f"!! 图片校验未过，不部署。残留违规:\n{out[-1000:]}")
        return 1

    code, out = run([PY, str(ROOT / "scripts/validate_inventory.py")])
    err_line = next((l for l in out.splitlines() if l.startswith("errors:")), "")
    print(f"[库存校验] exit={code} {err_line}")
    if code != 0 or not err_line.endswith("errors:   0"):
        print(f"!! 库存校验有 ERROR，不部署:\n{out[-1000:]}")
        return 1

    # 5) 提交 git（push_api 以 git HEAD 为基线）
    code, out = run(["git", "add", "-A"])
    code, out = run(["git", "commit", "-m",
                     f"daily: {today} 每日上架 {len(added)} 台 ({', '.join(added)})"])
    print(f"[git] commit exit={code}")

    # 6) 部署
    code, out = run([PY, str(ROOT / "scripts/push_api.py"), "plan"])
    print(f"[部署plan] {out.strip().splitlines()[0] if out.strip() else ''}")
    for _ in range(4):                       # 分批上传直到传完
        code, out = run([PY, str(ROOT / "scripts/push_api.py"), "upload", "150"])
        if "待传 0" in out or "无待传文件" in out or code != 0:
            break
    code, out = run([PY, str(ROOT / "scripts/push_api.py"), "finish",
                     f"daily: {today} 每日上架 {len(added)} 台"])
    deployed = "OK: main ->" in out
    print(f"[部署finish] exit={code} {'✅ 上线' if deployed else '❌ 失败'}")
    if not deployed:
        print(out[-800:])
        return 1

    result = {"date": today, "batch": batch, "uploaded": len(added),
              "stocks": added, "targets": picks, "status": "deployed"}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
