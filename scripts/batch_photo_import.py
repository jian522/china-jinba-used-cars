#!/usr/bin/env python3
"""Import several complete, authorized vehicle photo sets from one owner issue.

Each batch is validated in full before any inventory file is changed. This keeps
the live catalog from receiving partial galleries when one photo set is invalid.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import os
import re
import shutil
import tempfile

from PIL import Image, ImageOps

from admin_vehicle import DATA, EVENT_PATH, ROOT, download_image, fail, image_urls, sections


HEADER = re.compile(
    r"^(JB-\d{4})\s*\|\s*primary=(\d+)\s*\|\s*vin=([^|]+)\s*\|\s*source=(.+?)\s*$",
    re.I | re.M,
)
MAX_VEHICLES_PER_BATCH = 20


def fingerprint(image: Image.Image) -> str:
    """Return a stable pixel fingerprint that survives filename changes."""
    normalized = ImageOps.fit(image.convert("RGB"), (96, 72), Image.Resampling.LANCZOS)
    return sha256(normalized.tobytes()).hexdigest()


def parse_groups(text: str) -> list[dict[str, object]]:
    matches = list(HEADER.finditer(text or ""))
    if not matches:
        fail("No batch groups found. Use the exact JB-0008 | primary=1 | vin=... | source=... format")
    if len(matches) > MAX_VEHICLES_PER_BATCH:
        fail(f"A batch can contain at most {MAX_VEHICLES_PER_BATCH} vehicles")
    groups: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, match in enumerate(matches):
        stock_id = match.group(1).upper()
        if stock_id in seen:
            fail(f"Duplicate vehicle group: {stock_id}")
        seen.add(stock_id)
        primary = int(match.group(2))
        vin = match.group(3).strip()
        source = match.group(4).strip()
        if vin not in {"-", "无", "N/A", "n/a"} and not re.fullmatch(r"[A-Za-z0-9]{6}", vin):
            fail(f"{stock_id}: VIN must be the last 6 letters/numbers, or '-' when unavailable")
        if len(source) < 3:
            fail(f"{stock_id}: source must identify the dealer, supplier stock number, or authorized source")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        urls = image_urls(text[match.end():end])
        if not 6 <= len(urls) <= 9:
            fail(f"{stock_id}: expected 6 to 9 uploaded photos, found {len(urls)}")
        if not 1 <= primary <= len(urls):
            fail(f"{stock_id}: primary photo number is outside the uploaded range")
        groups.append({"stock_id": stock_id, "primary": primary, "vin": vin, "source": source, "urls": urls})
    return groups


def existing_fingerprints(excluded_ids: set[int]) -> dict[str, str]:
    found: dict[str, str] = {}
    uploads = ROOT / "uploads" / "cars"
    if not uploads.exists():
        return found
    for path in uploads.glob("*/*"):
        if not path.is_file():
            continue
        try:
            vehicle_id = int(path.parent.name)
        except ValueError:
            continue
        if vehicle_id in excluded_ids:
            continue
        try:
            with Image.open(path) as image:
                found[fingerprint(ImageOps.exif_transpose(image))] = str(path.relative_to(ROOT))
        except Exception:
            continue
    return found


def main() -> None:
    if not EVENT_PATH.is_file():
        fail("GITHUB_EVENT_PATH is missing")
    event = json.loads(EVENT_PATH.read_text())
    issue = event.get("issue") or {}
    form = sections(issue.get("body", ""))
    rights = form.get("图片授权确认", "")
    if not re.search(r"\[[xX]\]", rights):
        fail("The commercial photo rights confirmation must be checked")
    groups = parse_groups(form.get("Batch photo groups", ""))
    vehicles = json.loads(DATA.read_text())
    by_stock = {str(vehicle.get("stock_id", "")).upper(): vehicle for vehicle in vehicles}
    missing = [str(group["stock_id"]) for group in groups if group["stock_id"] not in by_stock]
    if missing:
        fail("Unknown stock IDs: " + ", ".join(missing))
    unpublished = [str(group["stock_id"]) for group in groups if by_stock[group["stock_id"]].get("status") != "published"]
    if unpublished:
        fail("Unpublished vehicles cannot receive a public gallery: " + ", ".join(unpublished))

    target_ids = {int(by_stock[group["stock_id"]]["id"]) for group in groups}
    known = existing_fingerprints(target_ids)
    batch_seen: dict[str, str] = {}
    photo_total = 0

    with tempfile.TemporaryDirectory(prefix="jinba-photo-batch-") as temp:
        stage_root = Path(temp)
        staged: dict[int, list[str]] = {}
        for group in groups:
            stock_id = str(group["stock_id"])
            vehicle = by_stock[stock_id]
            vehicle_id = int(vehicle["id"])
            urls = list(group["urls"])
            primary = int(group["primary"])
            urls.insert(0, urls.pop(primary - 1))
            stage = stage_root / str(vehicle_id)
            stage.mkdir(parents=True)
            paths: list[str] = []
            for index, url in enumerate(urls):
                image = download_image(url)
                digest = fingerprint(image)
                if digest in known:
                    fail(f"{stock_id}: a photo duplicates existing file {known[digest]}")
                if digest in batch_seen:
                    fail(f"{stock_id}: a photo duplicates one in {batch_seen[digest]}")
                batch_seen[digest] = stock_id
                image.thumbnail((1600, 1200), Image.Resampling.LANCZOS)
                filename = "primary.webp" if index == 0 else f"photo-{index + 1:02d}.webp"
                image.save(stage / filename, "WEBP", quality=86, method=6)
                paths.append(f"/uploads/cars/{vehicle_id}/{filename}")
                photo_total += 1
            staged[vehicle_id] = paths

        for group in groups:
            stock_id = str(group["stock_id"])
            vehicle = by_stock[stock_id]
            vehicle_id = int(vehicle["id"])
            target = ROOT / "uploads" / "cars" / str(vehicle_id)
            shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(stage_root / str(vehicle_id), target)
            vehicle["photos"] = staged[vehicle_id]
            vehicle["photo_status"] = "complete"
            vehicle["photo_source_reference"] = str(group["source"])
            vehicle["photo_rights"] = "confirmed"
            vin = str(group["vin"])
            if vin not in {"-", "无", "N/A", "n/a"}:
                vehicle["vin_last6"] = vin.upper()

    DATA.write_text(json.dumps(vehicles, ensure_ascii=False, indent=2) + "\n")
    summary = f"Batch photos: {len(groups)} vehicles, {photo_total} authorized photos"
    output = Path(os.environ.get("GITHUB_OUTPUT", "/tmp/jinba-admin-output"))
    with output.open("a") as handle:
        handle.write(f"vehicle_id=batch\nsummary={summary}\n")
    print(summary)


if __name__ == "__main__":
    main()
