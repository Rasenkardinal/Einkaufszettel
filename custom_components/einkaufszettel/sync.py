"""Durable, server-ordered field patches and source reconciliation state."""

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from typing import Any

from .model import ShoppingItem, deletion_marker


def new_sync_state() -> dict[str, Any]:
    """Keep receipts and deletion markers until an explicit future compaction."""
    return {
        "revision": 0,
        "receipts": {},
        "deleted": {},
        "source": {},
        "creates": {},
    }


def load_sync_state(value: object) -> dict[str, Any]:
    """Reject corrupt protocol state rather than forgetting deduplication."""
    if value is None:
        return new_sync_state()
    if not isinstance(value, dict) or set(value) != set(new_sync_state()):
        raise ValueError("Invalid synchronization storage")
    if type(value["revision"]) is not int or value["revision"] < 0:
        raise ValueError("Invalid synchronization revision")
    for name in ("receipts", "deleted", "source", "creates"):
        if not isinstance(value[name], dict) or any(
            not isinstance(key, str) or not key or not isinstance(item, dict)
            for key, item in value[name].items()
        ):
            raise ValueError(f"Invalid synchronization {name}")
    for receipt in value["receipts"].values():
        if not isinstance(receipt.get("payload"), str) or receipt.get("result") not in (
            "applied",
            "already_exists",
            "deleted",
        ):
            raise ValueError("Invalid operation receipt")
    for uid, item in value["deleted"].items():
        if item.get("uid") != uid:
            raise ValueError("Invalid deletion marker")
        ShoppingItem(**item)
    for baseline in value["source"].values():
        if (
            not isinstance(baseline.get("summary"), str)
            or baseline.get("status") not in ("needs_action", "completed")
            or type(baseline.get("present")) is not bool
            or type(baseline.get("superseded", False)) is not bool
        ):
            raise ValueError("Invalid source baseline")
    for intent in value["creates"].values():
        if (
            not isinstance(intent.get("before"), list)
            or any(not isinstance(uid, str) for uid in intent["before"])
            or not isinstance(intent.get("summary"), str)
            or type(intent.get("local_only", False)) is not bool
            or type(intent.get("needs_decision", False)) is not bool
            or not isinstance(intent.get("attempt", ""), str)
            or type(intent.get("match_count", 0)) is not int
            or intent.get("match_count", 0) < 0
            or not isinstance(intent.get("candidates", []), list)
            or any(
                not isinstance(candidate, dict)
                or not isinstance(candidate.get("uid"), str)
                or not isinstance(candidate.get("summary"), str)
                or candidate.get("status") not in ("needs_action", "completed")
                for candidate in intent.get("candidates", [])
            )
        ):
            raise ValueError("Invalid source creation intent")
    return deepcopy(value)


async def persist_items(
    data, items: list[ShoppingItem], state=None, *, product_operation=None
) -> None:
    """Commit the snapshot, receipts and tombstones in one HA Store write."""
    state = deepcopy(
        state if state is not None else getattr(data, "sync", new_sync_state())
    )
    deleted_sources = {
        item["source_uid"]
        for item in state["deleted"].values()
        if item.get("source_uid")
    }
    superseded_sources = {
        uid for uid, baseline in state["source"].items() if baseline.get("superseded")
    }
    items = [
        item
        for item in items
        if item.uid not in state["deleted"]
        and item.source_uid not in deleted_sources
        and item.source_uid not in superseded_sources
    ]
    if getattr(data, "product_rules", None) is not None:
        previous_items = {item.uid: item for item in data.items}
        events = []
        for item in items:
            old = previous_items.get(item.uid)
            if item.status == "needs_action" and (
                old is None
                or (
                    old.status == "completed"
                    and item.source_uid
                    and item.source_uid != old.source_uid
                )
            ):
                identity = (
                    f"source:{item.source_uid}"
                    if item.source_uid
                    else f"local:{item.uid}"
                )
                events.append(
                    (
                        f"added:{identity}",
                        item.summary,
                        item.metadata.get("catalog_id", "supermarket"),
                    )
                )
        items = await data.product_rules(
            items, operation=product_operation, events=events
        )
    previous = {item.uid: item for item in data.items}
    current = {item.uid: item for item in items}
    for uid in previous.keys() - current.keys():
        state["deleted"][uid] = deletion_marker(previous[uid])
    if items != data.items or state != getattr(data, "sync", new_sync_state()):
        state["revision"] += 1
    await data.store.async_save(
        {
            "items": [item.to_dict() for item in items],
            "sync": state,
        }
    )
    data.items = items
    data.sync = state


async def apply_operation(
    data, operation_id: str, action: str, uid: str, changes: dict
) -> str:
    """Apply once, ordered by acquisition of the caller's per-list lock."""
    if not operation_id or len(operation_id) > 200:
        raise ValueError("Invalid operation ID")
    if not isinstance(uid, str) or not uid or len(uid) > 200:
        raise ValueError("Invalid item UID")
    if action not in ("add_item", "update_item", "delete_item"):
        raise ValueError("Invalid operation action")
    if not isinstance(changes, dict) or set(changes) - {
        "summary",
        "status",
        "description",
        "due",
        "metadata",
    }:
        raise ValueError("Invalid item patch")
    if action == "delete_item" and changes:
        raise ValueError("Deletion cannot contain an item patch")
    payload = json.dumps([action, uid, changes], sort_keys=True, allow_nan=False)
    receipt_payload = payload
    metadata_changes = changes.get("metadata")
    if isinstance(metadata_changes, dict) and metadata_changes.get("image") is not None:
        receipt_payload = f"sha256:{hashlib.sha256(payload.encode()).hexdigest()}"
    state = deepcopy(getattr(data, "sync", new_sync_state()))
    receipt = state["receipts"].get(operation_id)
    if receipt:
        if receipt["payload"] not in (payload, receipt_payload):
            raise ValueError("Operation ID was already used for a different change")
        return receipt["result"]
    old = next((item for item in data.items if item.uid == uid), None)
    items = list(data.items)
    result = "applied"
    if uid in state["deleted"]:
        result = "deleted"
    elif action == "delete_item":
        # Unknown deletes also prevent delayed creation from resurrecting an ID.
        state["deleted"][uid] = (old or ShoppingItem(uid, "(deleted)")).to_dict()
        items = [item for item in items if item.uid != uid]
    elif action == "add_item" and old:
        result = "already_exists"
    else:
        if action == "update_item" and old is None:
            raise ValueError("Shopping item not found")
        values = dict(changes)
        if "metadata" in values:
            if not isinstance(values["metadata"], dict):
                raise ValueError("Invalid metadata patch")
            values["metadata"] = {**(old.metadata if old else {}), **values["metadata"]}
        if "summary" in values and isinstance(values["summary"], str):
            values["summary"] = values["summary"].strip()
        updated = replace(old, **values) if old else ShoppingItem(uid=uid, **values)
        items = (
            [updated if item.uid == uid else item for item in items]
            if old
            else [*items, updated]
        )
    state["receipts"][operation_id] = {
        "payload": receipt_payload,
        "result": result,
    }
    product_operation = None
    if (
        result == "applied"
        and action != "delete_item"
        and "category_id" in changes.get("metadata", {})
    ):
        article = next(item for item in items if item.uid == uid)
        product_operation = (
            operation_id,
            article.summary,
            changes["metadata"]["category_id"],
            payload,
            article.metadata.get("catalog_id", "supermarket"),
        )
    await persist_items(data, items, state, product_operation=product_operation)
    return result
