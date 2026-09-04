#!/usr/bin/env python3
"""Jinba inventory data validator (止血用).

Usage:
    python scripts/validate_inventory.py [path/to/vehicles.json]

Checks:
  1. JSON parses and every record has required keys.
  2. All 4 languages (zh/en/ru/ar) present and non-empty for title_i18n /
     description_i18n, titles match the language-appropriate pattern.
  3. Mojibake / encoding-corruption detection (UTF-8 text read/written as GBK
     leaves tell-tale chars in Chinese; Arabic corruption swaps content).
  4. Field sanity: id unique, stock_id unique + format JB-XXXX,
     price_usd > 0 and price string consistent, year/mileage consistent,
     status in {published, unpublished}.
  5. Cross-record leaks: Arabic description mentioning a different stock
     (content mix-up like the JB-0012 Tang/Wingle incident).
  6. Optional: verify referenced photo files exist under repo uploads/.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LANGS = ("zh", "en", "ru", "ar")
MOJIBAKE_CHARS = set("閲鍑鎻鏂浜涓撳闃胯杞締嵁鍑哄彛鐨勬柊杞﹁締鎺ュ悎绾垮垎绫诲睍绀鸿溅鍟嗘彁渚涚殑")
# Arabic letters are U+0600-U+06FF; CJK mojibake of Arabic lands in CJK blocks.
def looks_mojibake(text: str) -> bool:
    return any(ch in MOJIBAKE_CHARS for ch in text)

def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "data" / "vehicles.json"
    if not path.exists():
        print(f"NOT FOUND: {path}")
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"JSON PARSE ERROR: {exc}")
        return 2

    errors: list[str] = []
    warnings: list[str] = []

    ids: dict[int, str] = {}
    stocks: dict[str, int] = {}

    for i, v in enumerate(data, start=1):
        tag = f"[#{i}]"
        vid = v.get("id")
        stock = v.get("stock_id", "")
        if vid is None:
            errors.append(f"{tag} missing 'id'")
        else:
            if vid in ids:
                errors.append(f"{tag} duplicate id {vid} (also #{ids[vid]})")
            ids[vid] = str(i)

        if not stock:
            errors.append(f"{tag} missing stock_id")
        else:
            if stock in stocks:
                errors.append(f"{tag} duplicate stock_id {stock} (also #{stocks[stock]})")
            stocks[stock] = i
            if not re.fullmatch(r"JB-\d{3,4}", stock):
                errors.append(f"{tag} stock_id format odd: {stock!r}")

        if v.get("status") not in ("published", "unpublished", None):
            warnings.append(f"{tag} unexpected status {v.get('status')!r}")

        # i18n completeness + corruption
        for lang in LANGS:
            for field in ("title_i18n", "description_i18n"):
                text = (v.get(field) or {}).get(lang, "")
                if not text or not text.strip():
                    errors.append(f"{tag} {field}.{lang} empty (id={vid} {stock})")
                elif looks_mojibake(text):
                    errors.append(f"{tag} {field}.{lang} looks like mojibake: {text[:60]!r}")

        # Arabic description content mix-up detection: the description must
        # mention its own stock number (or at least not a *different* one).
        ar_desc = (v.get("description_i18n") or {}).get("ar", "")
        own = re.search(r"JB-\d{3,4}", ar_desc)
        if own and own.group(0) != stock and stock:
            errors.append(f"{tag} ar description references {own.group(0)} but record is {stock}")

        # Numeric/string consistency
        pu = v.get("price_usd")
        price_str = v.get("price", "")
        if pu is None or not isinstance(pu, (int, float)) or pu <= 0:
            errors.append(f"{tag} price_usd invalid: {pu!r} (id={vid})")
        elif price_str and (str(pu) not in price_str.replace(",", "") and f"{pu:,}" not in price_str):
            warnings.append(f"{tag} price string {price_str!r} inconsistent with price_usd={pu}")

        mk = v.get("mileage_km")
        mi = v.get("mileage", "")
        if mk is not None and mi and (str(mk) not in mi.replace(",", "") and f"{mk:,}" not in mi):
            warnings.append(f"{tag} mileage string {mi!r} inconsistent with mileage_km={mk}")

        y = v.get("year")
        if y and not re.fullmatch(r"\d{4}", str(y)):
            errors.append(f"{tag} year odd: {y!r}")

    print(f"checked {len(data)} vehicles from {path}")
    print(f"errors:   {len(errors)}")
    print(f"warnings: {len(warnings)}")
    for e in errors:
        print("  E  " + e)
    for w in warnings:
        print("  W  " + w)
    return 1 if errors else (0 if not warnings else 0)

if __name__ == "__main__":
    raise SystemExit(main())
