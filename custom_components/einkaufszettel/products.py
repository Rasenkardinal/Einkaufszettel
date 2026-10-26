"""Durable product rules shared by every list, including source imports."""

import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from homeassistant.helpers.storage import Store

from .catalog import product_key, validate_catalog
from .const import DOMAIN


async def apply_product_rules(
    hass, items, *, operation=None, seed=(), events=(), list_id=None
):
    """Persist assignments before projecting them; receipts make retries harmless."""
    lock = hass.data.setdefault(f"{DOMAIN}.supermarkets_lock", asyncio.Lock())
    async with lock:
        store = Store[dict[str, Any]](hass, 1, f"{DOMAIN}.supermarkets")
        stored = await store.async_load()
        catalog = deepcopy(validate_catalog(stored if stored is not None else {}))
        catalogs = catalog["catalogs"]
        product_maps = {
            catalog_id: {
                product["key"]: product for product in value.get("products", [])
            }
            for catalog_id, value in catalogs.items()
        }

        def catalog_for(item):
            catalog_id = item.metadata.get("catalog_id", "supermarket")
            value = catalogs.get(catalog_id)
            if value is None:
                raise ValueError("Ein Artikel verweist auf einen unbekannten Katalog.")
            return value, product_maps[catalog_id]

        def canonical_item(item):
            value, products = catalog_for(item)
            item_key = product_key(item.summary)
            key = value.get("product_aliases", {}).get(item_key, item_key)
            product = products.get(key)
            if product is None or (item.source_uid and item_key == key):
                return item
            return replace(item, summary=product["name"])

        def product_for(item):
            value, products = catalog_for(item)
            key = value.get("product_aliases", {}).get(
                product_key(item.summary), product_key(item.summary)
            )
            return products.get(key)

        items = [canonical_item(item) for item in items]
        seed = [canonical_item(item) for item in seed]
        # Only bootstrap names never seen before; an explicit removal stays removed.
        for item in [*seed, *items]:
            value, products = catalog_for(item)
            categories = {category["id"] for category in value.get("categories", [])}
            aliases = value.get("product_aliases", {})
            deleted_keys = set(value.get("deleted_product_keys", []))
            category = item.metadata.get("category_id")
            key = aliases.get(product_key(item.summary), product_key(item.summary))
            if key in deleted_keys and key not in products:
                continue
            if (
                key not in products
                or (
                    not products[key].get("category_known", True)
                    and "category_id" in item.metadata
                )
            ) and (category is None or category in categories):
                products[key] = {
                    **products.get(key, {}),
                    "key": key,
                    "name": item.summary,
                    "category_id": category,
                    "category_known": "category_id" in item.metadata,
                }
        if operation is not None:
            identity, name, category, payload, *catalog_id_value = operation
            catalog_id = catalog_id_value[0] if catalog_id_value else "supermarket"
            value = catalogs.get(catalog_id)
            if value is None:
                raise ValueError("Der Artikelkatalog wurde nicht gefunden.")
            products = product_maps[catalog_id]
            categories = {item["id"] for item in value.get("categories", [])}
            aliases = value.get("product_aliases", {})
            name_key = aliases.get(product_key(name), product_key(name))
            if name_key in products:
                name = products[name_key]["name"]
            receipts = value.setdefault("product_operations", {})
            previous = receipts.get(identity)
            if previous is not None and previous != payload:
                raise ValueError(
                    "Die Produktaktion wurde bereits mit anderem Inhalt verwendet."
                )
            if previous is None:
                if category is not None and category not in categories:
                    raise ValueError(
                        "Die Kategorie ist nicht mehr verfügbar. Bitte neu laden."
                    )
                products[product_key(name)] = {
                    **products.get(product_key(name), {}),
                    "key": product_key(name),
                    "name": name,
                    "category_id": category,
                    "category_known": True,
                }
                receipts[identity] = payload
        for event in events:
            identity, name, *catalog_id_value = event
            catalog_id = catalog_id_value[0] if catalog_id_value else "supermarket"
            value = catalogs.get(catalog_id)
            if value is None:
                raise ValueError("Der Artikelkatalog wurde nicht gefunden.")
            products = product_maps[catalog_id]
            aliases = value.get("product_aliases", {})
            if not list_id:
                raise ValueError("Die Einkaufsliste für die Produktstatistik fehlt.")
            receipts = value.setdefault("product_events", {})
            key = aliases.get(product_key(name), product_key(name))
            name = products[key]["name"] if key in products else name
            previous = receipts.get(identity)
            if previous is not None:
                continue
            product = products.setdefault(
                key,
                {
                    "key": key,
                    "name": name,
                    "category_id": None,
                    "category_known": False,
                },
            )
            stats = product.setdefault("usage", {}).setdefault(
                list_id, {"added": 0, "last_added": 0, "weeks": {}}
            )
            now = datetime.now(UTC)
            week = now.strftime("%G-W%V")
            stats["added"] += 1
            stats["last_added"] = now.timestamp() * 1000
            stats["weeks"][week] = stats["weeks"].get(week, 0) + 1
            receipts[identity] = key
        for catalog_id, value in catalogs.items():
            if product_maps[catalog_id] or "products" in value:
                value["products"] = list(product_maps[catalog_id].values())
        if catalog != (stored if stored is not None else {}):
            await store.async_save(validate_catalog(catalog))
        projected = []
        for item in items:
            product = product_for(item)
            if product is not None and (
                product.get("category_known", True) or "category_id" in item.metadata
            ):
                item = replace(
                    item,
                    metadata={**item.metadata, "category_id": product["category_id"]},
                )
            projected.append(item)
        return projected
