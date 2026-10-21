"""An independent local copy of a Home Assistant To-do list."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.storage import Store

from .const import CONF_SOURCE, DOMAIN, LEGACY_DOMAIN, STORAGE_VERSION
from .model import ShoppingItem, load_items
from .source import async_read_source

PLATFORMS = [Platform.TODO, Platform.BUTTON]


@dataclass
class EinkaufszettelData:
    """The persisted snapshot and lock shared with the To-do entity."""

    store: Store[dict[str, Any]]
    items: list[ShoppingItem]
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


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
                if old_entry.data.get(CONF_SOURCE) == entry.data[CONF_SOURCE]
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
                items = await async_read_source(hass, entry.data[CONF_SOURCE])
            await store.async_save({"items": [item.to_dict() for item in items]})
        else:
            items = load_items(data)
    except (HomeAssistantError, OSError, ValueError, TimeoutError) as err:
        raise ConfigEntryNotReady(f"Cannot load Einkaufszettel: {err}") from err

    entry.runtime_data = EinkaufszettelData(store, items)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: EinkaufszettelConfigEntry
) -> bool:
    """Unload without deleting the local shopping list."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
