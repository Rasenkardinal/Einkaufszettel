"""Authenticated WebSocket API for the installed shopping-list web app."""

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import CONF_SOURCE, DOMAIN, update_signal
from .model import ShoppingItem, append_new_items, update_item
from .source import async_read_source


def _get_entry(hass: HomeAssistant, connection, msg: dict[str, Any]):
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN or entry.runtime_data is None:
        connection.send_error(msg["id"], "not_found", "Shopping list not found")
        return None
    return entry


def _send_snapshot(connection, message_id: int, entry) -> None:
    connection.send_result(
        message_id,
        {
            "entry_id": entry.entry_id,
            "name": entry.data[CONF_NAME],
            "items": [item.to_dict() for item in entry.runtime_data.items],
        },
    )


async def _save_items(entry, items: list[ShoppingItem]) -> None:
    await entry.runtime_data.store.async_save(
        {"items": [item.to_dict() for item in items]}
    )
    entry.runtime_data.items = items


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get_lists"})
@websocket_api.async_response
async def websocket_get_lists(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """List configured, loaded shopping lists without creating new sources."""
    connection.send_result(
        msg["id"],
        [
            {
                "entry_id": entry.entry_id,
                "name": entry.data[CONF_NAME],
                "source_entity_id": entry.data[CONF_SOURCE],
            }
            for entry in hass.config_entries.async_entries(DOMAIN)
            if getattr(entry, "runtime_data", None) is not None
        ],
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_list",
        vol.Required("entry_id"): str,
    }
)
@websocket_api.async_response
async def websocket_get_list(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Return a persisted list snapshot to an authenticated HA user."""
    entry = _get_entry(hass, connection, msg)
    if entry is not None:
        _send_snapshot(connection, msg["id"], entry)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/add_item",
        vol.Required("entry_id"): str,
        vol.Required("uid"): str,
        vol.Required("summary"): str,
    }
)
@websocket_api.async_response
async def websocket_add_item(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Add an item idempotently so an interrupted offline sync can retry."""
    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return
    data = entry.runtime_data
    async with data.lock:
        existing = next((item for item in data.items if item.uid == msg["uid"]), None)
        changed = existing is None
        try:
            if existing is not None:
                if existing.summary != msg["summary"]:
                    raise ValueError("The queued item ID already exists")
                updated = data.items
            else:
                created = ShoppingItem(
                    uid=msg["uid"],
                    summary=msg["summary"].strip(),
                )
                if not created.summary:
                    raise ValueError("An item must have a nonempty summary")
                updated = [*data.items, created]
                await _save_items(entry, updated)
        except (HomeAssistantError, OSError, ValueError) as err:
            connection.send_error(msg["id"], "cannot_add_item", str(err))
            return
        if changed:
            async_dispatcher_send(hass, update_signal(entry.entry_id))
        _send_snapshot(connection, msg["id"], entry)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/update_item",
        vol.Required("entry_id"): str,
        vol.Required("uid"): str,
        vol.Optional("summary"): str,
        vol.Optional("status"): vol.In(["needs_action", "completed"]),
    }
)
@websocket_api.async_response
async def websocket_update_item(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Update an item's text or completion state without replacing the list."""
    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return
    data = entry.runtime_data
    async with data.lock:
        old = next((item for item in data.items if item.uid == msg["uid"]), None)
        if old is None:
            connection.send_error(msg["id"], "not_found", "Shopping item not found")
            return
        try:
            updated = update_item(
                data.items,
                old.uid,
                msg.get("summary", old.summary),
                msg.get("status", old.status),
                old.description,
                old.due,
            )
            changed = updated != data.items
            if changed:
                await _save_items(entry, updated)
        except (HomeAssistantError, OSError, ValueError) as err:
            connection.send_error(msg["id"], "cannot_update_item", str(err))
            return
        if changed:
            async_dispatcher_send(hass, update_signal(entry.entry_id))
        _send_snapshot(connection, msg["id"], entry)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_item",
        vol.Required("entry_id"): str,
        vol.Required("uid"): str,
    }
)
@websocket_api.async_response
async def websocket_delete_item(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Delete one item idempotently."""
    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return
    data = entry.runtime_data
    async with data.lock:
        updated = [item for item in data.items if item.uid != msg["uid"]]
        changed = updated != data.items
        try:
            if changed:
                await _save_items(entry, updated)
        except (HomeAssistantError, OSError) as err:
            connection.send_error(msg["id"], "cannot_delete_item", str(err))
            return
        if changed:
            async_dispatcher_send(hass, update_signal(entry.entry_id))
        _send_snapshot(connection, msg["id"], entry)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/copy_source",
        vol.Required("entry_id"): str,
    }
)
@websocket_api.async_response
async def websocket_copy_source(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Append unseen open source items, preserving existing local edits."""
    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return
    data = entry.runtime_data
    async with data.lock:
        try:
            incoming = await async_read_source(hass, entry.data[CONF_SOURCE])
            updated = append_new_items(data.items, incoming)
            changed = updated != data.items
            if changed:
                await _save_items(entry, updated)
        except (HomeAssistantError, OSError, ValueError, TimeoutError) as err:
            connection.send_error(msg["id"], "cannot_copy_source", str(err))
            return
        if changed:
            async_dispatcher_send(hass, update_signal(entry.entry_id))
        _send_snapshot(connection, msg["id"], entry)
