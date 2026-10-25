"""Serializable shopping items, independent of Home Assistant."""

import base64
import binascii
import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Any
from uuid import uuid4

STATUSES = {"needs_action", "completed"}
MAX_ITEM_IMAGE_BYTES = 512 * 1024


def parse_due(value: str | None) -> date | datetime | None:
    """Decode an ISO date or timezone-aware datetime."""
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError("A due datetime must include a timezone") from None
        return result


@dataclass(frozen=True)
class ShoppingItem:
    """A local item with its own identity and optional source reference."""

    uid: str
    summary: str
    status: str = "needs_action"
    description: str | None = None
    due: str | None = None
    source_uid: str | None = None
    metadata: dict[str, str | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.uid, str) or not self.uid:
            raise ValueError("An item must have a nonempty UID")
        if not isinstance(self.summary, str) or not self.summary.strip():
            raise ValueError("An item must have a nonempty summary")
        if not isinstance(self.status, str) or self.status not in STATUSES:
            raise ValueError("Invalid item status")
        for value in (self.description, self.due, self.source_uid):
            if value is not None and not isinstance(value, str):
                raise ValueError("Invalid optional item field")
        parse_due(self.due)
        if not isinstance(self.metadata, dict) or any(
            not isinstance(key, str)
            or not key
            or (value is not None and not isinstance(value, str))
            for key, value in self.metadata.items()
        ):
            raise ValueError("Metadata must contain named text values or null")
        image = self.metadata.get("image")
        if image is not None:
            match = re.fullmatch(
                r"data:image/(?:png|webp);base64,([A-Za-z0-9+/]+={0,2})", image
            )
            if match is None:
                raise ValueError("Invalid item image")
            try:
                image_bytes = base64.b64decode(match.group(1), validate=True)
            except (binascii.Error, ValueError):
                raise ValueError("Invalid item image") from None
            if not image_bytes or len(image_bytes) > MAX_ITEM_IMAGE_BYTES:
                raise ValueError("Item image exceeds the size limit")

    def to_dict(self) -> dict[str, Any]:
        """Return the storage representation."""
        result = {
            "uid": self.uid,
            "summary": self.summary,
            "status": self.status,
            "description": self.description,
            "due": self.due,
            "source_uid": self.source_uid,
        }
        if self.metadata:
            result["metadata"] = dict(self.metadata)
        return result


def import_items(raw_items: object) -> list[ShoppingItem]:
    """Validate a source response and copy open items without merging names."""
    if not isinstance(raw_items, list):
        raise ValueError("The source did not return an item list")
    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ValueError("Invalid source item")
        item = ShoppingItem(
            uid=str(uuid4()),
            summary=raw.get("summary"),
            status=raw.get("status"),
            description=raw.get("description"),
            due=raw.get("due"),
            source_uid=raw.get("uid") if raw.get("uid") else "",
        )
        if item.status == "needs_action":
            items.append(item)
    return items


def deletion_marker(item: ShoppingItem) -> dict[str, Any]:
    """Keep identity and provenance without retaining an item's image."""
    result = item.to_dict()
    metadata = result.get("metadata")
    if metadata:
        metadata.pop("image", None)
        if not metadata:
            result.pop("metadata")
    return result


def load_items(data: object) -> list[ShoppingItem]:
    """Validate persisted data; corrupt data must never trigger a new import."""
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ValueError("Invalid Einkaufszettel storage")
    items = []
    seen = set()
    for raw in data["items"]:
        if not isinstance(raw, dict):
            raise ValueError("Invalid stored item")
        item = ShoppingItem(
            uid=raw.get("uid"),
            summary=raw.get("summary"),
            status=raw.get("status"),
            description=raw.get("description"),
            due=raw.get("due"),
            source_uid=raw.get("source_uid"),
            metadata=raw.get("metadata", {}),
        )
        if item.uid in seen:
            raise ValueError("Duplicate stored UID")
        seen.add(item.uid)
        items.append(item)
    return items


def append_new_items(
    existing: list[ShoppingItem], incoming: list[ShoppingItem]
) -> list[ShoppingItem]:
    """Append unseen source identities without resetting local edits."""
    if any(not item.source_uid for item in incoming) or any(
        item.source_uid == "" for item in existing
    ):
        raise ValueError("Source item IDs are required for safe repeated copying")
    seen = {item.source_uid for item in existing}
    result = list(existing)
    for item in incoming:
        if item.source_uid not in seen:
            result.append(item)
            seen.add(item.source_uid)
    return result


def update_item(
    items: list[ShoppingItem],
    uid: str,
    summary: str,
    status: str,
    description: str | None,
    due: str | None,
) -> list[ShoppingItem]:
    """Produce a new snapshot, preserving local identity and provenance."""
    for index, old in enumerate(items):
        if old.uid == uid:
            new = replace(
                old, summary=summary, status=status, description=description, due=due
            )
            return [*items[:index], new, *items[index + 1 :]]
    raise ValueError(f"Unknown item UID: {uid}")
