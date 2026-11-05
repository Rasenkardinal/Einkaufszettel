"""Exercise backup transactions, crash recovery and authenticated file transport."""

import asyncio
import importlib
import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import web
from test_lifecycle import integration as lifecycle_integration

integration = lifecycle_integration


@pytest.fixture
def backup_env(integration):
    env = integration
    package = env.package.__name__
    env.backup = importlib.import_module(f"{package}.backup")
    env.http = importlib.import_module(f"{package}.backup_http")
    env.catalog = importlib.import_module(f"{package}.catalog")
    env.sync = importlib.import_module(f"{package}.sync")
    env.manager = env.backup.get_manager(env.hass)
    env.entry.runtime_data = env.package.EinkaufszettelData(
        env.store,
        [
            env.model.ShoppingItem(
                uid="item",
                summary="Milch",
                source_uid="source",
                metadata={"image": "data:image/png;base64,eA==", "quantity": "2"},
            )
        ],
    )
    env.entry.options = {"auto_shopping_threshold": 3, "enabled": False}
    env.entry.domain = "einkaufszettel"
    env.hass.config_entries.async_entries.return_value = [env.entry]
    env.hass.config_entries.async_get_entry.return_value = env.entry
    env.persisted = {
        "einkaufszettel.supermarkets": env.catalog.validate_catalog(
            {
                "supermarkets": [{"id": "market", "name": "Markt"}],
                "products": [
                    {
                        "key": "milch",
                        "name": "Milch",
                        "category_id": None,
                        "usage": {
                            env.entry.entry_id: {
                                "added": 4,
                                "last_added": 1000,
                                "weeks": {"2026-W43": 4},
                            }
                        },
                    }
                ],
            }
        )
    }

    def update(entry, **changes):
        for key, value in changes.items():
            setattr(entry, key, value)

    env.hass.config_entries.async_update_entry.side_effect = update
    # Store instances share real serialized values, not mutable mock return objects.
    for key in ("einkaufszettel.supermarkets",):
        env.stores.setdefault(
            key, SimpleNamespace(async_load=AsyncMock(), async_save=AsyncMock())
        )
    for key, store in env.stores.items():

        async def load(key=key):
            return deepcopy(env.persisted.get(key))

        async def save(value, key=key):
            env.persisted[key] = deepcopy(value)

        store.async_load.side_effect = load
        store.async_save.side_effect = save
    return env


async def test_backup_exact_roundtrip_and_paused_restore(backup_env):
    env = backup_env
    raw = await env.manager.backup()
    payload = env.backup.read_backup(raw)
    record = payload["lists"][0]
    assert record["snapshot"]["items"][0]["metadata"]["image"].startswith("data:")
    assert record["options"]["auto_shopping_threshold"] == 3
    before = deepcopy(payload)
    env.entry.runtime_data.items = []
    await env.manager.restore(payload, {env.entry.entry_id: env.entry.entry_id})
    assert payload == before
    assert env.entry.runtime_data.items[0].summary == "Milch"
    assert env.entry.options["source_paused"] is True
    assert env.entry.options["enabled"] is False
    assert env.entry.runtime_data.restore_id
    assert env.persisted["einkaufszettel.test-entry"]["restore_id"]
    assert env.persisted["einkaufszettel.restore_journal"] is None
    fallback = env.backup.read_backup(
        env.persisted["einkaufszettel.backup_previous"]["backup"].encode()
    )
    assert fallback["lists"][0]["snapshot"]["items"] == []
    assert not env.manager.blocked


async def test_restore_remaps_statistics_and_unlinks_foreign_source_ids(backup_env):
    env = backup_env
    payload = env.backup.read_backup(await env.manager.backup())
    catalog = payload["catalog"]["catalogs"]["supermarket"]
    catalog["product_events"]["test-entry:added:source:source"] = "milch"
    payload["catalog"] = env.catalog.validate_catalog(payload["catalog"])
    env.entry.entry_id = "new-entry"
    env.entry.data["source_entity_id"] = "todo.new"
    prepared = env.manager.prepare(payload, {"test-entry": "new-entry"})
    assert prepared["lists"][0]["snapshot"]["items"][0]["source_uid"] is None
    restored_catalog = prepared["catalog"]["catalogs"]["supermarket"]
    assert restored_catalog["products"][0]["usage"]["new-entry"]["added"] == 4
    assert (
        restored_catalog["product_events"]["new-entry:added:source:source"] == "milch"
    )
    env.backup.read_backup(env.backup.encode_backup(prepared))


