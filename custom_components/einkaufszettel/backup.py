"""Versioned backups and crash-recoverable replacement of integration data."""

import asyncio
import hashlib
import json
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from copy import deepcopy
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from uuid import uuid4

from homeassistant.components import websocket_api
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from .catalog import validate_catalog
from .const import CONF_SOURCE, DOMAIN
from .model import load_items
from .sync import load_sync_state

_LOGGER = logging.getLogger(__name__)
MAX_BACKUP_BYTES = 100 * 1024 * 1024
FORMAT = "easy-shopping-backup"


def canonical(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Doppeltes JSON-Feld: {key}")
        result[key] = value
    return result


def read_backup(raw: bytes) -> dict:
    """Validate the entire document before creating a preview or writing data."""
    if len(raw) > MAX_BACKUP_BYTES:
        raise ValueError("Die Sicherung darf maximal 100 MiB groß sein.")
    try:
        document = json.loads(raw, object_pairs_hook=_unique_object)
    except RecursionError as err:
        raise ValueError("Die JSON-Datei ist zu tief verschachtelt.") from err
    if not isinstance(document, dict) or set(document) != {"payload", "sha256"}:
        raise ValueError("Ungültige Sicherungsdatei.")
    payload = document["payload"]
    if hashlib.sha256(canonical(payload)).hexdigest() != document["sha256"]:
        raise ValueError("Die Prüfsumme stimmt nicht. Die Datei wurde verändert.")
    validate_payload(payload)
    return payload


def validate_payload(payload):
    if (
        not isinstance(payload, dict)
        or set(payload)
        != {"format", "schema_version", "app_version", "created_at", "lists", "catalog"}
        or payload["format"] != FORMAT
        or type(payload["schema_version"]) is not int
        or payload["schema_version"] != 1
        or not isinstance(payload["app_version"], str)
        or not isinstance(payload["created_at"], str)
        or not isinstance(payload["lists"], list)
    ):
        raise ValueError(
            "Unbekanntes Sicherungsformat oder nicht unterstützte Version."
        )
    created = datetime.fromisoformat(payload["created_at"])
    if created.tzinfo is None:
        raise ValueError("Das Sicherungsdatum benötigt eine Zeitzone.")
    if validate_catalog(payload["catalog"]) != payload["catalog"]:
        raise ValueError(
            "Der Artikelkatalog ist nicht vollständig oder benötigt eine nicht unterstützte Migration."
        )
    ids, sources, epochs = set(), set(), set()
    for record in payload["lists"]:
        if not isinstance(record, dict) or set(record) != {
            "entry_id",
            "name",
            "source_entity_id",
            "options",
            "snapshot",
        }:
            raise ValueError("Ungültige Liste in der Sicherung.")
        if (
            not isinstance(record["entry_id"], str)
            or not record["entry_id"]
            or record["entry_id"] in ids
            or not isinstance(record["name"], str)
            or not 1 <= len(record["name"].strip()) <= 100
            or not isinstance(record["source_entity_id"], str)
            or not record["source_entity_id"].startswith("todo.")
            or record["source_entity_id"] in sources
        ):
            raise ValueError("Ungültige oder doppelte Listenidentität.")
        ids.add(record["entry_id"])
        sources.add(record["source_entity_id"])
        options = record["options"]
        if (
            not isinstance(options, dict)
            or set(options) - {"enabled", "auto_shopping_threshold", "source_paused"}
            or any(
                type(options.get(key, True)) is not bool
                for key in ("enabled", "source_paused")
            )
            or type(options.get("auto_shopping_threshold", 0)) is not int
            or not 0
            <= options.get("auto_shopping_threshold", 0)
            <= 9_007_199_254_740_991
        ):
            raise ValueError("Ungültige Listeneinstellungen.")
        snapshot = record["snapshot"]
        if (
            not isinstance(snapshot, dict)
            or set(snapshot) != {"items", "sync", "restore_id"}
            or not isinstance(snapshot["restore_id"], str)
        ):
            raise ValueError("Ungültiger Listenspeicher.")
        epochs.add(snapshot["restore_id"])
        if len(epochs) > 1:
            raise ValueError(
                "Die Listen stammen aus unterschiedlichen Wiederherstellungsständen."
            )
        items = load_items(snapshot)
        if [item.to_dict() for item in items] != snapshot["items"]:
            raise ValueError("Unbekannte oder unvollständige Artikelfelder.")
        state = load_sync_state(snapshot["sync"])
        deleted = load_items({"items": list(state["deleted"].values())})
        if any(
            item.metadata.get("catalog_id", "supermarket")
            not in payload["catalog"]["catalogs"]
            for item in [*items, *deleted]
        ):
            raise ValueError("Ein Artikel verweist auf einen unbekannten Katalog.")
        source_ids = [item.source_uid for item in items if item.source_uid]
        if len(set(source_ids)) != len(source_ids) or any(
            item.uid in state["deleted"] for item in items
        ):
            raise ValueError("Widersprüchliche Artikel- oder Quellzuordnung.")


def encode_backup(payload) -> bytes:
    validate_payload(payload)
    result = canonical(
        {"payload": payload, "sha256": hashlib.sha256(canonical(payload)).hexdigest()}
    )
    if len(result) > MAX_BACKUP_BYTES:
        raise ValueError("Die Sicherung überschreitet die Grenze von 100 MiB.")
    return result


def get_manager(hass):
    key = f"{DOMAIN}.backup"
    if key not in hass.data:
        hass.data[key] = BackupManager(hass)
    return hass.data[key]


class BackupManager:
    def __init__(self, hass):
        self.hass = hass
        self.exclusive = asyncio.Lock()
        self.readers = 0
        self.idle = asyncio.Event()
        self.idle.set()
        self.blocked = False
        self.recovery_failed = False
        self.journal = Store(hass, 1, f"{DOMAIN}.restore_journal")
        self.fallback = Store(hass, 1, f"{DOMAIN}.backup_previous")
        self.settings = Store(hass, 1, f"{DOMAIN}.restore_settings")
        self.staged = None
        self.generation = uuid4().hex
        self.restore_id = ""
        self.connections = {}

    @asynccontextmanager
    async def activity(self):
        if self.blocked:
            raise HomeAssistantError(
                "Wiederherstellung unvollständig. Bitte Home Assistant zur Wiederherstellung neu starten."
                if self.recovery_failed
                else "Datensicherung/Wiederherstellung läuft. Bitte später erneut versuchen."
            )
        self.readers += 1
        self.idle.clear()
        try:
            yield
        finally:
            self.readers -= 1
            if not self.readers:
                self.idle.set()

    @asynccontextmanager
    async def maintenance(self):
        async with self.exclusive:
            if self.blocked:
                raise HomeAssistantError(
                    "Eine unvollständige Wiederherstellung muss zuerst durch einen HA-Neustart zurückgesetzt werden."
                )
            self.blocked = True
            try:
                await self.idle.wait()
                async with AsyncExitStack() as stack:
                    for entry in self.entries():
                        await stack.enter_async_context(entry.runtime_data.lock)
                    lock = self.hass.data.setdefault(
                        f"{DOMAIN}.supermarkets_lock", asyncio.Lock()
                    )
                    await stack.enter_async_context(lock)
                    yield
            finally:
                self.blocked = self.recovery_failed

    def entries(self):
        entries = [
            entry
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if CONF_SOURCE in entry.data
        ]
        if any(getattr(entry, "runtime_data", None) is None for entry in entries):
            raise HomeAssistantError(
                "Bitte zuerst alle Einkaufszettel-Listen in HA laden."
            )
        return sorted(entries, key=lambda entry: entry.entry_id)

    def targets(self):
        return [
            {
                "entry_id": entry.entry_id,
                "name": entry.data["name"],
                "source_entity_id": entry.data[CONF_SOURCE],
                "source_paused": entry.options.get("source_paused", False),
            }
            for entry in self.entries()
        ]

    async def capture(self):
        catalog = await Store(self.hass, 1, f"{DOMAIN}.supermarkets").async_load()
        manifest = await asyncio.to_thread(
            (Path(__file__).parent / "manifest.json").read_text, encoding="utf-8"
        )
        version = json.loads(manifest)["version"]
        payload = {
            "format": FORMAT,
            "schema_version": 1,
            "app_version": version,
            "created_at": datetime.now(UTC).isoformat(),
            "catalog": validate_catalog(catalog if catalog is not None else {}),
            "lists": [],
        }
        for entry in self.entries():
            data = entry.runtime_data
            payload["lists"].append(
                {
                    "entry_id": entry.entry_id,
                    "name": entry.data["name"],
                    "source_entity_id": entry.data[CONF_SOURCE],
                    "options": {
                        key: entry.options[key]
                        for key in (
                            "enabled",
                            "auto_shopping_threshold",
                            "source_paused",
                        )
                        if key in entry.options
                    },
                    "snapshot": {
                        "items": [item.to_dict() for item in data.items],
                        "sync": deepcopy(data.sync),
                        "restore_id": getattr(data, "restore_id", ""),
                    },
                }
            )
        validate_payload(payload)
        return payload

    async def backup(self):
        async with self.maintenance():
            return encode_backup(await self.capture())

    def prepare(self, payload, mapping):
        validate_payload(payload)
        entries = {entry.entry_id: entry for entry in self.entries()}
        old_ids = {record["entry_id"] for record in payload["lists"]}
        if (
            not isinstance(mapping, dict)
            or set(mapping) != old_ids
            or any(not isinstance(value, str) for value in mapping.values())
            or len(set(mapping.values())) != len(mapping)
            or set(mapping.values()) != set(entries)
        ):
            raise ValueError(
                "Jede gesicherte Liste muss genau einer eingerichteten App-Liste zugeordnet sein. Für vollständiges Ersetzen müssen alle App-Listen zugeordnet werden. Fehlende Listen bitte zuerst unter „Listen verwalten“ einrichten."
            )
        result = deepcopy(payload)
        restore_id = uuid4().hex
        for record in result["lists"]:
            entry = entries[mapping[record["entry_id"]]]
            if (
                entry.entry_id != record["entry_id"]
                or entry.data[CONF_SOURCE] != record["source_entity_id"]
            ):
                snapshot = record["snapshot"]
                for item in [*snapshot["items"], *snapshot["sync"]["deleted"].values()]:
                    item["source_uid"] = None
                snapshot["sync"]["source"] = {}
                snapshot["sync"]["creates"] = {}
            record["entry_id"] = entry.entry_id
            record["source_entity_id"] = entry.data[CONF_SOURCE]
            record["options"]["source_paused"] = True
            record["snapshot"]["restore_id"] = restore_id
        for catalog in result["catalog"]["catalogs"].values():
            for product in catalog["products"]:
                usage = product.get("usage")
                if usage:
                    remapped = {}
                    for key, stats in usage.items():
                        target = mapping.get(key, key)
                        if target in remapped:
                            raise ValueError(
                                "Statistik-Listenkennungen kollidieren bei dieser Zuordnung."
                            )
                        remapped[target] = stats
                    product["usage"] = remapped
            for field in ("product_events", "product_operations"):
                remapped = {}
                for key, value in catalog[field].items():
                    prefix, separator, suffix = key.partition(":")
                    target = f"{mapping.get(prefix, prefix)}{separator}{suffix}"
                    if target in remapped:
                        raise ValueError(
                            "Katalog-Operationskennungen kollidieren bei dieser Zuordnung."
                        )
                    remapped[target] = value
                catalog[field] = remapped
        result["catalog"] = validate_catalog(result["catalog"])
        validate_payload(result)
        return result

    def apply_settings(self, records):
        entries = {
            entry.entry_id: entry
            for entry in self.hass.config_entries.async_entries(DOMAIN)
        }
        for record in records:
            entry = entries.get(record["entry_id"])
            if (
                entry is None
                or entry.data.get(CONF_SOURCE) != record["source_entity_id"]
            ):
                continue
            if entry.options.get("_restore_settings_id") == record["token"]:
                continue
            self.hass.config_entries.async_update_entry(
                entry,
                title=record["name"],
                data={**entry.data, "name": record["name"]},
                options={**record["options"], "_restore_settings_id": record["token"]},
            )

    async def resume(self, ids):
        async with self.maintenance():
            entries = self.entries()
            valid = {entry.entry_id for entry in entries}
            if (
                not isinstance(ids, list)
                or not ids
                or any(not isinstance(uid, str) or uid not in valid for uid in ids)
            ):
                raise ValueError("Bitte mindestens eine gültige Liste auswählen.")
            records = [
                {
                    "entry_id": entry.entry_id,
                    "source_entity_id": entry.data[CONF_SOURCE],
                    "name": entry.data["name"],
                    "options": {
                        **entry.options,
                        "source_paused": False
                        if entry.entry_id in ids
                        else entry.options.get("source_paused", False),
                    },
                    "token": uuid4().hex,
                }
                for entry in entries
            ]
            await self.settings.async_save(
                {"restore_id": self.restore_id, "entries": records}
            )
            self.apply_settings(records)

    async def write(self, payload, *, runtime=True):
        entries = {
            entry.entry_id: entry
            for entry in self.hass.config_entries.async_entries(DOMAIN)
        }
        for record in payload["lists"]:
            entry = entries.get(record["entry_id"])
            if (
                entry is None
                or entry.data.get(CONF_SOURCE) != record["source_entity_id"]
            ):
                raise ValueError(
                    "Die HA-Listenkonfiguration hat sich geändert. Wiederherstellung abgebrochen."
                )
        settings = [
            {
                "entry_id": record["entry_id"],
                "source_entity_id": record["source_entity_id"],
                "name": record["name"],
                "options": {
                    **entries[record["entry_id"]].options,
                    "enabled": True,
                    "auto_shopping_threshold": 0,
                    "source_paused": False,
                    **record["options"],
                },
                "token": uuid4().hex,
            }
            for record in payload["lists"]
        ]
        # HA defers config-entry saves. Replay these durable settings after a crash.
        restore_id = (
            payload["lists"][0]["snapshot"]["restore_id"]
            if payload["lists"]
            else self.restore_id
        )
        await self.settings.async_save({"restore_id": restore_id, "entries": settings})
        await Store(self.hass, 1, f"{DOMAIN}.supermarkets").async_save(
            payload["catalog"]
        )
        for record in payload["lists"]:
            entry = entries[record["entry_id"]]
            snapshot = record["snapshot"]
            await Store(self.hass, 1, f"{DOMAIN}.{entry.entry_id}").async_save(snapshot)
            if runtime and getattr(entry, "runtime_data", None) is not None:
                entry.runtime_data.items = load_items(snapshot)
                entry.runtime_data.sync = load_sync_state(snapshot["sync"])
                entry.runtime_data.restore_id = snapshot["restore_id"]
                entry.runtime_data.source_error = None
        self.apply_settings(settings)
        self.restore_id = restore_id

    async def restore(self, payload, mapping):
        async with self.maintenance():
            replacement = self.prepare(payload, mapping)
            before = await self.capture()
            await self.fallback.async_save(
                {"backup": encode_backup(before).decode("utf-8")}
            )
            self.recovery_failed = True
            try:
                await self.journal.async_save({"before": before})
                await self.write(replacement)
                await self.journal.async_save(None)
                self.generation = uuid4().hex
                self.recovery_failed = False
            except (
                HomeAssistantError,
                OSError,
                ValueError,
                TypeError,
                asyncio.CancelledError,
            ):
                _LOGGER.exception("Restore failed; rolling back all Easy Shopping data")
                self.recovery_failed = True
                try:
                    await self.write(before)
                    await self.journal.async_save(None)
                    self.recovery_failed = False
                except (HomeAssistantError, OSError, ValueError, TypeError) as err:
                    _LOGGER.exception(
                        "Restore rollback failed; restart HA to recover the journal"
                    )
                    # Keep writes blocked until startup recovery has succeeded.
                    raise HomeAssistantError(
                        "Wiederherstellung und Rücksetzen fehlgeschlagen. Keine weiteren Änderungen vornehmen; Home Assistant neu starten."
                    ) from err
                raise

    async def recover(self):
        journal = await self.journal.async_load()
        if journal is not None:
            self.blocked = True
            validate_payload(journal["before"])
            await self.write(journal["before"], runtime=False)
            await self.journal.async_save(None)
            self.blocked = False
            _LOGGER.warning(
                "Interrupted Easy Shopping restore was rolled back from its journal"
            )
        settings = await self.settings.async_load()
        if settings is not None:
            self.restore_id = settings["restore_id"]
            self.apply_settings(settings["entries"])


def guard_command(command):
    """Join the async handler, not HA's synchronous scheduling wrapper."""
    handler = getattr(command, "__wrapped__", command)

    @websocket_api.async_response
    @wraps(command)
    async def guarded(hass, connection, msg):
        try:
            async with get_manager(hass).activity():
                manager = get_manager(hass)
                generation = manager.connections.setdefault(
                    connection, manager.generation
                )
                # HA connections cannot be weak-referenced; release them on disconnect.
                connection.subscriptions.setdefault(
                    f"{DOMAIN}.restore_generation",
                    lambda: manager.connections.pop(connection, None),
                )
                action = msg["type"].rsplit("/", 1)[-1]
                if generation != manager.generation and not action.startswith("get_"):
                    connection.send_error(
                        msg["id"],
                        "restore_conflict",
                        "Daten wurden wiederhergestellt. Bitte die App neu laden; alte Offline-Änderungen werden nicht automatisch übernommen.",
                    )
                    return
                await handler(hass, connection, msg)
        except HomeAssistantError as err:
            connection.send_error(msg["id"], "maintenance", str(err))

    return guarded
