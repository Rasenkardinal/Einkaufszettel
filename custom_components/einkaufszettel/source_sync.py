"""Reconcile the HA source without treating failed reads as empty lists."""

import asyncio
import hashlib
import json
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


def _normalized_name(name: str) -> str:
    return " ".join(name.split()).casefold()


def conflict_token(intent: dict, *, deleted=False) -> str:
    """Identify an attempt independently of changing candidate observations."""
    return hashlib.sha256(
        json.dumps(
            {
                key: intent.get(key)
                for key in ("before", "summary", "attempt", "local_only")
            }
            | {"deleted": deleted},
            sort_keys=True,
        ).encode()
    ).hexdigest()


def source_conflicts(data, *, include_local=False) -> list[dict]:
    linked = {item.source_uid for item in data.items if item.source_uid}
    return [
        {
            "uid": uid,
            "summary": intent["summary"],
            "token": conflict_token(intent, deleted=uid in data.sync["deleted"]),
            "candidates": [
                candidate
                for candidate in intent.get("candidates", [])
                if candidate["uid"] not in linked
            ],
            "reason": "multiple" if intent.get("match_count", 0) > 1 else "unconfirmed",
            "deleted": uid in data.sync["deleted"],
            "local_only": intent.get("local_only", False),
        }
        for uid, intent in getattr(data, "sync", {}).get("creates", {}).items()
        if (intent.get("needs_decision") or intent.get("local_only"))
        and (include_local or not intent.get("local_only"))
        and not (intent.get("local_only") and uid in data.sync["deleted"])
    ]


def _available_sources(data, incoming, uid):
    linked = {item.source_uid for item in data.items if item.uid != uid}
    blocked = {item.get("source_uid") for item in data.sync["deleted"].values()} | {
        key for key, value in data.sync["source"].items() if value.get("superseded")
    }
    return [item for item in incoming if item.uid not in linked | blocked]


