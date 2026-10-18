"""An independent local copy of a Home Assistant To-do list."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.storage import Store

from .const import CONF_SOURCE, DOMAIN, STORAGE_VERSION
from .model import ShoppingItem, load_items
from .source import async_read_source

PLATFORMS = [Platform.TODO, Platform.BUTTON]


@dataclass
class EasyShoppingData:
    """The persisted snapshot and lock shared with the To-do entity."""

    store: Store[dict[str, Any]]
    items: list[ShoppingItem]
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


type EasyShoppingConfigEntry = ConfigEntry[EasyShoppingData]


async def async_setup_entry(
    hass: HomeAssistant, entry: EasyShoppingConfigEntry
) -> bool:
    """Load the local snapshot, importing only if storage does not yet exist."""
    store = Store[dict[str, Any]](hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
    try:
        data = await store.async_load()
        if data is None:
            items = await async_read_source(hass, entry.data[CONF_SOURCE])
            await store.async_save({"items": [item.to_dict() for item in items]})
        else:
            items = load_items(data)
    except (HomeAssistantError, OSError, ValueError, TimeoutError) as err:
        raise ConfigEntryNotReady(f"Cannot load Easy Shopping: {err}") from err

    entry.runtime_data = EasyShoppingData(store, items)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: EasyShoppingConfigEntry
) -> bool:
    """Unload without deleting the local shopping list."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
