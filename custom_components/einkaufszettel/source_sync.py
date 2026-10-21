"""Reconcile the HA source without treating failed reads as empty lists."""

import asyncio
import logging
from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

from homeassistant.components.todo import TodoListEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import CONF_SOURCE, update_signal
from .source import async_read_all_source
from .sync import persist_items

_LOGGER = logging.getLogger(__name__)


def _baseline(item, present=True):
    return {"summary": item.summary, "status": item.status, "present": present}


async def _reconcile(hass, entry) -> None:
    data = entry.runtime_data
    entity_id = entry.data[CONF_SOURCE]
    incoming = await async_read_all_source(hass, entity_id)
    remote = {item.uid: item for item in incoming}
    state = deepcopy(data.sync)
    items = list(data.items)
    identities = [item.source_uid for item in items if item.source_uid is not None]
    if any(not uid for uid in identities) or len(identities) != len(set(identities)):
        raise ValueError("Die gespeicherte Quellzuordnung ist nicht eindeutig.")

    # A persisted intent is never blindly re-issued after a crash or timeout.
    for uid, intent in list(state["creates"].items()):
        candidates = [
            item
            for item in incoming
            if item.uid not in intent["before"] and item.summary == intent["summary"]
        ]
        linked = {item.source_uid for item in items if item.uid != uid}
        candidates = [item for item in candidates if item.uid not in linked]
        if len(candidates) != 1:
            raise HomeAssistantError(
                "Quellanlage noch unbestätigt oder mehrdeutig. "
                "Bitte die Quellliste prüfen; die Anlage wird nicht blind wiederholt."
            )
        source = candidates[0]
        items = [
            replace(item, source_uid=source.uid) if item.uid == uid else item
            for item in items
        ]
        if uid in state["deleted"]:
            state["deleted"][uid]["source_uid"] = source.uid
        state["source"][source.uid] = _baseline(source)
        del state["creates"][uid]
    if items != data.items or state != data.sync:
        await persist_items(data, items, state)
        state = deepcopy(data.sync)

    deleted_sources = {
        item["source_uid"]
        for item in state["deleted"].values()
        if item.get("source_uid")
    }
    linked = {item.source_uid for item in items if item.source_uid}
    for source in incoming:
        if source.uid in deleted_sources:
            continue
        if source.uid not in linked and source.status == "needs_action":
            # A removed source identity is not automatically resurrected.
            if (
                source.uid in state["source"]
                and not state["source"][source.uid]["present"]
            ):
                continue
            items.append(replace(source, uid=str(uuid4())))
            state["source"][source.uid] = _baseline(source)

    merged = []
    for item in items:
        source = remote.get(item.source_uid)
        baseline = state["source"].get(item.source_uid)
        if not item.source_uid:
            merged.append(item)
            continue
        if source is None:
            source_uid = item.source_uid
            if baseline is None or baseline["present"]:
                # Source removals retain our metadata and count as completion.
                item = replace(item, status="completed")
            elif item.status == "needs_action":
                # An explicit subsequent reopening needs a new source identity.
                item = replace(item, source_uid=None)
            state["source"][source_uid] = _baseline(item, present=False)
        elif baseline is None:
            # Bootstrap existing installations without discarding their local edits.
            state["source"][source.uid] = _baseline(source)
        else:
            changes = {
                field: getattr(source, field)
                for field in ("summary", "status")
                if getattr(source, field) != baseline[field]
            }
            item = replace(item, **changes)
            state["source"][source.uid] = _baseline(source)
        merged.append(item)
    if merged != data.items or state != data.sync:
        await persist_items(data, merged, state)

    entity = hass.states.get(entity_id)
    features = entity.attributes.get("supported_features", 0) if entity else 0
    errors = []
    for source_uid in deleted_sources:
        if source_uid not in remote:
            continue
        if not features & TodoListEntityFeature.DELETE_TODO_ITEM:
            errors.append("Die Quelle unterstützt das Löschen von Artikeln nicht.")
            continue
        await hass.services.async_call(
            "todo",
            "remove_item",
            {"entity_id": entity_id, "item": source_uid},
            blocking=True,
        )

    for item in list(data.items):
        source = remote.get(item.source_uid)
        if source is not None:
            patch = {}
            if item.summary != source.summary:
                patch["rename"] = item.summary
            if item.status != source.status:
                patch["status"] = item.status
            if not patch:
                continue
            if not features & TodoListEntityFeature.UPDATE_TODO_ITEM:
                errors.append("Die Quelle unterstützt das Ändern von Artikeln nicht.")
                continue
            await hass.services.async_call(
                "todo",
                "update_item",
                {"entity_id": entity_id, "item": source.uid, **patch},
                blocking=True,
            )
            # Read-back must confirm the write before we advance the baseline.
            confirmed = {
                value.uid: value
                for value in await async_read_all_source(hass, entity_id)
            }
            value = confirmed.get(source.uid)
            if value is None or any(
                getattr(value, field) != getattr(item, field)
                for field in ("summary", "status")
            ):
                raise HomeAssistantError(
                    "Die Quellliste hat die Änderung noch nicht bestätigt."
                )
            state = deepcopy(data.sync)
            state["source"][source.uid] = _baseline(value)
            await persist_items(data, data.items, state)
        elif not item.source_uid and item.status == "needs_action":
            if not features & TodoListEntityFeature.CREATE_TODO_ITEM:
                errors.append("Die Quelle unterstützt das Anlegen von Artikeln nicht.")
                continue
            # get_items is refreshed for each create; equal names remain distinct.
            before = await async_read_all_source(hass, entity_id)
            state = deepcopy(data.sync)
            state["creates"][item.uid] = {
                "before": [value.uid for value in before],
                "summary": item.summary,
            }
            await persist_items(data, data.items, state)
            await hass.services.async_call(
                "todo",
                "add_item",
                {"entity_id": entity_id, "item": item.summary},
                blocking=True,
            )
            after = await async_read_all_source(hass, entity_id)
            candidates = [
                value
                for value in after
                if value.uid not in state["creates"][item.uid]["before"]
                and value.summary == item.summary
            ]
            if len(candidates) != 1:
                raise HomeAssistantError(
                    "Die Anlage in der Quelle ist noch nicht eindeutig bestätigt."
                )
            created = candidates[0]
            state = deepcopy(data.sync)
            state["source"][created.uid] = _baseline(created)
            del state["creates"][item.uid]
            updated = [
                replace(value, source_uid=created.uid)
                if value.uid == item.uid
                else value
                for value in data.items
            ]
            await persist_items(data, updated, state)
    if errors:
        raise HomeAssistantError(" ".join(sorted(set(errors))))


async def synchronize_source(hass: HomeAssistant, entry) -> bool:
    """Bound network waits and explicitly expose source errors in app snapshots."""
    data = entry.runtime_data
    if not entry.options.get("enabled", True):
        return False
    if data.lock.locked():
        return False
    async with data.lock:
        previous = data.source_error
        revision = data.sync["revision"]
        try:
            async with asyncio.timeout(10):
                await _reconcile(hass, entry)
        except (HomeAssistantError, OSError, ValueError, TimeoutError) as err:
            data.source_error = (
                str(err) or "Zeitüberschreitung beim Quelllistenabgleich."
            )
            if data.source_error != previous:
                _LOGGER.warning(
                    "Source sync failed for %s: %s", entry.entry_id, data.source_error
                )
        else:
            data.source_error = None
        if data.sync["revision"] != revision or data.source_error != previous:
            async_dispatcher_send(hass, update_signal(entry.entry_id))
    return True


def start_source_sync(hass: HomeAssistant, entry) -> Callable[[], None]:
    """Poll even without an open app; HA owns the lifetime of this callback."""

    async def refresh(_now):
        await synchronize_source(hass, entry)

    return async_track_time_interval(hass, refresh, timedelta(seconds=30))
