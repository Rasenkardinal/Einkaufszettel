"""An independent local copy of a Home Assistant To-do list."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .const import CONF_SOURCE, DOMAIN, LEGACY_DOMAIN, STORAGE_VERSION
from .model import ShoppingItem, load_items
from .source import async_read_source
from .sync import load_sync_state, new_sync_state, persist_items

PLATFORMS = [Platform.BUTTON]
WEBAPP_PATH = Path(__file__).parent / "www"
PANEL_PATH = f"{DOMAIN}_app"
PANEL_ENTRIES_KEY = f"{DOMAIN}.panel_entries"


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Serve the installable web app and register its authenticated API."""
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                f"/{DOMAIN}",
                str(WEBAPP_PATH),
                cache_headers=False,
            )
        ]
    )
    from .websocket import (  # noqa: PLC0415
        websocket_add_item,
        websocket_apply_operation,
        websocket_configure_list,
        websocket_copy_source,
        websocket_create_product,
        websocket_delete_category,
        websocket_delete_item,
        websocket_delete_product,
        websocket_delete_supermarket,
        websocket_dismiss_product_suggestion,
        websocket_get_catalog,
        websocket_get_list,
        websocket_get_lists,
        websocket_get_sources,
        websocket_get_supermarkets,
        websocket_merge_product,
        websocket_remove_category_product,
        websocket_rename_product,
        websocket_resolve_source_conflict,
        websocket_save_category,
        websocket_save_market_bonus_card,
        websocket_save_market_categories,
        websocket_save_supermarket,
        websocket_sync_source,
        websocket_update_item,
    )

    for command in (
        websocket_get_list,
        websocket_get_lists,
        websocket_get_sources,
        websocket_configure_list,
        websocket_add_item,
        websocket_update_item,
        websocket_delete_item,
        websocket_copy_source,
        websocket_get_supermarkets,
        websocket_get_catalog,
        websocket_save_category,
        websocket_delete_category,
        websocket_save_market_bonus_card,
        websocket_save_market_categories,
        websocket_save_supermarket,
        websocket_delete_supermarket,
        websocket_apply_operation,
        websocket_sync_source,
        websocket_resolve_source_conflict,
        websocket_remove_category_product,
        websocket_create_product,
        websocket_rename_product,
        websocket_delete_product,
        websocket_merge_product,
        websocket_dismiss_product_suggestion,
    ):
        websocket_api.async_register_command(hass, command)
    return True


@dataclass
class EinkaufszettelData:
    """The persisted snapshot and lock shared with the To-do entity."""

    store: Store[dict[str, Any]]
    items: list[ShoppingItem]
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    sync: dict[str, Any] = field(default_factory=new_sync_state)
    source_error: str | None = None
    cancel_source_sync: Callable[[], None] | None = None
    product_rules: Callable[..., Awaitable[list[ShoppingItem]]] | None = None


type EinkaufszettelConfigEntry = ConfigEntry[EinkaufszettelData]


async def async_setup_entry(
    hass: HomeAssistant, entry: EinkaufszettelConfigEntry
) -> bool:
    """Load local data, migrate a matching legacy store, or import the source."""
    store = Store[dict[str, Any]](hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
    try:
        data = await store.async_load()
        if data is None:
            legacy_entries = [
                old_entry
                for old_entry in hass.config_entries.async_entries(LEGACY_DOMAIN)
                if CONF_SOURCE in entry.data
                and old_entry.data.get(CONF_SOURCE) == entry.data[CONF_SOURCE]
            ]
            if len(legacy_entries) > 1:
                raise ValueError(
                    "More than one legacy entry uses this source; resolve duplicates first"
                )
            if legacy_entries:
                legacy_entry = legacy_entries[0]
                legacy_store = Store[dict[str, Any]](
                    hass,
                    STORAGE_VERSION,
                    f"{LEGACY_DOMAIN}.{legacy_entry.entry_id}",
                )
                legacy_data = await legacy_store.async_load()
            else:
                legacy_data = None

            if legacy_data is not None:
                items = load_items(legacy_data)
            else:
                items = (
                    await async_read_source(hass, entry.data[CONF_SOURCE])
                    if CONF_SOURCE in entry.data
                    else []
                )
            await store.async_save({"items": [item.to_dict() for item in items]})
        else:
            items = load_items(data)
        sync = load_sync_state(data.get("sync") if data is not None else None)
    except (HomeAssistantError, OSError, ValueError, TimeoutError) as err:
        raise ConfigEntryNotReady(f"Cannot load Einkaufszettel: {err}") from err

    entry.runtime_data = EinkaufszettelData(store, items, sync=sync)
    from .products import apply_product_rules  # noqa: PLC0415

    async def product_rules(articles, *, operation=None, events=()):
        if operation is not None:
            identity, name, category, payload = operation
            operation = (f"{entry.entry_id}:{identity}", name, category, payload)
        return await apply_product_rules(
            hass,
            articles,
            operation=operation,
            events=[
                (f"{entry.entry_id}:{identity}", name) for identity, name in events
            ],
            list_id=entry.entry_id,
        )

    entry.runtime_data.product_rules = product_rules
    try:
        seed = [*items, *(ShoppingItem(**item) for item in sync["deleted"].values())]
        migrated = await apply_product_rules(hass, items, seed=seed)
        if migrated != items:
            await persist_items(entry.runtime_data, migrated)
    except (HomeAssistantError, OSError, ValueError) as err:
        raise ConfigEntryNotReady(f"Cannot load product assignments: {err}") from err
    registry = er.async_get(hass)
    for entity in list(registry.entities.values()):
        if entity.platform == DOMAIN and entity.entity_id.startswith("todo."):
            registry.async_remove(entity.entity_id)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    panel_entries = hass.data.setdefault(PANEL_ENTRIES_KEY, set())
    if not panel_entries:
        frontend.async_register_built_in_panel(
            hass,
            "iframe",
            sidebar_title="Einkaufszettel",
            sidebar_icon="mdi:cart-outline",
            frontend_url_path=PANEL_PATH,
            config={"url": f"/{DOMAIN}/app.html"},
        )
    panel_entries.add(entry.entry_id)
    if CONF_SOURCE in entry.data:
        from .source_sync import start_source_sync  # noqa: PLC0415

        entry.runtime_data.cancel_source_sync = start_source_sync(hass, entry)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: EinkaufszettelConfigEntry
) -> bool:
    """Unload without deleting the local shopping list."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        if entry.runtime_data.cancel_source_sync:
            entry.runtime_data.cancel_source_sync()
        panel_entries = hass.data.get(PANEL_ENTRIES_KEY, set())
        panel_entries.discard(entry.entry_id)
        if not panel_entries:
            frontend.async_remove_panel(hass, PANEL_PATH)
    return unloaded
