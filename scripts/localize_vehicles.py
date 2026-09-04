#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""止血：为 161–270 批次中 50 台「品牌/标题仍为中文」的已发布车辆做
品牌归位与 en/ru/ar 标题本地化，并同步其 description_i18n。

规则：
  * brand 归位为真实拉丁品牌（数据里的 brand 存成了中文车名/车型词）。
  * 每台车提供 token 替换：把标题开头的中文 token 换成拉丁市场名。
  * en 标题可整体覆盖；ru/ar 默认 = 原标题替换 token（保留原有本地化后缀词）。
  * description_i18n(en/ru/ar)：把描述里出现的旧标题替换成新标题；
    若描述不含旧标题（模板重建兜底），按站点既有文案模板重建。

只写 data/vehicles.json，不碰已生成页面（随后由 build_v2.py 全量重建）。
运行：python scripts/localize_vehicles.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "vehicles.json"

# id -> (latin_brand, token_to_replace, en_override_or_None)
# token 是标题开头的中文字段（= 原 brand 值）；en_override=None 时 en 标题 = 原标题替换 token。
FIX = {
    216: ("Qiantu", "前途", None),
    217: ("IM", "智己", None),
    218: ("Toyota", "雷凌", None),
    219: ("Zeekr", "极氪", None),
    220: ("Geely", "星越L", "Geely Monjaro 2024 2.0TD Automatic 2WD Edition"),
    221: ("Geely", "缤越", "Geely Coolray L 1.5TD DCT"),
    222: ("Cadillac", "凯迪拉克", None),
    223: ("Toyota", "普拉多", "Toyota Land Cruiser Prado 2026 2.4T TX Edition 5-seat"),
    224: ("Wuling", "五菱", "Wuling Sunshine 2015 1.2L LSI"),
    225: ("Volkswagen", "途观", None),
    226: ("Wuling", "五菱", "Wuling Bingo 2024 333km"),
    228: ("Hyundai", "领动", "Hyundai Elantra 1.6L Automatic 15th Anniversary"),
    229: ("BYD", "海豹05", "BYD Seal 05 DM-i Smart Driving 120KM Flagship"),
    230: ("Hyundai", "胜达", None),
    231: ("Volkswagen", "朗逸", None),
    232: ("Volkswagen", "途观", None),
    233: ("Volvo", "沃尔沃", None),
    234: ("Audi", "奥迪", None),
    235: ("Peugeot", "标致", None),
    236: ("BMW", "宝马", "BMW 3 Series 330Li M Sport"),
    237: ("Toyota", "奕泽IZOA", "Toyota C-HR 2018 2.0L Edition V"),
    238: ("Mazda", "马自达", None),
    239: ("Chevrolet", "迈锐宝XL", None),
    240: ("Subaru", "力狮", None),
    241: ("BYD", "秦L", None),
    242: ("GAC", "传祺", None),
    244: ("Baojun", "宝骏", None),
    245: ("Chevrolet", "科鲁兹", None),
    246: ("Mazda", "马自达", None),
    247: ("Hyundai", "瑞奕", None),
    249: ("Chevrolet", "科鲁兹", None),
    250: ("Audi", "奥迪", None),
    251: ("Great Wall", "长城", None),
    252: ("Geely", "帝豪GS", None),
    253: ("BYD", "海豚", None),
    254: ("Ford", "翼搏", None),
    255: ("Baojun", "宝骏", None),
    256: ("Wuling", "宏光MINIEV", None),
    257: ("Haval", "哈弗", None),
    258: ("Hongqi", "红旗", None),
    259: ("Geely", "帝豪", None),
    260: ("Wuling", "五菱", "Wuling Rongguang V 2018 1.5L"),
    261: ("Buick", "昂科威Plus", None),
    262: ("Wuling", "宏光MINIEV", None),
    265: ("BYD", "元PLUS", None),
    266: ("Buick", "英朗", None),
    267: ("BMW", "宝马", "BMW X5 xDrive 40Li M Sport"),
    268: ("Volvo", "沃尔沃", None),
    269: ("Buick", "威朗", "Buick Verano Pro 533T Edition"),
    270: ("Volkswagen", "迈腾", None),
}


