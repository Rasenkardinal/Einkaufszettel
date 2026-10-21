"""Manually append new items from the configured source list."""

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.network import NoURLAvailableError, get_url

from . import EinkaufszettelConfigEntry
from .const import CONF_SOURCE, DOMAIN, update_signal
from .model import append_new_items
from .source import async_read_source


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EinkaufszettelConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Expose one copy button per configured list."""
    async_add_entities([CopySourceButton(entry), InstallWebAppButton(entry)])


class CopySourceButton(ButtonEntity):
    """Copy unseen open source entries without changing existing local entries."""

    _attr_has_entity_name = True
    _attr_translation_key = "copy_source"
    _attr_icon = "mdi:content-copy"

    def __init__(self, entry: EinkaufszettelConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_copy_source"
        self._attr_translation_placeholders = {"list_name": entry.data[CONF_NAME]}

    async def async_press(self) -> None:
        """Read, merge and persist atomically before notifying the To-do UI."""
        data = self._entry.runtime_data
        async with data.lock:
            try:
                incoming = await async_read_source(
                    self.hass, self._entry.data[CONF_SOURCE]
                )
                updated = append_new_items(data.items, incoming)
                if updated == data.items:
                    return
                await data.store.async_save(
                    {"items": [item.to_dict() for item in updated]}
                )
            except (HomeAssistantError, ValueError, OSError, TimeoutError) as err:
                raise HomeAssistantError(f"Cannot copy source list: {err}") from err
            data.items = updated
            async_dispatcher_send(self.hass, update_signal(self._entry.entry_id))


class InstallWebAppButton(ButtonEntity):
    """Provide a direct HA action to open and install the list's web app."""

    _attr_has_entity_name = True
    _attr_translation_key = "install_web_app"
    _attr_icon = "mdi:cellphone-arrow-down"

    def __init__(self, entry: EinkaufszettelConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_install_web_app"
        self._attr_translation_placeholders = {"list_name": entry.data[CONF_NAME]}

    async def async_press(self) -> None:
        """Show a Home Assistant notification linking to the installable PWA."""
        try:
            base_url = get_url(self.hass, prefer_external=True)
        except NoURLAvailableError:
            base_url = ""
        app_url = (
            f"{base_url.rstrip('/')}/{DOMAIN}/app.html?entry_id={self._entry.entry_id}"
        )
        persistent_notification.async_create(
            self.hass,
            (
                f"[Web-App öffnen und installieren]({app_url})\n\n"
                f"Falls sich der Link nicht öffnet, kopiere diese Adresse in "
                f"deinen Browser:\n\n{app_url}\n\n"
                "Du kannst den Einkaufszettel auch direkt über den neuen "
                "Eintrag in der Home-Assistant-Seitenleiste öffnen. Zum "
                "Installieren öffne die App dort in einem eigenen Browserfenster."
            ),
            title="Einkaufszettel",
            notification_id=f"{DOMAIN}_{self._entry.entry_id}_install",
        )
