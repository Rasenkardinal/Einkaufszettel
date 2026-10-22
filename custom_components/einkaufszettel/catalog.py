"""Shared categories and market-specific category order."""

import base64
import binascii
from copy import deepcopy
from typing import Any
from uuid import uuid4

MAX_BONUS_CARD_BYTES = 512 * 1024
BONUS_CARD_PREFIXES = (
    "data:image/png;base64,",
    "data:image/jpeg;base64,",
    "data:image/webp;base64,",
)


def product_key(name: str) -> str:
    """Match spelling variants without merging different product names."""
    return " ".join(name.split()).lower().replace("ß", "ss").replace("ς", "σ")


def _validate_bonus_card(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    prefix = next(
        (prefix for prefix in BONUS_CARD_PREFIXES if value.startswith(prefix)), None
    )
    if prefix is None:
        return False
    encoded = value[len(prefix) :]
    if not encoded or len(encoded) > ((MAX_BONUS_CARD_BYTES + 2) // 3) * 4:
        return False
    try:
        image = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return False
    return 0 < len(image) <= MAX_BONUS_CARD_BYTES


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
    products = data.get("products", [])
    if not isinstance(products, list) or any(
        not isinstance(product, dict)
        or not isinstance(product.get("name"), str)
        or not product_key(product["name"])
        or product.get("key") != product_key(product["name"])
        or "category_id" not in product
        or (
            product.get("category_id") is not None
            and (
                not isinstance(product["category_id"], str)
                or product["category_id"] not in category_ids
            )
        )
        for product in products
    ):
        raise ValueError("Ungültige gespeicherte Produktzuordnungen.")
    if len({product["key"] for product in products}) != len(products):
        raise ValueError("Doppelte Produkte im Katalog.")
    receipts = data.get("product_operations", {})
    if not isinstance(receipts, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in receipts.items()
    ):
        raise ValueError("Ungültige Produktbestätigungen.")
    for market in data.get("supermarkets", []):
        if "bonus_card" in market and not _validate_bonus_card(market["bonus_card"]):
            raise ValueError(
                "Ungültiges Bonuskartenbild (maximal 512 KiB, PNG/JPEG/WebP)."
            )
        order = market.get("category_ids", [])
        if (
            not isinstance(order, list)
            or any(
                not isinstance(uid, str) or (uid and uid not in category_ids)
                for uid in order
            )
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
    if action == "remove_category_product":
        product = next(
            (p for p in result.get("products", []) if p["key"] == msg["product_key"]),
            None,
        )
        if product is None or product["category_id"] != msg["category_id"]:
            raise ValueError(
                "Die Produktzuordnung wurde inzwischen geändert. Bitte neu laden."
            )
        product["category_id"] = None
    elif action == "save_market_categories":
        market = next((m for m in markets if m["id"] == msg["market_id"]), None)
        if market is None:
            raise ValueError("Der Supermarkt wurde nicht gefunden. Bitte neu laden.")
        market["category_ids"] = list(msg["category_ids"])
    elif action == "save_market_bonus_card":
        market = next((m for m in markets if m["id"] == msg["market_id"]), None)
        if market is None:
            raise ValueError("Der Supermarkt wurde nicht gefunden. Bitte neu laden.")
        bonus_card = msg["bonus_card"]
        if bonus_card:
            if not _validate_bonus_card(bonus_card):
                raise ValueError(
                    "Ungültiges Bonuskartenbild (maximal 512 KiB, PNG/JPEG/WebP)."
                )
            market["bonus_card"] = bonus_card
        else:
            market.pop("bonus_card", None)
    else:
        uid = msg["category_id"]
        if uid and not any(c["id"] == uid for c in categories):
            raise ValueError("Die Kategorie wurde nicht gefunden. Bitte neu laden.")
        if action == "delete_category":
            if not uid:
                raise ValueError("Bitte wähle eine Kategorie.")
            result["categories"] = [c for c in categories if c["id"] != uid]
            for product in result.get("products", []):
                if product["category_id"] == uid:
                    product["category_id"] = None
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