@pytest.mark.parametrize(
    "mapping", [None, {}, {"test-entry": "missing"}, {"extra": "test-entry"}]
)
async def test_bad_mapping_makes_no_writes(backup_env, mapping):
    env = backup_env
    payload = env.backup.read_backup(await env.manager.backup())
    before = deepcopy(env.persisted)
    with pytest.raises(ValueError, match="zugeordnet"):
        await env.manager.restore(payload, mapping)
    assert env.persisted == before
    assert not env.manager.blocked


async def test_unloaded_list_blocks_backup_without_writes(backup_env):
    env = backup_env
    del env.entry.runtime_data
    with pytest.raises(env.error, match="laden"):
        await env.manager.backup()
    assert not env.manager.blocked


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.update(schema_version=2),
        lambda payload: payload.update(created_at="2026-01-01"),
        lambda payload: payload["lists"][0]["options"].update(
            auto_shopping_threshold=True
        ),
        lambda payload: payload["lists"][0]["snapshot"]["items"].append(
            deepcopy(payload["lists"][0]["snapshot"]["items"][0])
        ),
        lambda payload: payload["lists"][0]["snapshot"]["items"][0].update(
            unknown=True
        ),
        lambda payload: payload["lists"][0]["snapshot"]["items"][0]["metadata"].update(
            catalog_id="missing"
        ),
        lambda payload: payload["lists"][0]["snapshot"]["sync"].update(revision=-1),
    ],
)
async def test_invalid_backup_rejected_before_restore(backup_env, mutation):
    env = backup_env
    payload = env.backup.read_backup(await env.manager.backup())
    mutation(payload)
    with pytest.raises(ValueError):
        env.backup.encode_backup(payload)


async def test_bad_checksum_duplicate_keys_and_size_rejected(backup_env, monkeypatch):
    env = backup_env
    raw = await env.manager.backup()
    with pytest.raises(ValueError, match="Prüfsumme"):
        env.backup.read_backup(raw.replace(b"Milch", b"Brot"))
    with pytest.raises(ValueError, match="Doppeltes"):
        env.backup.read_backup(b'{"payload":{},"payload":{},"sha256":""}')
    with pytest.raises(ValueError):
        env.backup.read_backup(b"[" * 2000)
    monkeypatch.setattr(env.backup, "MAX_BACKUP_BYTES", 10)
    with pytest.raises(ValueError, match="100 MiB"):
        env.backup.read_backup(raw)


async def test_partial_write_failure_rolls_back_every_store(backup_env):
    env = backup_env
    payload = env.backup.read_backup(await env.manager.backup())
    payload["lists"][0]["name"] = "Neu"
    payload["lists"][0]["snapshot"]["items"] = []
    failed = False
    original_save = env.store.async_save.side_effect

    async def fail_once(value):
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("disk full")
        await original_save(value)

    env.store.async_save.side_effect = fail_once
    with pytest.raises(OSError, match="disk full"):
        await env.manager.restore(payload, {"test-entry": "test-entry"})
    assert env.entry.runtime_data.items[0].summary == "Milch"
    assert env.entry.data["name"] == "Einkaufszettel"
    assert env.entry.options["auto_shopping_threshold"] == 3
    assert env.persisted["einkaufszettel.restore_journal"] is None
    assert not env.manager.blocked


async def test_failed_rollback_blocks_writes_until_startup_recovery(backup_env):
    env = backup_env
    payload = env.backup.read_backup(await env.manager.backup())
    original_save = env.store.async_save.side_effect
    env.store.async_save.side_effect = OSError("disk full")
    with pytest.raises(env.error, match="neu starten"):
        await env.manager.restore(payload, {"test-entry": "test-entry"})
    assert env.manager.blocked
    assert (
        env.persisted["einkaufszettel.restore_journal"]["before"]["lists"]
        == payload["lists"]
    )
    with pytest.raises(env.error):
        async with env.manager.activity():
            pytest.fail("Writes must remain blocked")
    env.store.async_save.side_effect = original_save
    restarted = env.backup.BackupManager(env.hass)
    await restarted.recover()
    assert env.persisted["einkaufszettel.restore_journal"] is None
    assert not restarted.blocked


async def test_cancelled_restore_rolls_back_and_propagates_cancellation(backup_env):
    env = backup_env
    payload = env.backup.read_backup(await env.manager.backup())
    original_save = env.store.async_save.side_effect
    calls = 0

    async def cancelled(value):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise asyncio.CancelledError
        await original_save(value)

    env.store.async_save.side_effect = cancelled
    with pytest.raises(asyncio.CancelledError):
        await env.manager.restore(payload, {"test-entry": "test-entry"})
    assert env.entry.runtime_data.items[0].summary == "Milch"
    assert not env.manager.blocked


