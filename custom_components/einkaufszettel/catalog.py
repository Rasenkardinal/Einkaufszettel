"""Shared categories and market-specific category order."""

import base64
import binascii
import re
from copy import deepcopy
from typing import Any
from uuid import uuid4

MAX_BONUS_CARD_BYTES = 512 * 1024
CATALOG_FIELDS = (
    "categories",
    "products",
    "product_aliases",
    "dismissed_product_suggestions",
    "deleted_product_keys",
    "product_operations",
    "product_events",
)
BUILTIN_CATALOGS = {
    "supermarket": "Supermarkt",
    "hardware": "Baumarkt",
    "tasks": "Aufgaben",
}
BONUS_CARD_PREFIXES = (
    "data:image/png;base64,",
    "data:image/jpeg;base64,",
    "data:image/webp;base64,",
)


def product_key(name: str) -> str:
    """Match spelling variants without merging different product names."""
    return " ".join(name.split()).lower().replace("ß", "ss").replace("ς", "σ")


def product_usage_count(product: dict[str, Any]) -> int:
    """Return the corrected total without modifying list or weekly statistics."""
    return product.get("usage_adjustment", 0) + sum(
        max(stats["added"], sum(stats["weeks"].values()))
        for stats in product.get("usage", {}).values()
    )


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


def _empty_catalog(catalog_id: str, name: str) -> dict[str, Any]:
    return {
        "id": catalog_id,
        "name": name,
        "categories": [],
        "products": [],
        "product_aliases": {},
        "dismissed_product_suggestions": [],
        "deleted_product_keys": [],
        "product_operations": {},
        "product_events": {},
    }


def catalog_payload(data: dict[str, Any], catalog_id: str) -> dict[str, Any]:
    """Return the active catalog together with the market and catalog registry."""
    data = validate_catalog(data)
    catalog = data["catalogs"].get(catalog_id)
    if catalog is None:
        raise ValueError("Der Artikelkatalog wurde nicht gefunden. Bitte neu laden.")
    return {
        "catalog_id": catalog_id,
        "catalogs": data["catalogs"],
        "supermarkets": data["supermarkets"],
        **{key: catalog[key] for key in CATALOG_FIELDS},
    }