def fmt_km(km):
    return f"{int(km):,}"


def rebuild_desc(lang, v, new_title):
    km = v.get("mileage_km")
    stock = v.get("stock_id", "")
    year = v.get("year", "")
    if lang == "en":
        return (f"Stock {stock}: {year} {new_title} with {fmt_km(km)} km indicated "
                "mileage. Confirm availability, condition and export quotation before payment.")
    if lang == "ru":
        return (f"Автомобиль {stock}: {new_title}, {year} год, заявленный пробег "
                f"{fmt_km(km)} км. Наличие, состояние и экспортная цена подтверждаются до оплаты.")
    # ar
    return (f"المخزون {stock}: {new_title} موديل {year}، والعداد المعروض "
            f"{fmt_km(km)} كم. يجب تأكيد التوفر والحالة وعرض التصدير قبل الدفع.")


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    by_id = {int(v["id"]): v for v in data}
    applied = []
    for vid, (brand, token, en_override) in sorted(FIX.items()):
        v = by_id.get(vid)
        if v is None:
            print(f"!! id {vid} 不存在"); continue
        old = {lang: v.get("title_i18n", {}).get(lang, "") for lang in ("zh", "en", "ru", "ar")}
        if not old["en"].startswith(token):
            print(f"!! id {vid} en 标题未以 token 开头: {old['en']!r}"); continue

        new_titles = {}
        repl = _market_token(vid, token, brand)
        for lang in ("en", "ru", "ar"):
            t = old[lang]
            if not t:
                continue
            new_titles[lang] = t.replace(token, repl, 1)
        if en_override:
            new_titles["en"] = en_override
        # 更新描述：替换旧标题；找不到则模板重建
        for lang in ("en", "ru", "ar"):
            desc = v.get("description_i18n", {}).get(lang, "")
            nt = new_titles.get(lang) or new_titles["en"]
            if old[lang] and old[lang] in desc:
                desc = desc.replace(old[lang], nt)
            elif desc and old["zh"] and old["zh"] in desc:
                desc = desc.replace(old["zh"], nt)
            else:
                desc = rebuild_desc(lang, v, nt)
            v.setdefault("description_i18n", {})[lang] = desc
        v["title_i18n"].update(new_titles)
        v["brand"] = brand
        applied.append(vid)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {len(applied)} vehicles: {applied}")


def _market_token(vid, token, brand):
    # 品牌即市场名的直接返回品牌；否则“品牌 + 空格 + 车型”已经存在于标题尾部。
    # 这里按 token 语义给出品牌词即可；标题尾部保留原拉丁型号。
    return {
        218: "Toyota Levin", 231: "Volkswagen Lavida", 240: "Subaru Legacy",
        247: "Hyundai Reina", 254: "Ford EcoSport", 253: "BYD Dolphin",
        241: "BYD Qin L", 265: "BYD Yuan PLUS", 229: "BYD Seal 05",
        237: "Toyota C-HR", 228: "Hyundai Elantra", 230: "Hyundai Santa Fe",
        223: "Toyota Land Cruiser Prado", 224: "Wuling Sunshine",
        260: "Wuling Rongguang V", 226: "Wuling Bingo", 256: "Wuling Hongguang MINIEV",
        262: "Wuling Hongguang MINIEV", 269: "Buick Verano Pro", 261: "Buick Envision Plus",
        266: "Buick Excelle GT", 259: "Geely Emgrand", 252: "Geely Emgrand GS",
        221: "Geely Coolray", 220: "Geely Monjaro", 251: "Great Wall",
        257: "Haval", 258: "Hongqi", 235: "Peugeot", 239: "Chevrolet Malibu XL",
        245: "Chevrolet Cruze", 249: "Chevrolet Cruze", 242: "GAC",
        270: "Volkswagen Magotan", 222: "Cadillac", 236: "BMW", 267: "BMW",
    }.get(vid, brand)


if __name__ == "__main__":
    main()