async def test_deferred_config_settings_and_resume_survive_restart(backup_env):
    env = backup_env
    payload = env.backup.read_backup(await env.manager.backup())
    payload["lists"][0]["name"] = "Wiederhergestellt"
    await env.manager.restore(payload, {"test-entry": "test-entry"})
    # Emulate HA losing its delayed config_entries save on abrupt shutdown.
    env.entry.options = {}
    env.entry.data["name"] = "Alter Name"
    restarted = env.backup.BackupManager(env.hass)
    await restarted.recover()
    assert env.entry.data["name"] == "Wiederhergestellt"
    assert env.entry.options["source_paused"]
    assert env.entry.options["auto_shopping_threshold"] == 3
    old_options = deepcopy(env.entry.options)
    await restarted.resume(["test-entry"])
    assert not env.entry.options["source_paused"]
    env.entry.options = old_options
    await env.backup.BackupManager(env.hass).recover()
    assert not env.entry.options["source_paused"]


async def test_new_lists_after_restore_share_durable_epoch(backup_env, monkeypatch):
    env = backup_env
    payload = env.backup.read_backup(await env.manager.backup())
    await env.manager.restore(payload, {"test-entry": "test-entry"})
    restarted = env.backup.BackupManager(env.hass)
    await restarted.recover()
    env.hass.data["einkaufszettel.backup"] = restarted
    extra = SimpleNamespace(
        entry_id="new-list",
        domain="einkaufszettel",
        data={"name": "Neu", "source_entity_id": "todo.new"},
        options={},
    )
    env.hass.config_entries.async_entries.return_value = [env.entry, extra]
    monkeypatch.setattr(env.package, "async_read_source", AsyncMock(return_value=[]))
    assert await env.package.async_setup_entry(env.hass, extra)
    assert extra.runtime_data.restore_id == env.entry.runtime_data.restore_id
    assert (
        env.stores["einkaufszettel.new-list"].async_save.call_args.args[0]["restore_id"]
        == restarted.restore_id
    )
    exported = env.backup.read_backup(await restarted.backup())
    assert len(exported["lists"]) == 2
    with pytest.raises(ValueError, match="zugeordnet"):
        restarted.prepare(
            exported, {"test-entry": "test-entry", "new-list": "test-entry"}
        )


async def test_maintenance_waits_for_active_writes_and_rejects_new_ones(backup_env):
    env = backup_env
    async with env.manager.activity():
        task = asyncio.create_task(env.manager.backup())
        await asyncio.sleep(0)
        assert env.manager.blocked and not task.done()
        with pytest.raises(env.error):
            async with env.manager.activity():
                pytest.fail("New writes must be refused")
    env.backup.read_backup(await task)
    assert not env.manager.blocked


async def test_stale_operations_rejected_and_restore_epoch_persisted(backup_env):
    env = backup_env
    payload = env.backup.read_backup(await env.manager.backup())
    await env.manager.restore(payload, {"test-entry": "test-entry"})
    connection = Mock()
    msg = {
        "id": 1,
        "type": "einkaufszettel/apply_operation",
        "entry_id": "test-entry",
        "operation_id": "old-operation",
        "action": "update_item",
        "uid": "item",
        "changes": {"summary": "Alt"},
    }
    await env.websocket.websocket_apply_operation(env.hass, connection, msg)
    assert connection.send_error.call_args.args[1] == "restore_conflict"
    assert env.entry.runtime_data.items[0].summary == "Milch"
    msg["restore_id"] = env.entry.runtime_data.restore_id
    await env.websocket.websocket_apply_operation(env.hass, connection, msg)
    assert env.entry.runtime_data.items[0].summary == "Alt"
    assert env.persisted["einkaufszettel.test-entry"]["restore_id"] == msg["restore_id"]


async def test_paused_sources_cannot_sync_copy_or_resolve(backup_env):
    env = backup_env
    env.entry.options["source_paused"] = True
    source_sync = importlib.import_module(f"{env.package.__name__}.source_sync")
    assert not await source_sync.synchronize_source(env.hass, env.entry)
    with pytest.raises(env.error, match="gesperrt"):
        await source_sync.resolve_source_conflict(
            env.hass, env.entry, "item", "", "retry"
        )
    button = env.button.CopySourceButton(env.entry)
    button.hass = env.hass
    with pytest.raises(env.error, match="gesperrt"):
        await button.async_press()
    connection = Mock()
    await env.websocket.websocket_copy_source(
        env.hass, connection, {"id": 1, "entry_id": "test-entry"}
    )
    assert connection.send_error.call_args.args[1] == "source_paused"
    env.hass.services.async_call.assert_not_called()


