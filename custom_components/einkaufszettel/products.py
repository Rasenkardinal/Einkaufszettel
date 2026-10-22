"""Durable product rules shared by every list, including source imports."""

import asyncio
from copy import deepcopy
from dataclasses import replace
from typing import Any

from homeassistant.helpers.storage import Store

from .catalog import product_key, validate_catalog
from .const import DOMAIN


async def apply_product_rules(hass, items, *, operation=None, seed=()):
    """Persist assignments before projecting them; receipts make retries harmless."""
    lock = hass.data.setdefault(f"{DOMAIN}.supermarkets_lock", asyncio.Lock())
    async with lock:
        store = Store[dict[str, Any]](hass, 1, f"{DOMAIN}.supermarkets")
        stored = await store.async_load()
        catalog = deepcopy(validate_catalog(stored if stored is not None else {}))
        categories = {category["id"] for category in catalog.get("categories", [])}
        products = {product["key"]: product for product in catalog.get("products", [])}
        # Only bootstrap names never seen before; an explicit removal stays removed.
        for item in [*seed, *items]:
            category = item.metadata.get("category_id")
            key = product_key(item.summary)
            if (
                key not in products
                and "category_id" in item.metadata
                and (category is None or category in categories)
            ):
                products[key] = {
                    "key": key,
                    "name": item.summary,
                    "category_id": category,
                }
        if operation is not None:
            identity, name, category, payload = operation
            receipts = catalog.setdefault("product_operations", {})
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
                    "key": product_key(name),
                    "name": name,
                    "category_id": category,
                }
                receipts[identity] = payload
        if products or "products" in catalog:
            catalog["products"] = list(products.values())
        if catalog != (stored if stored is not None else {}):
            await store.async_save(catalog)
        return [
            replace(
                item,
                metadata={
                    **item.metadata,
                    "category_id": products[product_key(item.summary)]["category_id"],
                },
            )
            if product_key(item.summary) in products
            else item
            for item in items
        ]
