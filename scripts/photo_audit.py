"""Audit vehicle photo coverage without downloading or inventing images."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import date
from pathlib import Path


def build_photo_audit(root: Path, vehicles: list[dict]) -> dict:
    published = [v for v in vehicles if v.get("status") == "published"]
    primary_hashes: dict[str, list[int]] = defaultdict(list)
    rows = []

    for vehicle in published:
        photos = vehicle.get("photos") or []
        existing = []
        for photo in photos:
            path = root / str(photo).lstrip("/")
            if path.is_file():
                existing.append(photo)
        if existing:
            primary = root / str(existing[0]).lstrip("/")
            digest = hashlib.sha256(primary.read_bytes()).hexdigest()
            primary_hashes[digest].append(int(vehicle["id"]))
        rows.append(
            {
                "id": int(vehicle["id"]),
                "stock_id": vehicle.get("stock_id", ""),
                "title": vehicle.get("title", ""),
                "photo_count": len(existing),
                "missing_to_6": max(0, 6 - len(existing)),
                "missing_to_9": max(0, 9 - len(existing)),
                "complete": len(existing) >= 6,
                "primary": existing[0] if existing else "",
                "duplicate_primary_with": [],
            }
        )

    duplicate_groups = [ids for ids in primary_hashes.values() if len(ids) > 1]
    duplicate_map = {
        vehicle_id: sorted(other for other in ids if other != vehicle_id)
        for ids in duplicate_groups
        for vehicle_id in ids
    }
    for row in rows:
        row["duplicate_primary_with"] = duplicate_map.get(row["id"], [])

    complete = sum(row["complete"] for row in rows)
    return {
        "generated_on": date.today().isoformat(),
        "summary": {
            "published_vehicles": len(rows),
            "complete_vehicles": complete,
            "incomplete_vehicles": len(rows) - complete,
            "available_photos": sum(row["photo_count"] for row in rows),
            "missing_to_6": sum(row["missing_to_6"] for row in rows),
            "missing_to_9": sum(row["missing_to_9"] for row in rows),
            "duplicate_primary_groups": len(duplicate_groups),
        },
        "duplicate_primary_groups": sorted(duplicate_groups, key=lambda ids: ids[0]),
        "vehicles": sorted(rows, key=lambda row: (row["complete"], row["photo_count"], row["id"])),
    }

