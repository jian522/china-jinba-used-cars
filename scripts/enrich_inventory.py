#!/usr/bin/env python3
"""Add safe export fields and deterministic multilingual copy to inventory."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vehicles.json"

MODEL_NAMES = {
    "名爵ZS": "ZS", "捷途X70 PLUS": "X70 PLUS", "捷途X70": "X70",
    "捷途旅行者": "Traveller", "捷途大圣": "Dashing", "捷途自由者": "Ziyouzhe",
    "哈弗大狗 PLUS": "Dargo PLUS", "哈弗大狗": "Dargo", "哈弗初恋": "Jolion",
    "哈弗猛龙": "Raptor", "哈弗枭龙MAX": "Xiaolong MAX", "哈弗枭龙": "Xiaolong",
    "哈弗H6": "H6", "哈弗H9": "H9", "哈弗F7": "F7", "哈弗M6": "M6",
    "海狮07": "Sea Lion 07", "海狮05": "Sea Lion 05", "宋PLUS": "Song PLUS",
    "宋Pro": "Song Pro", "秦PLUS": "Qin PLUS", "秦L": "Qin L", "海豹06": "Seal 06",
    "海豹": "Seal", "海鸥": "Seagull", "海豚": "Dolphin", "唐": "Tang",
    "汉": "Han", "元": "Yuan",
    "瑞虎8 PLUS": "Tiggo 8 PLUS", "瑞虎8 PRO": "Tiggo 8 PRO", "瑞虎8L": "Tiggo 8L",
    "瑞虎8": "Tiggo 8", "瑞虎7": "Tiggo 7", "瑞虎3x": "Tiggo 3x",
    "艾瑞泽8 PRO": "Arrizo 8 PRO", "艾瑞泽8": "Arrizo 8", "艾瑞泽5": "Arrizo 5",
    "欧萌达": "Omoda",
    "阿维塔": "Avatr ", "蔚来": "", "小鹏": "", "极氪": "",
    "金刚炮": "King Kong Poer", "风骏7": "Wingle 7", "风骏5": "Wingle 5", "炮": "Poer",
    "荣威RX5新能源": "RX5 eRX5", "荣威RX5": "RX5", "荣威iMAX8": "iMAX8", "荣威i5": "i5",
    "飞凡R7": "Rising Auto R7", "飞凡F7": "Rising Auto F7",
    "缤越": "Coolray", "星越L": "Monjaro", "帝豪": "Emgrand",
    "长安CS75PLUS": "CS75 PLUS", "长安CS55PLUS": "CS55 PLUS", "逸动": "Eado",
    "理想L7": "L7", "问界M7": "M7", "智界S7": "S7", "传祺GS3": "GS3",
}

PHRASES = {
    "新能源": " ", "2026款": "2026 ", "2025款": "2025 ", "2024款": "2024 ",
    "第三代": "3rd Gen", "第二代": "2nd Gen", "第四代": "4th Gen", "第5代": "5th Gen",
    "超长续航": "Extended Range", "长续航": "Long Range", "增程版": "Range-Extended",
    "增程": "Range-Extended", "纯电动": "EV", "纯电版": "EV", "纯电": "EV",
    "智能焕新版": "Smart Upgrade", "智驾版": "Smart Driving", "智航版": "Smart Navigation",
    "旗舰智航版": "Flagship Smart Navigation", "后驱智驾版": "RWD Smart Driving",
    "长续航四驱智驾版": "Long Range AWD Smart Driving", "智能": "Smart",
    "自动": "Automatic", "手动": "Manual", "双电机": "Dual-Motor", "后驱": "RWD",
    "四驱": "4WD", "两驱": "2WD", "柴油": "Diesel", "汽油": "Petrol",
    "七座": "7-seat", "六座": "6-seat", "五座": "5-seat", "12座": "12-seat",
    "7座": "7-seat", "6座": "6-seat", "5座": "5-seat",
    "双排皮卡": "Double-Cab Pickup", "商务车": "Business Van", "大双": "Double-Cab Long Bed",
    "长箱": "Long Bed", "平箱": "Standard Bed", "商用版": "Commercial", "乘用版": "Passenger",
    "公务型": "Business", "冠军版": "Champion Edition", "冠军": "Champion",
    "改款": "Facelift", "旗舰型": "Flagship", "尊贵型": "Premium", "尊贵版": "Premium",
    "尊享型": "Premium", "尊享版": "Premium", "尊荣型": "Premium", "尊荣版": "Premium",
    "豪华智联型": "Luxury Connected", "行政豪华版": "Executive Luxury",
    "行政版": "Executive", "豪华版": "Luxury", "豪享版": "Luxury",
    "精英型": "Elite", "精英版": "Elite", "领先版": "Leading", "卓越版": "Excellence",
    "超越型": "Beyond", "时尚版": "Fashion", "风尚型": "Style", "舒适版": "Comfort",
    "青春豪华版": "Youth Luxury", "青春风尚版": "Youth Style", "进阶版": "Advanced",
    "性能版": "Performance", "签名版": "Signature", "都市版": "Urban",
    "科技版": "Technology", "活力版": "Vitality", "畅行版": "Comfort",
    "领航型": "Navigation", "智享版": "Smart Comfort", "智享型": "Smart Comfort",
    "超感精英版": "Elite", "全景乐享版": "Panoramic Comfort", "夺目版": "Distinctive",
    "领锐版": "Leading", "创酷型": "Cool", "劲享版": "Comfort",
    "探索": "Explore", "发现": "Discovery", "穿越版": "Adventure", "穿越": "Adventure",
    "国潮版": "China Chic", "边牧版": "Border Collie Edition", "中华田园犬版": "Rural Dog Edition",
    "潮野版": "Outdoor Edition", "自动全球百万918版": "Automatic Global 918 Edition",
    "至美优雅版": "Elegant", "至美舒享版": "Comfort", "猎美尊享版": "Premium",
    "领潮风尚版": "Trend Style", "青奢风潮版": "Youth Luxury", "激擎耀世版": "Performance",
    "创酷型": "Cool", "智慧鲸悦版": "Smart Comfort", "东方曜": "Oriental Edition",
    "自动揽星版": "Automatic Premium", "新蓝鲸": "Blue Whale", "超混优越版": "Super Hybrid Premium",
    "超混优��版": "Super Hybrid Premium", "超混优": "Super Hybrid", "高能版": "High Power",
    "激光雷达旗舰型": "LiDAR Flagship", "线激光雷达": "-line LiDAR", "国VI": "China VI",
    "签名": "Signature", "过道版": "Aisle Edition", "全景": "Panoramic", "版": "Edition",
    "款": "", "型": "", "座": "-seat", "第": "", "代": "Gen",
    "尚": "Style", "驰": "Sport", "山": "Mountain", "潮": "Trend",
}


def tidy(text: str) -> str:
    text = text.replace("）", "").replace("（", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;)])", r"\1", text)
    return text.strip(" -")


def english_title(vehicle: dict) -> str:
    if vehicle.get("title_en"):
        return tidy(vehicle["title_en"])
    text = vehicle.get("title", "")
    brand = vehicle.get("brand", "")
    # Remove repeated Chinese/English maker names while preserving the export brand.
    maker_words = [brand, "名爵", "捷途", "哈弗", "荣威", "长安", "传祺", "理想", "问界", "智界"]
    for word in maker_words:
        if word:
            text = re.sub(rf"^\s*{re.escape(word)}\s*", "", text, flags=re.I)
    for source, target in sorted(MODEL_NAMES.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)
    for source, target in sorted(PHRASES.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, f" {target} ")
    # Unmapped trim marketing words are removed rather than mistranslated.
    text = re.sub(r"[\u4e00-\u9fff]+", " ", text)
    text = tidy(text)
    return tidy(f"{brand} {text}")


def localized_title(en: str, lang: str) -> str:
    replacements = {
        "ru": {
            "Automatic": "автомат", "Manual": "механика", "Extended Range": "увеличенный запас хода",
            "Long Range": "большой запас хода", "Range-Extended": "гибрид с увеличенным запасом",
            "Smart Driving": "интеллектуальное вождение", "Luxury": "люкс", "Premium": "премиум",
            "Flagship": "флагман", "Edition": "версия", "Pickup": "пикап", "EV": "электромобиль",
        },
        "ar": {
            "Automatic": "أوتوماتيك", "Manual": "يدوي", "Extended Range": "مدى ممتد",
            "Long Range": "مدى طويل", "Range-Extended": "هجين ممتد المدى",
            "Smart Driving": "قيادة ذكية", "Luxury": "فاخر", "Premium": "بريميوم",
            "Flagship": "رائدة", "Edition": "فئة", "Pickup": "بيك أب", "EV": "كهربائية",
        },
    }
    text = en
    for source, target in sorted(replacements[lang].items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)
    return tidy(text)


def inferred_fields(vehicle: dict) -> None:
    title = vehicle.get("title", "")
    vehicle.setdefault("stock_id", f"JB-{int(vehicle['id']):04d}")
    vehicle.setdefault("status", "published" if int(vehicle["id"]) > 6 else "unpublished")
    vehicle["price_usd"] = int(re.sub(r"\D", "", vehicle.get("price", "")) or 0)
    vehicle["mileage_km"] = int(re.sub(r"\D", "", vehicle.get("mileage", "")) or 0)
    engine = re.search(r"\b\d\.\d[TL]\b", title, re.I)
    vehicle.setdefault("engine", engine.group(0).upper() if engine else "")
    if not vehicle.get("drive"):
        vehicle["drive"] = "4WD" if "四驱" in title else "RWD" if "后驱" in title else "2WD" if "两驱" in title else ""
    seats = re.search(r"(\d{1,2})座", title)
    if seats and not vehicle.get("seats"):
        vehicle["seats"] = int(seats.group(1))
    for key in ("body_type", "color", "production_date", "registration_date", "vin_last6", "emission", "departure_port"):
        vehicle.setdefault(key, "")
    vehicle.setdefault("trade_term", "FOB")
    vehicle["photo_status"] = "complete" if 6 <= len(vehicle.get("photos", [])) <= 10 else "limited"


def descriptions(vehicle: dict, titles: dict[str, str]) -> dict[str, str]:
    stock = vehicle["stock_id"]
    mileage = vehicle["mileage_km"]
    year = vehicle.get("year", "")
    return {
        "zh": f"库存编号{stock}，{year}年{vehicle['title']}，表显里程{mileage:,}公里。库存、车况和出口报价请在付款前确认。",
        "en": f"Stock {stock}: {year} {titles['en']} with {mileage:,} km indicated mileage. Confirm availability, condition and export quotation before payment.",
        "ru": f"Автомобиль {stock}: {titles['ru']}, {year} год, заявленный пробег {mileage:,} км. Наличие, состояние и экспортная цена подтверждаются до оплаты.",
        "ar": f"المخزون {stock}: {titles['ar']} موديل {year}، والعداد المعروض {mileage:,} كم. يجب تأكيد التوفر والحالة وعرض التصدير قبل الدفع.",
    }


def enrich_vehicle(vehicle: dict) -> dict:
    inferred_fields(vehicle)
    en = english_title(vehicle)
    titles = {
        "zh": vehicle.get("title", ""),
        "en": en,
        "ru": tidy(vehicle.get("title_ru") or localized_title(en, "ru")),
        "ar": tidy(vehicle.get("title_ar") or localized_title(en, "ar")),
    }
    vehicle["title_i18n"] = titles
    vehicle["description_i18n"] = descriptions(vehicle, titles)
    return vehicle


def enrich_all(vehicles: list[dict]) -> list[dict]:
    return [enrich_vehicle(vehicle) for vehicle in vehicles]


def main() -> None:
    vehicles = enrich_all(json.loads(DATA.read_text()))
    DATA.write_text(json.dumps(vehicles, ensure_ascii=False, indent=2) + "\n")
    print(f"enriched {len(vehicles)} vehicles")


if __name__ == "__main__":
    main()
