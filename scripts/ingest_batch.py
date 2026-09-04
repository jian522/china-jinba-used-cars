#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一站式批量入库 / 更新 / 替换工具（沙箱可测，--commit 才写真实文件）。

数据约定（与 data/import-template.csv 一致）：
  stock_id,title,brand,model,year,mileage_km,price_usd,fuel,transmission,
  body_type,color,drive,engine,seats,emission,departure_port,trade_term,
  vin_last6,registration_date,production_date,status,source
可选附加列：title_en / title_ru / title_ar / action(add|update|unpublish|replace)

图片约定：imports/<批次>/<stock_id>/*.(jpg|jpeg|png|webp)
  6–9 张；顺序 = 文件名排序（可加 01_/02_ 前缀控制，primary 字样优先排第一）；
  主图应为前脸或左前 45° 外观。图片将转 WebP(≤1600,q86) 存入 uploads/cars/<id>/。

行为：
  * action=unpublish / CSV status=unpublished → 仅下架对应 stock（无需图片）
  * stock_id 已存在 → 更新该车（替换照片与字段）
  * 全新 stock → 新增（id 取当前最大 +1）
  * replace：CSV 里列出要下架的旧 stock（action=unpublish）即“替换老车型”
  * 发布条件：图片≥6 张 且 四语标题齐（否则自动置 unpublished=待补待译）

用法：
  python scripts/ingest_batch.py --batch <名称> --csv <文件>            # 预演(默认)
  python scripts/ingest_batch.py --batch <名称> --csv <文件> --commit   # 写 vehicles.json + 照片
  # 入库后上线：python scripts/make_thumbs.py && python scripts/build_v2.py
  #            && python scripts/validate_inventory.py && push_api …
  # 测试沙箱：--data <副本vehicles.json> --uploads-root <沙箱目录>
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
EXTS = (".jpg", ".jpeg", ".png", ".webp")

BRAND_MAP = {
    "比亚迪": "BYD", "大众": "Volkswagen", "丰田": "Toyota", "本田": "Honda",
    "日产": "Nissan", "现代": "Hyundai", "起亚": "Kia", "吉利": "Geely",
    "哈弗": "Haval", "奇瑞": "Chery", "长安": "Changan", "荣威": "Roewe",
    "名爵": "MG", "五菱": "Wuling", "宝骏": "Baojun", "广汽传祺": "GAC",
    "传祺": "GAC", "红旗": "Hongqi", "长城": "Great Wall", "宝马": "BMW",
    "奥迪": "Audi", "奔驰": "Mercedes-Benz", "标致": "Peugeot", "雪佛兰": "Chevrolet",
    "别克": "Buick", "福特": "Ford", "马自达": "Mazda", "沃尔沃": "Volvo",
    "捷途": "Jetour", "坦克": "Tank", "极氪": "Zeekr", "凯迪拉克": "Cadillac",
    "斯柯达": "Skoda", "英菲尼迪": "Infiniti", "讴歌": "Acura", "雷克萨斯": "Lexus",
    "东风": "Dongfeng", "江淮": "JAC", "江铃": "JMC", "广汽埃安": "Aion",
    "埃安": "Aion", "小鹏": "XPeng", "蔚来": "NIO", "理想": "Li Auto",
    "零跑": "Leapmotor", "哪吒": "Neta", "智己": "IM", "深蓝": "Deepal",
    "阿维塔": "Avatr", "岚图": "Voyah", "欧拉": "Ora", "腾势": "Denza",
    "方程豹": "Fangchengbao", "仰望": "Yangwang", "星途": "EXEED", "奇瑞捷途": "Jetour",
}
FUEL_CN = {"汽油": "Petrol", "燃油": "Petrol", "纯电": "纯电", "插电混动": "插混",
           "插混": "插混", "混动": "混动", "柴油": "柴油", "油电混合": "混动"}
TRANS_CN = {"自动": "自动", "手动": "手动", "AT": "自动", "CVT": "自动",
            "DCT": "自动", "双离合": "自动"}


def to_int(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace("$", "").replace("元", "").replace(" ", "")
    if not s or s.lower() in {"-", "none", "nan"}:
        return None
    if "万" in s:  # 2.3万 -> 23000
        return int(float(s.replace("万", "")) * 10000)
    try:
        return int(float(s))
    except ValueError:
        return None


def norm(v, d=None):
    if v is None:
        return d if d is not None else ""
    s = str(v).strip()
    return d if (s in {"", "-", "_", "None", "no response", "No response"}) else s


def load_vehicles(data_path: Path) -> list[dict]:
    if data_path.exists():
        return json.loads(data_path.read_text(encoding="utf-8"))
    return []


def md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def photo_files(folder: Path):
    files = [p for p in folder.iterdir() if p.suffix.lower() in EXTS]
    files.sort(key=lambda p: (0, p.name) if p.stem.lower().startswith("primary")
               or re.match(r"^\d", p.name) else (1, p.name))
    return files


def desc_template(lang, stock, year, title, km):
    k = f"{int(km):,}" if km else "?"
    if lang == "zh":
        return (f"库存编号{stock}，{year}年{title}，表显里程{k}公里。"
                "库存、车况和出口报价请在付款前确认。")
    if lang == "en":
        return (f"Stock {stock}: {year} {title} with {k} km indicated mileage. "
                "Confirm availability, condition and export quotation before payment.")
    if lang == "ru":
        return (f"Автомобиль {stock}: {title}, {year} год, заявленный пробег {k} км. "
                "Наличие, состояние и экспортная цена подтверждаются до оплаты.")
    return (f"المخزون {stock}: {title} موديل {year}، والعداد المعروض {k} كم. "
            "يجب تأكيد التوفر والحالة وعرض التصدير قبل الدفع.")


def transcode(src: Path, target: Path, max_side=1600, quality=86) -> None:
    img = Image.open(src)
    img.load()
    img = ImageOps.exif_transpose(img).convert("RGB")
    if max(img.size) > max_side:
        scale = max_side / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    img.save(target, "WEBP", quality=quality, method=6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, help="批次目录名（默认 imports/<batch>）")
    ap.add_argument("--batch-root", default=str(ROOT / "imports"),
                    help="批次根目录（沙箱测试时指向别处）")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--data", default=str(ROOT / "data" / "vehicles.json"))
    ap.add_argument("--uploads-root", default=str(ROOT / "uploads"))
    ap.add_argument("--min-photos", type=int, default=6)
    ap.add_argument("--commit", action="store_true", help="真正写入；缺省为预演")
    ap.add_argument("--unpublish", help="可选：列出要下架的旧 stock_id（每行一个，配合替换）")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    batch_dir = Path(args.batch_root) / args.batch
    data_path = Path(args.data)
    uploads_root = Path(args.uploads_root)
    vehicles = load_vehicles(data_path)
    by_stock = {v.get("stock_id"): v for v in vehicles}

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    if args.unpublish:
        for line in Path(args.unpublish).read_text(encoding="utf-8").splitlines():
            stock = line.strip()
            if stock in by_stock:
                by_stock[stock]["status"] = "unpublished"
                print(f"[下架] {stock}")

    next_id = max((int(v["id"]) for v in vehicles), default=0) + 1
    preview: list[str] = []
    for r in rows:
        stock = norm(r.get("stock_id"))
        if not stock:
            print("!! 缺少 stock_id，跳过"); continue
        action = norm(r.get("action"), "add")
        status = norm(r.get("status"), "published")
        if action == "unpublish" or status == "unpublished":
            if stock in by_stock:
                if args.commit:
                    by_stock[stock]["status"] = "unpublished"
                preview.append(f"[{action or '下架'}] {stock}")
            continue
        folder = batch_dir / stock
        photos = photo_files(folder) if folder.is_dir() else []
        if len(photos) < args.min_photos:
            print(f"!! {stock} 图片仅 {len(photos)} 张(<{args.min_photos})：将保持未发布")
            status = "unpublished"
        seen = set(); dups = []
        for p in photos:
            m = md5(p)
            if m in seen:
                dups.append(p.name)
            seen.add(m)
        brand = norm(r.get("brand"))
        brand = BRAND_MAP.get(brand, brand)
        km = to_int(r.get("mileage_km"))
        price = to_int(r.get("price_usd"))
        title = norm(r.get("title"))
        title_en = norm(r.get("title_en")); title_ru = norm(r.get("title_ru")); title_ar = norm(r.get("title_ar"))
        if not (title_en and title_ru and title_ar) and re.search(r"[\u4e00-\u9fff]", title):
            print(f"!! {stock} 缺少 title_en/ru/ar：将保持未发布（待翻译）")
            status = "unpublished"
        v = by_stock.get(stock)
        vid = v["id"] if v else next_id
        fuel = norm(r.get("fuel")); fuel = FUEL_CN.get(fuel, fuel)
        trans = norm(r.get("transmission")); trans = TRANS_CN.get(trans, trans)
        record = {
            "id": vid, "stock_id": stock, "status": status, "title": title,
            "price": f"${price:,}" if price else "$0",
            "price_usd": price, "year": norm(r.get("year")),
            "mileage": f"{km} km" if km else "", "mileage_km": km,
            "fuel": fuel, "transmission": trans, "brand": brand,
            "model": norm(r.get("model")),
            "body_type": norm(r.get("body_type")), "color": norm(r.get("color")),
            "drive": norm(r.get("drive")), "engine": norm(r.get("engine")),
            "seats": to_int(r.get("seats")), "emission": norm(r.get("emission")),
            "departure_port": norm(r.get("departure_port")), "trade_term": norm(r.get("trade_term"), "FOB"),
            "vin_last6": norm(r.get("vin_last6")),
            "registration_date": norm(r.get("registration_date")),
            "production_date": norm(r.get("production_date")),
            "source": norm(r.get("source")),
            "photos": [],
        }
        titles = {"zh": title,
                  "en": title_en or (title if not re.search(r"[\u4e00-\u9fff]", title) else ""),
                  "ru": title_ru or (title if not re.search(r"[\u4e00-\u9fff]", title) else ""),
                  "ar": title_ar or (title if not re.search(r"[\u4e00-\u9fff]", title) else "")}
        record["title_i18n"] = {k: (t or "") for k, t in titles.items()}
        if title_en and title_ru and title_ar and title:
            y = norm(r.get("year"), "?")
            record["description_i18n"] = {
                k: desc_template(k, stock, y, titles[k], km) for k in ("zh", "en", "ru", "ar")}
        verb = "更新" if v else "新增"
        detail = f"[{verb}] {stock} {brand} {title} (id={vid}, 图{len(photos)},{'已发布' if status=='published' else '未发布'}"
        if dups:
            detail += f", 重复:{','.join(dups)}"
        detail += ")"
        preview.append(detail)
        if args.commit and photos:
            car_dir = uploads_root / "cars" / str(vid)
            shutil.rmtree(car_dir, ignore_errors=True)
            car_dir.mkdir(parents=True, exist_ok=True)
            for i, p in enumerate(photos, start=1):
                name = "primary.webp" if i == 1 else f"photo-{i:02d}.webp"
                transcode(p, car_dir / name)
                record["photos"].append(f"/uploads/cars/{vid}/{name}")
        if args.commit:
            if v:
                v.update({k2: val for k2, val in record.items() if k2 != "id"})
            else:
                record["id"] = next_id
                vehicles.append(record)
                next_id += 1
    print("===== 计划 =====")
    print("\n".join(preview) if preview else "(空)")
    if args.commit:
        out = json.dumps(vehicles, ensure_ascii=False, indent=2) + "\n"
        data_path.write_text(out, encoding="utf-8")
        print(f"===== 已写入 {data_path}（车辆总数 {len(vehicles)}）=====")
        print("下一步: python scripts/make_thumbs.py && python scripts/build_v2.py "
              "&& python scripts/validate_inventory.py")
    else:
        print("===== 预演模式（加 --commit 生效）=====")


if __name__ == "__main__":
    main()