def http_request(env, data=b"", *, admin=True, user="admin"):
    class Request(dict):
        app = {env.http.KEY_HASS: env.hass}

    async def chunks(size):
        for offset in range(0, len(data), size):
            yield data[offset : offset + size]

    request = Request(hass_user=SimpleNamespace(is_admin=admin, id=user))
    request.content = SimpleNamespace(iter_chunked=chunks)
    return request


@pytest.mark.parametrize(
    ("method", "action"),
    [
        ("get", None),
        ("get", "status"),
        ("get", "previous"),
        ("post", "preview"),
        ("post", "restore"),
        ("post", "resume"),
    ],
)
async def test_every_file_endpoint_requires_admin(backup_env, method, action):
    env = backup_env
    view = env.http.BackupView()
    with pytest.raises(web.HTTPForbidden):
        await getattr(view, method)(http_request(env, admin=False), action)


async def test_http_preview_restore_fallback_and_resume(backup_env):
    env = backup_env
    view = env.http.BackupView()
    download = await view.get(http_request(env))
    assert download.status == 200 and download.headers["Cache-Control"] == "no-store"
    preview = await view.post(http_request(env, download.body), "preview")
    info = json.loads(preview.body)
    assert info["lists"][0]["items"] == 1 and len(info["targets"]) == 1
    command = {
        "token": info["token"],
        "mapping": {"test-entry": "test-entry"},
        "confirm": True,
    }
    raw = json.dumps(command).encode()
    wrong_user = await view.post(http_request(env, raw, user="another"), "restore")
    assert wrong_user.status == 400
    restored = await view.post(http_request(env, raw), "restore")
    assert restored.status == 200 and env.entry.options["source_paused"]
    assert restored.headers["Cache-Control"] == "no-store"
    assert (await view.post(http_request(env, raw), "restore")).status == 400
    previous = await view.get(http_request(env), "previous")
    env.backup.read_backup(previous.body)
    resumed = await view.post(
        http_request(env, b'{"confirm":true,"entry_ids":["test-entry"]}'), "resume"
    )
    assert resumed.status == 200 and not env.entry.options["source_paused"]


async def test_preview_expiry_bad_json_and_upload_limit(backup_env, monkeypatch):
    env = backup_env
    view = env.http.BackupView()
    preview = await view.post(http_request(env, await env.manager.backup()), "preview")
    token = json.loads(preview.body)["token"]
    env.manager.staged["expires"] = 0
    response = await view.post(
        http_request(env, json.dumps({"token": token, "confirm": True}).encode()),
        "restore",
    )
    assert response.status == 400
    assert (await view.post(http_request(env, b"not-json"), "preview")).status == 400
    monkeypatch.setattr(env.http, "MAX_BACKUP_BYTES", 10)
    assert (await view.post(http_request(env, b"x" * 11), "preview")).status == 400


async def test_old_websocket_connections_must_reload_after_restore(backup_env):
    env = backup_env
    handler = AsyncMock()
    handler.__name__ = "command"
    guarded = env.backup.guard_command(handler)

    class Connection:
        __slots__ = ("send_error", "subscriptions")

    connection = Connection()
    connection.subscriptions = {}
    connection.send_error = Mock()
    message = {"id": 1, "type": "einkaufszettel/save_category"}
    await guarded(env.hass, connection, message)
    handler.assert_awaited_once()
    env.manager.generation = "restored"
    await guarded(env.hass, connection, message)
    handler.assert_awaited_once()
    assert connection.send_error.call_args.args[1] == "restore_conflict"
    await guarded(env.hass, connection, {**message, "type": "einkaufszettel/get_list"})
    assert handler.await_count == 2
    connection.subscriptions["einkaufszettel.restore_generation"]()
    assert connection not in env.manager.connections


async def test_options_flow_links_to_admin_page_without_changing_options(backup_env):
    flow = backup_env.config_flow.EinkaufszettelOptionsFlow()
    result = await flow.async_step_init()
    assert result["description_placeholders"]["backup_url"] == "/einkaufszettel_backup"
    assert (await flow.async_step_init({}))["type"] == "abort"
