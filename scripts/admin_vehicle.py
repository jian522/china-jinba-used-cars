#!/usr/bin/env python3
"""Process owner-only GitHub Issue Form submissions into vehicle inventory.

The workflow that calls this script must restrict execution to the repository
owner. User-provided values are parsed as data only and are never executed.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import json
import os
import re
import shutil
import sys

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vehicles.json"
EVENT_PATH = Path(os.environ.get("GITHUB_EVENT_PATH", ""))
ALLOWED_IMAGE_HOSTS = {"github.com", "user-images.githubusercontent.com"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def clean(value: str) -> str:
    value = value.strip()
    return "" if value in {"_No response_", "No response"} else value


def sections(body: str) -> dict[str, str]:
    parts = re.split(r"^###\s+(.+?)\s*$", body or "", flags=re.M)
    return {parts[i].strip(): clean(parts[i + 1]) for i in range(1, len(parts), 2)}


def number(value: str, field: str, minimum: int = 0, maximum: int = 10**9) -> int:
    digits = re.sub(r"[^0-9]", "", value)
    if not digits:
        fail(f"{field} must contain a number")
    result = int(digits)
    if not minimum <= result <= maximum:
        fail(f"{field} must be between {minimum} and {maximum}")
    return result


def image_urls(text: str) -> list[str]:
    urls = re.findall(r"https://[^\s)>]+", text or "")
    return [u.rstrip(".,") for u in urls if "user-attachments/assets" in u or "user-images.githubusercontent.com" in u]


def allowed_host(host: str) -> bool:
    host = (host or "").lower()
    return host in ALLOWED_IMAGE_HOSTS or host.endswith(".githubusercontent.com")


def download_image(url: str) -> Image.Image:
    if not allowed_host(urlparse(url).hostname or ""):
        fail("Photos must be uploaded directly to the GitHub issue")
    request = Request(url, headers={"User-Agent": "Jinba-Inventory-Bot/1.0"})
    with urlopen(request, timeout=45) as response:
        final_host = urlparse(response.geturl()).hostname or ""
        if not allowed_host(final_host):
            fail("An uploaded photo redirected to an unsupported host")
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
        if content_type not in {"image/jpeg", "image/png", "image/webp"}:
            fail(f"Unsupported image type: {content_type or 'unknown'}")
        raw = response.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        fail("Each photo must be smaller than 15 MB")
    try:
        image = Image.open(BytesIO(raw))
        image.load()
        image = ImageOps.exif_transpose(image).convert("RGB")
    except Exception as exc:
        fail(f"A photo could not be decoded: {exc}")
    if image.width < 800 or image.height < 600:
        fail("Each photo must be at least 800 × 600 pixels")
    return image


def save_photos(vehicle_id: int, urls: list[str], primary_number: int) -> list[str]:
    if not 6 <= len(urls) <= 9:
        fail("A published vehicle requires 6 to 9 original photos")
    if not 1 <= primary_number <= len(urls):
        fail("Primary photo number is outside the uploaded photo range")
    ordered = urls[:]
    ordered.insert(0, ordered.pop(primary_number - 1))
    target = ROOT / "uploads" / "cars" / str(vehicle_id)
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    result = []
    for index, url in enumerate(ordered):
        image = download_image(url)
        image.thumbnail((1600, 1200), Image.Resampling.LANCZOS)
        filename = "primary.webp" if index == 0 else f"photo-{index + 1:02d}.webp"
        image.save(target / filename, "WEBP", quality=86, method=6)
        result.append(f"/uploads/cars/{vehicle_id}/{filename}")
    return result


def field(form: dict[str, str], name: str, required: bool = False) -> str:
    value = form.get(name, "")
    if required and not value:
        fail(f"Missing required field: {name}")
    return value


def normalize_fuel(value: str) -> str:
    return {"EV": "纯电", "PHEV": "插混", "Hybrid": "混动", "Diesel": "柴油", "Petrol": "Petrol"}.get(value, value)


def normalize_transmission(value: str) -> str:
    return {"Automatic": "自动", "Manual": "手动"}.get(value, value)


def export_fields(form: dict[str, str]) -> dict[str, object]:
    mapping = {
        "Body type": "body_type", "Engine / motor": "engine", "Drive type": "drive",
        "Exterior color": "color", "Production date": "production_date",
        "First registration": "registration_date", "VIN last 6 characters": "vin_last6",
        "Emission standard": "emission", "Departure port": "departure_port",
        "Trade term": "trade_term", "Chinese description": "description_zh",
        "English title (optional)": "title_en", "Russian title (optional)": "title_ru",
        "Arabic title (optional)": "title_ar",
    }
    out: dict[str, object] = {}
    for source, target in mapping.items():
        if form.get(source) and form[source] != "No change":
            out[target] = form[source]
    if form.get("Seats"):
        out["seats"] = number(form["Seats"], "Seats", 1, 60)
    return out


def add_vehicle(vehicles: list[dict], form: dict[str, str]) -> tuple[int, str]:
    vehicle_id = max((int(v["id"]) for v in vehicles), default=0) + 1
    title = field(form, "Chinese vehicle title", True)
    price = number(field(form, "Price in USD", True), "Price in USD", 1, 2_000_000)
    mileage = number(field(form, "Mileage in km", True), "Mileage", 0, 2_000_000)
    year = number(field(form, "Model year", True), "Model year", 1990, 2100)
    urls = image_urls(field(form, "Upload 6–9 original photos", True))
    primary = number(field(form, "Primary photo number", True), "Primary photo number", 1, 9)
    photos = save_photos(vehicle_id, urls, primary)
    brand = field(form, "Brand", True)
    vehicle = {
        "id": vehicle_id,
        "stock_id": f"JB-{vehicle_id:04d}",
        "status": "published",
        "title": title,
        "price": f"${price:,}",
        "price_usd": price,
        "year": str(year),
        "mileage": f"{mileage} km",
        "mileage_km": mileage,
        "fuel": normalize_fuel(field(form, "Fuel type", True)),
        "transmission": normalize_transmission(field(form, "Transmission", True)),
        "brand": brand,
        "model": field(form, "Model / trim", True),
        "photos": photos,
        "photo_status": "complete",
    }
    vehicle.update(export_fields(form))
    vehicles.append(vehicle)
    return vehicle_id, f"Added {vehicle['stock_id']} — {title}"


def find_vehicle(vehicles: list[dict], form: dict[str, str]) -> dict:
    raw = field(form, "Vehicle ID", True)
    vehicle_id = number(raw, "Vehicle ID", 1)
    try:
        return next(v for v in vehicles if int(v["id"]) == vehicle_id)
    except StopIteration:
        fail(f"Vehicle {vehicle_id} does not exist")


def update_vehicle(vehicles: list[dict], form: dict[str, str]) -> tuple[int, str]:
    vehicle = find_vehicle(vehicles, form)
    simple = {
        "Chinese vehicle title": "title", "Brand": "brand", "Model / trim": "model",
        "Model year": "year", "Fuel type": "fuel", "Transmission": "transmission",
    }
    for source, target in simple.items():
        if form.get(source):
            value = form[source]
            if target == "fuel": value = normalize_fuel(value)
            if target == "transmission": value = normalize_transmission(value)
            vehicle[target] = value
    if form.get("Price in USD"):
        price = number(form["Price in USD"], "Price in USD", 1, 2_000_000)
        vehicle.update(price=f"${price:,}", price_usd=price)
    if form.get("Mileage in km"):
        mileage = number(form["Mileage in km"], "Mileage", 0, 2_000_000)
        vehicle.update(mileage=f"{mileage} km", mileage_km=mileage)
    vehicle.update(export_fields(form))
    urls = image_urls(form.get("Replace with 6–9 original photos", ""))
    if urls:
        primary = number(form.get("Primary photo number", "1"), "Primary photo number", 1, 9)
        vehicle["photos"] = save_photos(int(vehicle["id"]), urls, primary)
        vehicle["photo_status"] = "complete"
    return int(vehicle["id"]), f"Updated {vehicle.get('stock_id')} — {vehicle['title']}"


def unpublish_vehicle(vehicles: list[dict], form: dict[str, str]) -> tuple[int, str]:
    vehicle = find_vehicle(vehicles, form)
    vehicle["status"] = "unpublished"
    reason = form.get("Reason", "")
    return int(vehicle["id"]), f"Unpublished {vehicle.get('stock_id')} — {reason or vehicle['title']}"


def main() -> None:
    if not EVENT_PATH.is_file():
        fail("GITHUB_EVENT_PATH is missing")
    event = json.loads(EVENT_PATH.read_text())
    issue = event.get("issue") or {}
    labels = {item.get("name") for item in issue.get("labels", [])}
    form = sections(issue.get("body", ""))
    vehicles = json.loads(DATA.read_text())
    title = issue.get("title", "")
    if "vehicle-add" in labels or title.startswith("[新增车辆]"):
        vehicle_id, summary = add_vehicle(vehicles, form)
    elif "vehicle-update" in labels or title.startswith("[更新车辆]"):
        vehicle_id, summary = update_vehicle(vehicles, form)
    elif "vehicle-unpublish" in labels or title.startswith("[下架车辆]"):
        vehicle_id, summary = unpublish_vehicle(vehicles, form)
    else:
        fail("No supported vehicle administration label was found")
    DATA.write_text(json.dumps(vehicles, ensure_ascii=False, indent=2) + "\n")
    output = Path(os.environ.get("GITHUB_OUTPUT", "/tmp/jinba-admin-output"))
    with output.open("a") as handle:
        handle.write(f"vehicle_id={vehicle_id}\nsummary={summary}\n")
    print(summary)


if __name__ == "__main__":
    main()