def validate_catalog(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate the legacy supermarket catalog and validate every parallel catalog."""
    if not isinstance(data, dict):
        raise ValueError("Ungültige Katalogdaten.")
    result = deepcopy(data)
    markets = result.get("supermarkets", [])
    if not isinstance(markets, list) or any(
        not isinstance(market, dict)
        or not isinstance(market.get("id"), str)
        or not market["id"]
        or not isinstance(market.get("name"), str)
        or not market["name"].strip()
        or len(market["name"]) > 100
        for market in markets
    ):
        raise ValueError("Ungültige Katalogdaten.")
    if len({market["id"] for market in markets}) != len(markets):
        raise ValueError("Doppelte IDs im Katalog.")

    catalogs = result.get("catalogs")
    if catalogs is None:
        catalogs = {
            catalog_id: _empty_catalog(catalog_id, name)
            for catalog_id, name in BUILTIN_CATALOGS.items()
        }
        catalogs["supermarket"].update(
            {
                key: result.get(key, _empty_catalog("", "")[key])
                for key in CATALOG_FIELDS
            }
        )
    if not isinstance(catalogs, dict):
        raise ValueError("Ungültige Artikelkataloge.")
    catalogs = deepcopy(catalogs)
    for catalog_id, name in BUILTIN_CATALOGS.items():
        catalogs.setdefault(catalog_id, _empty_catalog(catalog_id, name))
    if any(
        not isinstance(catalog_id, str)
        or not catalog_id
        or not isinstance(catalog, dict)
        or catalog.get("id") != catalog_id
        or not isinstance(catalog.get("name"), str)
        or not catalog["name"].strip()
        or len(catalog["name"]) > 100
        for catalog_id, catalog in catalogs.items()
    ):
        raise ValueError("Ungültige Artikelkataloge.")
    if len({catalog["name"].casefold() for catalog in catalogs.values()}) != len(
        catalogs
    ):
        raise ValueError("Doppelte Namen in den Artikelkatalogen.")

    for catalog in catalogs.values():
        for key in CATALOG_FIELDS:
            catalog.setdefault(key, _empty_catalog("", "")[key])
        categories = catalog["categories"]
        if not isinstance(categories, list) or any(
            not isinstance(record, dict)
            or not isinstance(record.get("id"), str)
            or not record["id"]
            or not isinstance(record.get("name"), str)
            or not record["name"].strip()
            or len(record["name"]) > 100
            for record in categories
        ):
            raise ValueError("Ungültige Katalogdaten.")
        if len({record["id"] for record in categories}) != len(categories):
            raise ValueError("Doppelte IDs im Katalog.")
        category_ids = {category["id"] for category in categories}
        products = catalog["products"]
        if not isinstance(products, list) or any(
            not isinstance(product, dict)
            or not isinstance(product.get("name"), str)
            or not product_key(product["name"])
            or product.get("key") != product_key(product["name"])
            or "category_id" not in product
            or not validate_product_usage(product.get("usage", {}))
            or type(product.get("usage_adjustment", 0)) is not int
            or (
                validate_product_usage(product.get("usage", {}))
                and product_usage_count(product) < 0
            )
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
        deleted_keys = catalog["deleted_product_keys"]
        if (
            not isinstance(deleted_keys, list)
            or any(
                not isinstance(key, str) or not key or product_key(key) != key
                for key in deleted_keys
            )
            or len(set(deleted_keys)) != len(deleted_keys)
        ):
            raise ValueError("Ungültige Produkt-Löschvermerke.")
        dismissed_suggestions = catalog["dismissed_product_suggestions"]
        if not isinstance(dismissed_suggestions, list):
            raise ValueError("Ungültige bestätigte Artikelsuchvorschläge.")
        dismissed_pairs = set()
        for pair in dismissed_suggestions:
            if (
                not isinstance(pair, list)
                or len(pair) != 2
                or any(
                    not isinstance(key, str) or key not in product_keys for key in pair
                )
                or pair[0] == pair[1]
                or frozenset(pair) in dismissed_pairs
            ):
                raise ValueError("Ungültige bestätigte Artikelsuchvorschläge.")
            dismissed_pairs.add(frozenset(pair))
        aliases = catalog["product_aliases"]
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
        receipts = catalog["product_operations"]
        if not isinstance(receipts, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in receipts.items()
        ):
            raise ValueError("Ungültige Produktbestätigungen.")
        events = catalog["product_events"]
        if not isinstance(events, dict) or any(
            not isinstance(key, str) or not key or not isinstance(value, str)
            for key, value in events.items()
        ):
            raise ValueError("Ungültige Produktstatistik-Bestätigungen.")

    for market in markets:
        market.setdefault("catalog_id", "supermarket")
        catalog = catalogs.get(market["catalog_id"])
        if catalog is None:
            raise ValueError("Ein Supermarkt verweist auf einen unbekannten Katalog.")
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
                not isinstance(uid, str)
                or (uid and uid not in {c["id"] for c in catalog["categories"]})
                for uid in order
            )
            or len(set(order)) != len(order)
        ):
            raise ValueError("Ungültige Produktkategorien für einen Markt.")
    result["catalogs"] = catalogs
    # Keep a read-compatible projection for older clients; catalogs is authoritative.
    result.update(
        {key: deepcopy(catalogs["supermarket"][key]) for key in CATALOG_FIELDS}
    )
    result["supermarkets"] = markets
    return result


def create_custom_catalog(
    data: dict[str, Any], catalog_id: str, name: str
) -> dict[str, Any]:
    """Add an empty reusable custom catalog without changing existing catalogs."""
    result = deepcopy(validate_catalog(data))
    name = name.strip()
    if (
        not catalog_id
        or catalog_id in result["catalogs"]
        or not name
        or len(name) > 100
        or any(
            catalog["name"].casefold() == name.casefold()
            for catalog in result["catalogs"].values()
        )
    ):
        raise ValueError("Der eigene Katalogname ist ungültig oder bereits vergeben.")
    result["catalogs"][catalog_id] = _empty_catalog(catalog_id, name)
    return validate_catalog(result)


def change_catalog(
    data: dict[str, Any], action: str, msg: dict[str, Any]
) -> dict[str, Any]:
    """Return a validated replacement without modifying the stored snapshot."""
    result = deepcopy(validate_catalog(data))
    catalog_id = msg.get("catalog_id", "supermarket")
    catalog = result["catalogs"].get(catalog_id)
    if catalog is None:
        raise ValueError("Der Artikelkatalog wurde nicht gefunden. Bitte neu laden.")
    result.update({key: deepcopy(catalog[key]) for key in CATALOG_FIELDS})
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
        "set_product_statistics",
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
            if action == "set_product_statistics":
                count = msg["count"]
                if type(count) is not int or not 0 <= count <= 2147483647:
                    raise ValueError(
                        "Bitte gib eine ganze Zahl von 0 bis 2147483647 ein."
                    )
                product["usage_adjustment"] = (
                    product.get("usage_adjustment", 0)
                    + count
                    - product_usage_count(product)
                )
            elif action == "rename_product":
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
                deleted_keys = result.setdefault("deleted_product_keys", [])
                for key in [
                    source_key,
                    *(a for a, t in aliases.items() if t == source_key),
                ]:
                    if key not in deleted_keys:
                        deleted_keys.append(key)
                result["product_aliases"] = {
                    alias: target
                    for alias, target in aliases.items()
                    if alias != source_key and target != source_key
                }
            else:
                target_key = msg["target_key"]
                target = next(
                    (item for item in products if item["key"] == target_key), None
                )
                if target is None or target is product:
                    raise ValueError("Bitte wähle einen anderen vorhandenen Artikel.")
                total = product_usage_count(target) + product_usage_count(product)
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
                if "usage_adjustment" in target or "usage_adjustment" in product:
                    target["usage_adjustment"] = (
                        target.get("usage_adjustment", 0)
                        + total
                        - product_usage_count(target)
                    )
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
        if market.get("catalog_id", "supermarket") != catalog_id:
            raise ValueError(
                "Der Katalog des Supermarkts hat sich geändert. Bitte neu laden."
            )
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
                if market.get("catalog_id", "supermarket") == catalog_id:
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
    result["catalogs"][catalog_id].update(
        {key: deepcopy(result[key]) for key in CATALOG_FIELDS}
    )
    return validate_catalog(result)
