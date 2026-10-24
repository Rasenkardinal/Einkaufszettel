"""Shared categories and market-specific category order."""

import base64
import binascii
import re
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


def validate_product_usage(usage: Any) -> bool:
    """Accept additive per-list counters and compact weekly history."""
    if not isinstance(usage, dict):
        return False
    for list_id, stats in usage.items():
        if not isinstance(list_id, str) or not list_id or not isinstance(stats, dict):
            return False
        if (
            type(stats.get("added")) is not int
            or stats["added"] < 0
            or type(stats.get("last_added")) not in (int, float)
            or not 0 <= stats["last_added"] < float("inf")
            or not isinstance(stats.get("weeks"), dict)
        ):
            return False
        if any(
            not isinstance(week, str)
            or re.fullmatch(r"\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])", week) is None
            or type(count) is not int
            or count < 0
            for week, count in stats["weeks"].items()
        ):
            return False
    return True


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
        or not validate_product_usage(product.get("usage", {}))
        or type(product.get("category_known", True)) is not bool
        or (
            product.get("category_known") is False
            and product.get("category_id") is not None
        )
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
    product_keys = {product["key"] for product in products}
    dismissed_suggestions = data.get("dismissed_product_suggestions", [])
    if not isinstance(dismissed_suggestions, list):
        raise ValueError("Ungültige bestätigte Artikelsuchvorschläge.")
    dismissed_pairs = set()
    for pair in dismissed_suggestions:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or any(not isinstance(key, str) or key not in product_keys for key in pair)
            or pair[0] == pair[1]
            or frozenset(pair) in dismissed_pairs
        ):
            raise ValueError("Ungültige bestätigte Artikelsuchvorschläge.")
        dismissed_pairs.add(frozenset(pair))
    aliases = data.get("product_aliases", {})
    if not isinstance(aliases, dict) or any(
        not isinstance(key, str)
        or not key
        or product_key(key) != key
        or key in product_keys
        or not isinstance(value, str)
        or not value
        or product_key(value) != value
        or key == value
        or value not in product_keys
        for key, value in aliases.items()
    ):
        raise ValueError("Ungültige Produktnamen-Zuordnungen.")
    receipts = data.get("product_operations", {})
    if not isinstance(receipts, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in receipts.items()
    ):
        raise ValueError("Ungültige Produktbestätigungen.")
    events = data.get("product_events", {})
    if not isinstance(events, dict) or any(
        not isinstance(key, str) or not key or not isinstance(value, str)
        for key, value in events.items()
    ):
        raise ValueError("Ungültige Produktstatistik-Bestätigungen.")
    for market in data.get("supermarkets", []):
        if any(
            key in market and type(market[key]) is not bool
            for key in ("deposit_receipt_hint", "show_bonus_card")
        ):
            raise ValueError("Ungültige Supermarktoptionen.")
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
    if action == "dismiss_product_suggestion":
        product_keys = {product["key"] for product in result.get("products", [])}
        source_key = msg["product_key"]
        similar_key = msg["similar_key"]
        if (
            source_key == similar_key
            or source_key not in product_keys
            or similar_key not in product_keys
        ):
            raise ValueError("Die Artikelähnlichkeit wurde nicht gefunden.")
        pair = {source_key, similar_key}
        dismissed = result.setdefault("dismissed_product_suggestions", [])
        if not any(set(existing) == pair for existing in dismissed):
            dismissed.append([source_key, similar_key])
    elif action in (
        "create_product",
        "rename_product",
        "delete_product",
        "merge_product",
    ):
        products = result.setdefault("products", [])
        aliases = result.setdefault("product_aliases", {})
        if action == "create_product":
            name = msg["name"].strip()
            if not name or len(name) > 200:
                raise ValueError("Der Name muss 1–200 Zeichen enthalten.")
            key = product_key(name)
            if any(item["key"] == key for item in products):
                raise ValueError("Ein Artikel mit diesem Namen existiert bereits.")
            aliases.pop(key, None)
            products.append(
                {
                    "key": key,
                    "name": name,
                    "category_id": None,
                    "category_known": False,
                }
            )
        else:
            source_key = msg["product_key"]
            product = next(
                (item for item in products if item["key"] == source_key), None
            )
            if product is None:
                raise ValueError("Der Artikel wurde nicht gefunden. Bitte neu laden.")
            if action == "rename_product":
                name = msg["name"].strip()
                if not name or len(name) > 200:
                    raise ValueError("Der Name muss 1–200 Zeichen enthalten.")
                new_key = product_key(name)
                if new_key != source_key and any(
                    item["key"] == new_key for item in products
                ):
                    raise ValueError(
                        "Ein Artikel mit diesem Namen existiert bereits. Bitte führe die Artikel zusammen."
                    )
                if new_key == source_key:
                    product["name"] = name
                else:
                    aliases.pop(new_key, None)
                    for alias, target in list(aliases.items()):
                        if target == source_key:
                            aliases[alias] = new_key
                    aliases[source_key] = new_key
                    product["key"] = new_key
                    product["name"] = name
                    for receipt, target in result.get("product_events", {}).items():
                        if target == source_key:
                            result["product_events"][receipt] = new_key
            elif action == "delete_product":
                products.remove(product)
                result["product_aliases"] = {
                    alias: target
                    for alias, target in aliases.items()
                    if alias != source_key and target != source_key
                }
                result["product_events"] = {
                    receipt: target
                    for receipt, target in result.get("product_events", {}).items()
                    if target != source_key
                }
            else:
                target_key = msg["target_key"]
                target = next(
                    (item for item in products if item["key"] == target_key), None
                )
                if target is None or target is product:
                    raise ValueError("Bitte wähle einen anderen vorhandenen Artikel.")
                target_usage = target.setdefault("usage", {})
                for list_id, stats in product.get("usage", {}).items():
                    combined = target_usage.setdefault(
                        list_id, {"added": 0, "last_added": 0, "weeks": {}}
                    )
                    combined["added"] += stats["added"]
                    combined["last_added"] = max(
                        combined["last_added"], stats["last_added"]
                    )
                    for week, count in stats["weeks"].items():
                        combined["weeks"][week] = combined["weeks"].get(week, 0) + count
                if (
                    target.get("category_id") is None
                    and product.get("category_id") is not None
                ):
                    target["category_id"] = product["category_id"]
                    target["category_known"] = product.get("category_known", True)
                for alias, destination in list(aliases.items()):
                    if destination == source_key:
                        aliases[alias] = target_key
                aliases[source_key] = target_key
                products.remove(product)
                for receipt, destination in result.get("product_events", {}).items():
                    if destination == source_key:
                        result["product_events"][receipt] = target_key
        product_keys = {item["key"] for item in products}
        result["dismissed_product_suggestions"] = [
            pair
            for pair in result.get("dismissed_product_suggestions", [])
            if all(key in product_keys for key in pair)
        ]
    elif action == "remove_category_product":
        product = next(
            (p for p in result.get("products", []) if p["key"] == msg["product_key"]),
            None,
        )
        if product is None or product["category_id"] != msg["category_id"]:
            raise ValueError(
                "Die Produktzuordnung wurde inzwischen geändert. Bitte neu laden."
            )
        product["category_id"] = None
        product["category_known"] = True
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
                    product["category_known"] = True
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
