"""Authenticated WebSocket API for the installed shopping-list web app."""

import asyncio
from typing import Any
from uuid import uuid4

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .catalog import change_catalog, validate_catalog
from .const import CONF_SOURCE, DOMAIN, update_signal
from .model import ShoppingItem, append_new_items, update_item
from .source import async_read_source
from .sync import apply_operation, persist_items


async def _market_command(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    action = msg["type"].rsplit("/", 1)[-1]
    if action != "get_supermarkets" and (
        connection.user is None or not connection.user.is_admin
    ):
        connection.send_error(
            msg["id"], "unauthorized", "HA-Administratorrechte erforderlich."
        )
        return
    lock = hass.data.setdefault(f"{DOMAIN}.supermarkets_lock", asyncio.Lock())
    async with lock:
        store = Store[dict[str, Any]](hass, 1, f"{DOMAIN}.supermarkets")
        try:
            data = await store.async_load()
            if data is not None:
                validate_catalog(data)
            markets = [] if data is None else data["supermarkets"]
            if not isinstance(markets, list) or any(
                not isinstance(market, dict)
                or not isinstance(market.get("id"), str)
                or not market["id"]
                or not isinstance(market.get("name"), str)
                or not market["name"].strip()
                or len(market["name"]) > 100
                for market in markets
            ):
                raise ValueError("Ungültige gespeicherte Supermarktdaten.")
            if len({market["id"] for market in markets}) != len(markets):
                raise ValueError("Doppelte IDs in den gespeicherten Supermarktdaten.")
            if action != "get_supermarkets":
                uid = msg["market_id"]
                if uid and not any(market["id"] == uid for market in markets):
                    raise ValueError(
                        "Der Supermarkt wurde nicht gefunden. Bitte neu laden."
                    )
                if action == "delete_supermarket":
                    if not uid:
                        raise ValueError("Bitte wähle einen Supermarkt.")
                    markets = [market for market in markets if market["id"] != uid]
                else:
                    name = msg["name"].strip()
                    if not name or len(name) > 100:
                        raise ValueError("Der Name muss 1–100 Zeichen enthalten.")
                    if any(
                        m["id"] != uid and m["name"].casefold() == name.casefold()
                        for m in markets
                    ):
                        raise ValueError(
                            "Ein Supermarkt mit diesem Namen existiert bereits."
                        )
                    if uid:
                        markets = [
                            {**m, "name": name} if m["id"] == uid else m
                            for m in markets
                        ]
                    else:
                        markets = [*markets, {"id": uuid4().hex, "name": name}]
                await store.async_save({**(data or {}), "supermarkets": markets})
        except (HomeAssistantError, OSError, ValueError, KeyError, TypeError) as err:
            connection.send_error(msg["id"], "cannot_manage_supermarkets", str(err))
            return
        connection.send_result(msg["id"], markets)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get_supermarkets"})
@websocket_api.async_response
async def websocket_get_supermarkets(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Read the shared supermarket registry."""
    await _market_command(hass, connection, msg)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_supermarket",
        vol.Required("market_id"): str,
        vol.Required("name"): str,
    }
)
@websocket_api.async_response
async def websocket_save_supermarket(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Create or rename a supermarket; an empty ID creates a new one."""
    await _market_command(hass, connection, msg)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_supermarket",
        vol.Required("market_id"): str,
    }
)
@websocket_api.async_response
async def websocket_delete_supermarket(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Delete a supermarket without changing any shopping list."""
    await _market_command(hass, connection, msg)


async def _catalog_command(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    action = msg["type"].rsplit("/", 1)[-1]
    if action != "get_catalog" and (
        connection.user is None or not connection.user.is_admin
    ):
        connection.send_error(
            msg["id"], "unauthorized", "HA-Administratorrechte erforderlich."
        )
        return
    lock = hass.data.setdefault(f"{DOMAIN}.supermarkets_lock", asyncio.Lock())
    async with lock:
        store = Store[dict[str, Any]](hass, 1, f"{DOMAIN}.supermarkets")
        try:
            stored = await store.async_load()
            data = validate_catalog(stored if stored is not None else {})
            if action != "get_catalog":
                data = change_catalog(data, action, msg)
                await store.async_save(data)
            connection.send_result(
                msg["id"],
                {
                    "supermarkets": data.get("supermarkets", []),
                    "categories": data.get("categories", []),
                },
            )
        except (HomeAssistantError, OSError, ValueError, KeyError, TypeError) as err:
            connection.send_error(msg["id"], "cannot_manage_catalog", str(err))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get_catalog"})
@websocket_api.async_response
async def websocket_get_catalog(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Read shared categories and market orders."""
    await _catalog_command(hass, connection, msg)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_category",
        vol.Required("category_id"): str,
        vol.Required("name"): str,
    }
)
@websocket_api.async_response
async def websocket_save_category(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Create or rename a shared category."""
    await _catalog_command(hass, connection, msg)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_category",
        vol.Required("category_id"): str,
    }
)
@websocket_api.async_response
async def websocket_delete_category(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Delete a category and its market assignments."""
    await _catalog_command(hass, connection, msg)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_market_categories",
        vol.Required("market_id"): str,
        vol.Required("category_ids"): [str],
    }
)
@websocket_api.async_response
async def websocket_save_market_categories(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Save the ordered category assignments for a market."""
    await _catalog_command(hass, connection, msg)


def _get_entry(hass: HomeAssistant, connection, msg: dict[str, Any]):
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if (
        entry is None
        or entry.domain != DOMAIN
        or CONF_SOURCE not in entry.data
        or getattr(entry, "runtime_data", None) is None
    ):
        connection.send_error(msg["id"], "not_found", "Shopping list not found")
        return None
    return entry


def _send_snapshot(connection, message_id: int, entry, **extra) -> None:
    from .source_sync import source_conflicts  # noqa: PLC0415

    connection.send_result(
        message_id,
        {
            "entry_id": entry.entry_id,
            "name": entry.data[CONF_NAME],
            "items": [item.to_dict() for item in entry.runtime_data.items],
            "revision": getattr(entry.runtime_data, "sync", {}).get("revision", 0),
            "deleted_uids": list(
                getattr(entry.runtime_data, "sync", {}).get("deleted", {})
            ),
            "source_error": getattr(entry.runtime_data, "source_error", None),
            "source_conflicts": source_conflicts(entry.runtime_data),
            "source_local_items": [
                item
                for item in source_conflicts(entry.runtime_data, include_local=True)
                if item["local_only"]
            ],
            **extra,
        },
    )


async def _save_items(entry, items: list[ShoppingItem]) -> None:
    await persist_items(entry.runtime_data, items)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/apply_operation",
        vol.Required("entry_id"): str,
        vol.Required("operation_id"): str,
        vol.Required("action"): vol.In(["add_item", "update_item", "delete_item"]),
        vol.Required("uid"): str,
        vol.Required("changes"): dict,
    }
)
@websocket_api.async_response
async def websocket_apply_operation(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Acknowledge only after item changes and deduplication are durable."""
    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return
    async with entry.runtime_data.lock:
        try:
            result = await apply_operation(
                entry.runtime_data,
                msg["operation_id"],
                msg["action"],
                msg["uid"],
                msg["changes"],
            )
        except (HomeAssistantError, OSError, ValueError, TypeError) as err:
            connection.send_error(msg["id"], "cannot_apply_operation", str(err))
            return
        async_dispatcher_send(hass, update_signal(entry.entry_id))
        _send_snapshot(
            connection,
            msg["id"],
            entry,
            ack_operation_id=msg["operation_id"],
            operation_result=result,
        )


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/sync_source", vol.Required("entry_id"): str}
)
@websocket_api.async_response
async def websocket_sync_source(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Try source reconciliation without withholding already durable app changes."""
    from .source_sync import synchronize_source  # noqa: PLC0415

    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return
    completed = await synchronize_source(hass, entry)
    _send_snapshot(
        connection,
        msg["id"],
        entry,
        **(
            {}
            if completed
            else {
                "source_error": "Quelllistenabgleich läuft bereits oder die Liste ist ausgeblendet."
            }
        ),
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/resolve_source_conflict",
        vol.Required("entry_id"): str,
        vol.Required("uid"): str,
        vol.Required("token"): str,
        vol.Required("action"): vol.In(["link", "retry", "local"]),
        vol.Optional("source_uid"): str,
    }
)
@websocket_api.async_response
async def websocket_resolve_source_conflict(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Apply an explicit decision, rejecting stale dialogs from another device."""
    from .source_sync import resolve_source_conflict  # noqa: PLC0415

    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return
    try:
        async with asyncio.timeout(10):
            await resolve_source_conflict(
                hass,
                entry,
                msg["uid"],
                msg["token"],
                msg["action"],
                msg.get("source_uid"),
            )
    except (HomeAssistantError, OSError, ValueError, TimeoutError) as err:
        connection.send_error(
            msg["id"],
            "cannot_resolve_conflict",
            str(err) or "Zeitüberschreitung bei der Konfliktauflösung.",
        )
        return
    async_dispatcher_send(hass, update_signal(entry.entry_id))
    _send_snapshot(connection, msg["id"], entry)


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
            and CONF_SOURCE in entry.data
            and entry.options.get("enabled", True)
        ],
    )


