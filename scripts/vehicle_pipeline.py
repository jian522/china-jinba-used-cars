#!/usr/bin/env python3
"""Jinba 车辆数据采集管道 v1.0

用途：
  从「车商提供的车辆清单 CSV/Excel」+「本地图片文件夹」规范化导入车辆数据与图片，
  与现有 data/vehicles.json、assets/vehicle-images.json 无缝对接。

合规边界（重要）：
  - 本脚本不抓取二手车之家 / 瓜子二手车等平台页面。这些平台在 robots.txt 与
    用户协议中明确禁止自动化抓取，且图片版权属于平台与车商。
  - 合规数据来源：
    1) 车商直接提供的车辆清单与实拍图（首选，有授权）
    2) 品牌官网公开参数（配置参数可用，需记录来源）
    3) GitHub Issue 导入流程（已有 batch_photo_import.py，含授权确认勾选）
  - 如需参考平台公开信息，请人工浏览后手动录入，不要自动化抓取。

用法：
  1. 复制 data/import-template.csv 为你的批次文件，按行填写车辆
  2. 把每台车的图片放入 imports/<批次名>/<stock_id>/ 文件夹（6-9 张，jpg/png/webp）
  3. 运行: python scripts/vehicle_pipeline.py --batch imports/<批次名>
  4. 脚本输出校验报告；通过后图片规范化到 uploads/cars/<id>/，数据并入 vehicles.json

数据结构（并入 vehicles.json 的字段）：
  id / stock_id / title / brand / model / year / mileage / mileage_km /
  fuel / transmission / price / price_usd / body_type / color / drive /
  engine / seats / emission / departure_port / trade_term / vin_last6 /
  registration_date / production_date / status / photos[]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import time
from datetime import date
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vehicles.json"
IMAGES_INDEX = ROOT / "assets" / "vehicle-images.json"
UPLOADS = ROOT / "uploads" / "cars"
ALLOWED_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
PHOTO_MIN, PHOTO_MAX = 6, 10  # 展示标准：外观+内饰 6-10 张，首图为前脸或左前 45°
REQUIRED_FIELDS = ["stock_id", "title", "brand", "year", "mileage_km", "price_usd", "fuel"]

# 常见燃料/变速箱别名归一化（车商写法 → 站点标准值）
FUEL_MAP = {
    "纯电": "纯电", "ev": "纯电", "electric": "纯电", "bev": "纯电",
    "插混": "插混", "dmi": "插混", "dm-i": "插混", "phev": "插混", "增程": "插混",
    "混动": "混动", "hev": "混动", "hybrid": "混动",
    "柴油": "柴油", "diesel": "柴油",
    "汽油": "Petrol", "petrol": "Petrol", "gasoline": "Petrol", "燃油": "Petrol",
}
TRANS_MAP = {
    "自动": "自动", "at": "自动", "cvt": "自动", "dct": "自动",
    "dsg": "自动", "automatic": "自动", "auto": "自动",
    "手动": "手动", "mt": "手动", "manual": "手动",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def die(msg: str) -> None:
    log(f"[错误] {msg}")
    sys.exit(1)


def norm_fuel(raw: str) -> str:
    return FUEL_MAP.get(raw.strip().lower(), raw.strip())


def norm_trans(raw: str) -> str:
    return TRANS_MAP.get(raw.strip().lower(), raw.strip())


def parse_mileage_km(raw: str) -> int:
    """『4.5万公里』『45,000 km』『45000』统一成整数公里。"""
    s = str(raw).strip().lower().replace(",", "").replace("，", "")
    m = re.search(r"([\d.]+)\s*万", s)
    if m:
        return int(float(m.group(1)) * 10000)
    m = re.search(r"([\d.]+)", s)
    if m:
        return int(float(m.group(1)))
    die(f"无法解析里程: {raw!r}")


def parse_price_usd(raw: str) -> str:
    s = re.sub(r"[^\d.]", "", str(raw))
    if not s:
        return "Ask price"
    return f"${int(float(s)):,}"


def image_fingerprint(path: Path) -> str:
    """文件字节哈希做精确去重（快，够用；像素级去重由导入时 PIL 指纹补充）。"""
    return sha256(path.read_bytes()).hexdigest()


def next_vehicle_id(vehicles: list[dict]) -> int:
    return max((int(v["id"]) for v in vehicles), default=0) + 1


def next_stock_id(vehicles: list[dict]) -> str:
    used = {v.get("stock_id", "") for v in vehicles}
    n = max((int(re.sub(r"\D", "", s) or 0) for s in used), default=0)
    while True:
        n += 1
        candidate = f"JB-{n:04d}"
        if candidate not in used:
            return candidate


def load_batch_csv(batch_dir: Path) -> list[dict]:
    csv_path = batch_dir / "vehicles.csv"
    if not csv_path.is_file():
        die(f"缺少 {csv_path}。复制 data/import-template.csv 开始填写")
    with csv_path.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        die("CSV 为空")
    return rows


def validate_batch(batch_dir: Path, rows: list[dict], vehicles: list[dict]) -> list[dict]:
    """校验 + 归一化。任何硬错误直接终止；软警告记录后继续。"""
    existing_stocks = {str(v.get("stock_id", "")).upper() for v in vehicles}
    existing_vins = {str(v.get("vin_last6", "")).upper() for v in vehicles if v.get("vin_last6")}
    seen_stocks: set[str] = set()
    seen_fp: dict[str, str] = {}
    normalized: list[dict] = []

    for i, row in enumerate(rows, 1):
        ctx = f"第{i}行 {row.get('stock_id') or '(未填)'}"
        # 必填字段
        for f in REQUIRED_FIELDS:
            if not str(row.get(f, "")).strip():
                die(f"{ctx}: 缺少必填字段 {f}")

        stock_id = str(row["stock_id"]).strip().upper()
        if not re.fullmatch(r"JB-\d{4}", stock_id):
            die(f"{ctx}: stock_id 必须是 JB-0000 格式")
        if stock_id in existing_stocks:
            log(f"  [更新] {ctx}: 库存号已存在，将更新该车辆")
        if stock_id in seen_stocks:
            die(f"{ctx}: 批次内 stock_id 重复")
        seen_stocks.add(stock_id)

        vin = str(row.get("vin_last6", "")).strip().upper()
        if vin and vin in {"-", "无", "N/A"}:
            vin = ""
        if vin and not re.fullmatch(r"[A-Z0-9]{6}", vin):
            die(f"{ctx}: vin_last6 必须是 6 位字母数字")
        if vin and vin in existing_vins and stock_id not in existing_stocks:
            die(f"{ctx}: VIN 尾号 {vin} 已被其他车辆使用（防重复上架）")

        year = int(row["year"])
        if not 2005 <= year <= date.today().year + 1:
            die(f"{ctx}: 年份 {year} 不合理")

        km = parse_mileage_km(row["mileage_km"])
        if km > 500000:
            log(f"  [警告] {ctx}: 里程 {km}km 异常偏高，请人工确认")

        # 图片文件夹校验
        photo_dir = batch_dir / stock_id
        if not photo_dir.is_dir():
            die(f"{ctx}: 缺少图片文件夹 {photo_dir}")
        photos = sorted(
            p for p in photo_dir.iterdir()
            if p.suffix.lower() in ALLOWED_IMG_EXT and p.is_file()
        )
        if not PHOTO_MIN <= len(photos) <= PHOTO_MAX:
            die(f"{ctx}: 图片数量 {len(photos)} 张，要求 {PHOTO_MIN}-{PHOTO_MAX} 张")
        # 首图角度无法自动判定，仅提醒人工确认（规范见 imports/车商索图与拍摄规范.md）
        log(f"  [确认] {ctx}: 首图 = {photos[0].name}，须为前脸正视或左前 45°（人工确认）")
        for p in photos:
            fp = image_fingerprint(p)
            if fp in seen_fp:
                die(f"{ctx}: 图片 {p.name} 与 {seen_fp[fp]} 字节完全相同（跨车辆重复图）")
            seen_fp[fp] = f"{stock_id}/{p.name}"

        normalized.append({
            "row": row, "stock_id": stock_id, "vin": vin, "year": year, "km": km,
            "photos": photos,
        })
    return normalized


def import_photos(items: list[dict], id_by_stock: dict[str, int]) -> dict[str, list[str]]:
    """图片规范化落盘: uploads/cars/<id>/primary.jpg + NN_photo_N.jpg"""
    UPLOADS.mkdir(parents=True, exist_ok=True)
    result: dict[str, list[str]] = {}
    for item in items:
        vid = id_by_stock[item["stock_id"]]
        dest_dir = UPLOADS / str(vid)
        dest_dir.mkdir(exist_ok=True)
        rel: list[str] = []
        for idx, src in enumerate(item["photos"]):
            name = "primary.jpg" if idx == 0 else f"{vid}_photo_{idx + 1}.jpg"
            dest = dest_dir / name
            # 统一转成 ≤1600px JPEG，控制仓库体积
            convert_to_jpeg(src, dest)
            rel.append(f"/uploads/cars/{vid}/{name}")
            time.sleep(0.05)  # 温和的写盘节奏，避免瞬时 IO 尖峰
        result[item["stock_id"]] = rel
        log(f"  [图片] {item['stock_id']} → {len(rel)} 张已规范化")
    return result


def convert_to_jpeg(src: Path, dest: Path, max_side: int = 1600) -> None:
    try:
        from PIL import Image, ImageOps
    except ImportError:
        die("需要 Pillow: pip install Pillow")
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if max(im.size) > max_side:
            im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        im.save(dest, "JPEG", quality=82, optimize=True, progressive=True)


def merge_records(
    items: list[dict], photos_by_stock: dict[str, list[str]],
    vehicles: list[dict],
) -> tuple[int, int]:
    """并入 vehicles.json。返回 (新增数, 更新数)"""
    by_stock = {str(v.get("stock_id", "")).upper(): v for v in vehicles}
    added = updated = 0
    for item in items:
        row = item["row"]
        photos = photos_by_stock[item["stock_id"]]
        base = {
            "stock_id": item["stock_id"],
            "title": str(row["title"]).strip(),
            "brand": str(row["brand"]).strip(),
            "model": str(row.get("model", "")).strip() or str(row["title"]).strip(),
            "year": item["year"],
            "mileage": f"{item['km'] // 10000}万公里" if item["km"] >= 10000 else f"{item['km']}公里",
            "mileage_km": item["km"],
            "fuel": norm_fuel(str(row["fuel"])),
            "transmission": norm_trans(str(row.get("transmission", "") or "自动")),
            "price": parse_price_usd(row["price_usd"]),
            "price_usd": int(re.sub(r"[^\d]", "", str(row["price_usd"])) or 0),
            "body_type": str(row.get("body_type", "")).strip(),
            "color": str(row.get("color", "")).strip(),
            "drive": str(row.get("drive", "")).strip(),
            "engine": str(row.get("engine", "")).strip(),
            "seats": str(row.get("seats", "")).strip(),
            "emission": str(row.get("emission", "")).strip(),
            "departure_port": str(row.get("departure_port", "") or "上海港").strip(),
            "trade_term": str(row.get("trade_term", "") or "FOB").strip(),
            "vin_last6": item["vin"],
            "registration_date": str(row.get("registration_date", "")).strip(),
            "production_date": str(row.get("production_date", "")).strip(),
            "status": str(row.get("status", "") or "published").strip(),
            "photos": photos,
            "photo_status": "complete" if len(photos) >= 6 else "limited",
            "photo_source_reference": str(row.get("source", "")).strip(),
            "photo_rights": "dealer-provided" if not row.get("source") else str(row["source"]).strip(),
        }
        existing = by_stock.get(item["stock_id"])
        if existing and not existing.get("_placeholder"):
            existing.update(base)
            updated += 1
        else:
            base["id"] = next_vehicle_id(vehicles)
            vehicles.append(base)
            by_stock[item["stock_id"]] = base
            added += 1
    return added, updated


def rebuild_image_index(vehicles: list[dict]) -> None:
    index = {}
    for v in vehicles:
        existing = [p for p in v.get("photos", []) if (ROOT / str(p).lstrip("/")).is_file()]
        index[str(v["id"])] = existing
    IMAGES_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="车辆数据+图片规范化导入")
    ap.add_argument("--batch", required=True, help="批次目录，如 imports/2026-09-batch1")
    ap.add_argument("--dry-run", action="store_true", help="只校验不写入")
    args = ap.parse_args()

    batch_dir = ROOT / args.batch
    if not batch_dir.is_dir():
        die(f"批次目录不存在: {batch_dir}")

    log(f"== Jinba 车辆数据管道 == 批次: {args.batch}")
    vehicles = json.loads(DATA.read_text(encoding="utf-8")) if DATA.is_file() else []
    rows = load_batch_csv(batch_dir)
    log(f"[1/4] 读取 {len(rows)} 行 CSV")

    items = validate_batch(batch_dir, rows, vehicles)
    log(f"[2/4] 校验通过: {len(items)} 台车 × {PHOTO_MIN}-{PHOTO_MAX} 张图，无重复")

    if args.dry_run:
        log("[dry-run] 校验完成，未写入任何文件")
        return

    id_by_stock = {
        str(v.get("stock_id", "")).upper(): int(v["id"]) for v in vehicles
    }
    # 为批次内新车预分配 id：登记映射 + 落盘占位（merge_records 用完整数据覆盖占位）
    for item in items:
        if item["stock_id"] not in id_by_stock:
            id_by_stock[item["stock_id"]] = next_vehicle_id(vehicles)
            vehicles.append({"id": id_by_stock[item["stock_id"]], "stock_id": item["stock_id"], "_placeholder": True})

    log("[3/4] 规范化图片（≤1600px JPEG q82）")
    photos_by_stock = import_photos(items, id_by_stock)

    log("[4/4] 合并数据")
    added, updated = merge_records(items, photos_by_stock, vehicles)
    # 防御性清理：任何未被 merge_records 覆盖的占位记录不应留在数据库
    vehicles[:] = [v for v in vehicles if not v.get("_placeholder")]
    DATA.write_text(json.dumps(vehicles, ensure_ascii=False, indent=2) + "\n")
    rebuild_image_index(vehicles)

    log(f"\n完成: 新增 {added} 台 / 更新 {updated} 台，图片索引已重建")
    log("下一步: python scripts/build_v2.py 重建站点页面")


if __name__ == "__main__":
    main()