async def resolve_source_conflict(hass, entry, uid, token, action, source_uid=None):
    """Revalidate a human decision against current source IDs under the list lock."""
    data = entry.runtime_data
    async with data.lock:
        intent = data.sync["creates"].get(uid)
        if (
            not intent
            or conflict_token(intent, deleted=uid in data.sync["deleted"]) != token
        ):
            raise ValueError(
                "Der Konflikt wurde bereits geändert. Bitte erneut synchronisieren."
            )
        state = deepcopy(data.sync)
        items = list(data.items)
        if action == "local":
            state["creates"][uid]["local_only"] = True
        elif action == "retry":
            if uid in state["deleted"]:
                raise ValueError(
                    "Ein gelöschter Artikel kann nicht erneut angelegt werden."
                )
            del state["creates"][uid]
        elif action == "link":
            incoming = await async_read_all_source(hass, entry.data[CONF_SOURCE])
            source = next(
                (
                    item
                    for item in _available_sources(data, incoming, uid)
                    if item.uid == source_uid
                ),
                None,
            )
            if source is None:
                raise ValueError(
                    "Der Quellartikel fehlt oder ist bereits zugeordnet. Bitte erneut synchronisieren."
                )
            items = [
                replace(item, source_uid=source.uid) if item.uid == uid else item
                for item in items
            ]
            if uid in state["deleted"]:
                state["deleted"][uid]["source_uid"] = source.uid
            state["source"][source.uid] = _baseline(source)
            del state["creates"][uid]
        else:
            raise ValueError("Unbekannte Konfliktentscheidung.")
        await persist_items(data, items, state)
        data.source_error = None


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
    unresolved_names = set()
    for uid, intent in list(state["creates"].items()):
        if intent.get("local_only"):
            intent["candidates"] = [
                {"uid": item.uid, "summary": item.summary, "status": item.status}
                for item in _available_sources(data, incoming, uid)
            ]
            continue
        candidates = [
            item
            for item in incoming
            if item.uid not in intent["before"]
            and _normalized_name(item.summary) == _normalized_name(intent["summary"])
        ]
        available = _available_sources(data, incoming, uid)
        available_ids = {item.uid for item in available}
        candidates = [
            item
            for item in candidates
            if item.uid in available_ids
            and not any(
                value.source_uid == item.uid and value.uid != uid for value in items
            )
        ]
        competing_attempt = any(
            other_uid != uid
            and not other.get("local_only")
            and _normalized_name(other["summary"])
            == _normalized_name(intent["summary"])
            for other_uid, other in state["creates"].items()
        )
        if len(candidates) != 1 or intent.get("needs_decision") or competing_attempt:
            intent["needs_decision"] = True
            intent["match_count"] = len(candidates)
            intent["candidates"] = [
                {"uid": item.uid, "summary": item.summary, "status": item.status}
                for item in available
            ]
            unresolved_names.add(_normalized_name(intent["summary"]))
            continue
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
        if source is not None and _normalized_name(item.summary) == _normalized_name(
            source.summary
        ):
            item = replace(item, summary=source.summary)
        merged.append(item)

    linked = {item.source_uid for item in merged if item.source_uid}
    unlinked = [
        source
        for source in incoming
        if source.uid not in linked
        and source.uid not in deleted_sources
        and source.status == "needs_action"
        and not state["source"].get(source.uid, {}).get("superseded")
        and state["source"].get(source.uid, {}).get("present", True)
        and _normalized_name(source.summary) not in unresolved_names
    ]
    # Decide all matches against the same snapshot, never by source iteration order.
    for source in unlinked:
        name = _normalized_name(source.summary)
        matches = [
            item
            for item in merged
            if _normalized_name(item.summary) == name
            and not state["creates"].get(item.uid, {}).get("local_only")
        ]
        unique_incoming = (
            sum(_normalized_name(item.summary) == name for item in unlinked) == 1
        )
        if source.uid not in state["source"] and unique_incoming and len(matches) == 1:
            old = matches[0]
            if old.source_uid:
                state["source"][old.source_uid]["superseded"] = True
            reopened = replace(
                old,
                summary=source.summary,
                status="needs_action",
                source_uid=source.uid,
            )
            merged = [reopened if item.uid == old.uid else item for item in merged]
        else:
            merged.append(replace(source, uid=str(uuid4())))
        state["source"][source.uid] = _baseline(source)
    if merged != data.items or state != data.sync:
        await persist_items(data, merged, state)

    entity = hass.states.get(entity_id)
    features = entity.attributes.get("supported_features", 0) if entity else 0
    errors = []
    if unresolved_names:
        errors.append(
            "Bei einigen Artikeln ist noch unklar, ob sie in der verbundenen Liste "
            "angelegt wurden. Bitte über „Sync-Konflikte auflösen“ prüfen. "
            "Andere Artikel werden weiter abgeglichen."
        )
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
        if item.uid in data.sync["creates"]:
            continue
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
            if (
                value is None
                or _normalized_name(value.summary) != _normalized_name(item.summary)
                or value.status != item.status
            ):
                raise HomeAssistantError(
                    f"Die Änderung an „{item.summary}“ ist in der verbundenen Liste "
                    "noch nicht bestätigt. Sie bleibt in der App gespeichert; "
                    "der Abgleich wird erneut versucht."
                )
            state = deepcopy(data.sync)
            state["source"][source.uid] = _baseline(value)
            updated = [
                replace(article, summary=value.summary)
                if article.uid == item.uid
                else article
                for article in data.items
            ]
            await persist_items(data, updated, state)
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
                "attempt": uuid4().hex,
            }
            await persist_items(data, data.items, state)
            try:
                async with asyncio.timeout(3):
                    await hass.services.async_call(
                        "todo",
                        "add_item",
                        {"entity_id": entity_id, "item": item.summary},
                        blocking=True,
                    )
                    after = await async_read_all_source(hass, entity_id)
            except (HomeAssistantError, OSError, ValueError, TimeoutError) as err:
                state = deepcopy(data.sync)
                state["creates"][item.uid]["needs_decision"] = True
                await persist_items(data, data.items, state)
                errors.append(
                    f"„{item.summary}“ ist in der App gespeichert. Ob der Artikel auch "
                    "in der verbundenen Liste angelegt wurde, konnte nicht bestätigt "
                    f"werden ({str(err) or 'Zeitüberschreitung'}). Bitte über "
                    "„Sync-Konflikte auflösen“ prüfen, bevor er erneut angelegt wird."
                )
                continue
            candidates = [
                value
                for value in after
                if value.uid not in state["creates"][item.uid]["before"]
                and _normalized_name(value.summary) == _normalized_name(item.summary)
            ]
            if len(candidates) != 1:
                state = deepcopy(data.sync)
                intent = state["creates"][item.uid]
                intent["needs_decision"] = True
                intent["match_count"] = len(candidates)
                intent["candidates"] = [
                    {"uid": value.uid, "summary": value.summary, "status": value.status}
                    for value in _available_sources(data, after, item.uid)
                ]
                await persist_items(data, data.items, state)
                errors.append(
                    f"„{item.summary}“ ist in der App gespeichert. In der verbundenen "
                    "Liste wurde kein eindeutig passender neuer Artikel bestätigt. "
                    "Bitte über „Sync-Konflikte auflösen“ prüfen."
                )
                continue
            created = candidates[0]
            state = deepcopy(data.sync)
            state["source"][created.uid] = _baseline(created)
            del state["creates"][item.uid]
            updated = [
                replace(value, source_uid=created.uid, summary=created.summary)
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