def _sources(hass: HomeAssistant) -> list[dict[str, Any]]:
    registry = er.async_get(hass)
    entries = {
        entry.data[CONF_SOURCE]: entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if CONF_SOURCE in entry.data
    }
    result = []
    for state in hass.states.async_all("todo"):
        registered = registry.async_get(state.entity_id)
        if registered is not None and registered.platform == DOMAIN:
            continue
        entry = entries.get(state.entity_id)
        result.append(
            {
                "source_entity_id": state.entity_id,
                "source_name": state.name,
                "name": entry.data[CONF_NAME] if entry else state.name,
                "enabled": entry.options.get("enabled", True) if entry else False,
                "available": state.state not in ("unavailable", "unknown"),
            }
        )
    known = {source["source_entity_id"] for source in result}
    for source, entry in entries.items():
        if source not in known:
            result.append(
                {
                    "source_entity_id": source,
                    "source_name": source,
                    "name": entry.data[CONF_NAME],
                    "enabled": entry.options.get("enabled", True),
                    "available": False,
                }
            )
    return result


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get_sources"})
@websocket_api.async_response
async def websocket_get_sources(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Discover external HA lists, including disabled and unavailable sources."""
    connection.send_result(msg["id"], _sources(hass))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/configure_list",
        vol.Required("source_entity_id"): str,
        vol.Required("name"): str,
        vol.Required("enabled"): bool,
    }
)
@websocket_api.async_response
async def websocket_configure_list(
    hass: HomeAssistant, connection, msg: dict[str, Any]
) -> None:
    """Persist shared aliases and visibility without renaming Alexa lists."""
    if connection.user is None or not connection.user.is_admin:
        connection.send_error(
            msg["id"], "unauthorized", "HA-Administratorrechte erforderlich."
        )
        return
    source = msg["source_entity_id"]
    name = msg["name"].strip()
    candidates = {item["source_entity_id"] for item in _sources(hass)}
    if not name or len(name) > 100 or source not in candidates:
        connection.send_error(
            msg["id"], "invalid_input", "Select a HA list and a name (1-100 characters)"
        )
        return
    entry = next(
        (
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.data.get(CONF_SOURCE) == source
        ),
        None,
    )
    if entry is None:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data={CONF_SOURCE: source, CONF_NAME: name, "enabled": msg["enabled"]},
        )
        if result["type"] != "create_entry":
            connection.send_error(
                msg["id"],
                "cannot_configure_list",
                "Could not read or configure the selected HA source",
            )
            return
        entry = result["result"]
    hass.config_entries.async_update_entry(
        entry,
        title=name,
        data={**entry.data, CONF_NAME: name},
        options={**entry.options, "enabled": msg["enabled"]},
    )
    connection.send_result(msg["id"], {"entry_id": entry.entry_id})


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
