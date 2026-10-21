"""Shared categories and market-specific category order."""

from copy import deepcopy
from typing import Any
from uuid import uuid4


def validate_catalog(data: dict[str, Any]) -> dict[str, Any]:
    """Validate legacy market data as well as the extended catalog."""
    if not isinstance(data, dict):
        raise ValueError("Ungültige Katalogdaten.")
    for key in ("supermarkets", "categories"):
        records = data.get(key, [])
        if not isinstance(records, list) or any(
            not isinstance(record, dict)
            or not isinstance(record.get("id"), str)
            or not record["id"]
            or not isinstance(record.get("name"), str)
            or not record["name"].strip()
            or len(record["name"]) > 100
            for record in records
        ):
            raise ValueError("Ungültige Katalogdaten.")
        if len({record["id"] for record in records}) != len(records):
            raise ValueError("Doppelte IDs im Katalog.")
    category_ids = {category["id"] for category in data.get("categories", [])}
    for market in data.get("supermarkets", []):
        order = market.get("category_ids", [])
        if (
            not isinstance(order, list)
            or any(not isinstance(uid, str) or uid not in category_ids for uid in order)
            or len(set(order)) != len(order)
        ):
            raise ValueError("Ungültige Produktkategorien für einen Markt.")
    return data


def change_catalog(
    data: dict[str, Any], action: str, msg: dict[str, Any]
) -> dict[str, Any]:
    """Return a validated replacement without modifying the stored snapshot."""
    result = deepcopy(validate_catalog(data))
    categories = result.setdefault("categories", [])
    markets = result.setdefault("supermarkets", [])
    if action == "save_market_categories":
        market = next((m for m in markets if m["id"] == msg["market_id"]), None)
        if market is None:
            raise ValueError("Der Supermarkt wurde nicht gefunden. Bitte neu laden.")
        market["category_ids"] = list(msg["category_ids"])
    else:
        uid = msg["category_id"]
        if uid and not any(c["id"] == uid for c in categories):
            raise ValueError("Die Kategorie wurde nicht gefunden. Bitte neu laden.")
        if action == "delete_category":
            if not uid:
                raise ValueError("Bitte wähle eine Kategorie.")
            result["categories"] = [c for c in categories if c["id"] != uid]
            for market in markets:
                market["category_ids"] = [
                    key for key in market.get("category_ids", []) if key != uid
                ]
        elif action == "save_category":
            name = msg["name"].strip()
            if not name or len(name) > 100:
                raise ValueError("Der Name muss 1–100 Zeichen enthalten.")
            if any(
                c["id"] != uid and c["name"].casefold() == name.casefold()
                for c in categories
            ):
                raise ValueError("Eine Kategorie mit diesem Namen existiert bereits.")
            if uid:
                for category in categories:
                    if category["id"] == uid:
                        category["name"] = name
            else:
                categories.append({"id": uuid4().hex, "name": name})
        else:
            raise ValueError("Unbekannte Katalogaktion.")
    return validate_catalog(result)
