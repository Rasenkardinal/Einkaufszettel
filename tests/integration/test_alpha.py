"""Exercise HA source discovery and app management without duplicate To-do lists."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.einkaufszettel.const import DOMAIN

SOURCE = "todo.alexa"


class SourceList(TodoListEntity):
    """Expose the source through HA's real To-do service."""

    _attr_name = "Alexa Long Shopping List"
    _attr_should_poll = False
    _attr_todo_items = [
        TodoItem(uid="source-1", summary="Milch", status=TodoItemStatus.NEEDS_ACTION),
        TodoItem(uid="source-2", summary="Brot", status=TodoItemStatus.NEEDS_ACTION),
        TodoItem(uid="source-3", summary="Eier", status=TodoItemStatus.COMPLETED),
    ]
    entity_id = SOURCE


@pytest.fixture
async def source(hass: HomeAssistant):
    assert await async_setup_component(hass, "todo", {})
    entity = SourceList()
    await hass.data["todo"].async_add_entities([entity])
    return entity


async def setup_app(hass: HomeAssistant, *, with_source=False):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Einkaufszettel",
        data={
            "name": "Einkaufszettel",
            **({"source_entity_id": SOURCE} if with_source else {}),
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def command(client, message_id, command_type, **data):
    await client.send_json(
        {"id": message_id, "type": f"{DOMAIN}/{command_type}", **data}
    )
    result = await client.receive_json()
    assert result["id"] == message_id
    return result


async def test_user_flow_creates_hub_without_source_selection(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["data_schema"].schema
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"name": "Einkaufszettel"}
    await hass.async_block_till_done()
    assert not hass.states.async_all("todo")


async def test_backup_http_restore_and_websocket_generation(
    hass, source, hass_client, hass_ws_client
):
    """Use HA's real authenticated view, slotted connection and command decorators."""
    entry = await setup_app(hass, with_source=True)
    websocket = await hass_ws_client(hass)
    before = await command(websocket, 1, "get_list", entry_id=entry.entry_id)
    client = await hass_client()
    download = await client.get(f"/api/{DOMAIN}/backup")
    assert download.status == 200
    assert download.headers["Cache-Control"] == "no-store"
    raw = await download.read()
    assert json.loads(raw)["payload"]["lists"][0]["entry_id"] == entry.entry_id
    preview = await client.post(f"/api/{DOMAIN}/backup/preview", data=raw)
    assert preview.status == 200
    token = (await preview.json())["token"]
    changed = await command(
        websocket,
        2,
        "apply_operation",
        entry_id=entry.entry_id,
        operation_id="before-restore",
        action="add_item",
        uid="new-item",
        changes={"summary": "Neu"},
    )
    assert changed["success"]
    restored = await client.post(
        f"/api/{DOMAIN}/backup/restore",
        json={
            "token": token,
            "mapping": {entry.entry_id: entry.entry_id},
            "confirm": True,
        },
    )
    assert restored.status == 200
    assert entry.options["source_paused"]
    snapshot = await command(websocket, 3, "get_list", entry_id=entry.entry_id)
    assert snapshot["result"]["items"] == before["result"]["items"]
    assert snapshot["result"]["restore_id"]
    stale = await command(
        websocket,
        4,
        "apply_operation",
        entry_id=entry.entry_id,
        operation_id="old-offline",
        action="delete_item",
        uid=before["result"]["items"][0]["uid"],
        changes={},
    )
    assert not stale["success"] and stale["error"]["code"] == "restore_conflict"
    fallback = await client.get(f"/api/{DOMAIN}/backup/previous")
    assert fallback.status == 200
    previous = json.loads(await fallback.read())
    assert len(previous["payload"]["lists"][0]["snapshot"]["items"]) == 3
    resumed = await client.post(
        f"/api/{DOMAIN}/backup/resume",
        json={"entry_ids": [entry.entry_id], "confirm": True},
    )
    assert resumed.status == 200
    assert not entry.options["source_paused"]
    await websocket.close()
    await hass.async_block_till_done()


async def test_backup_http_rejects_nonadmin_and_unauthenticated(
    hass, source, hass_client, hass_read_only_user
):
    await setup_app(hass, with_source=True)
    client = await hass_client()
    refresh = await hass.auth.async_create_refresh_token(
        hass_read_only_user, "https://example.test"
    )
    token = hass.auth.async_create_access_token(refresh)
    headers = {"Authorization": f"Bearer {token}"}
    for action in ("", "/status", "/previous"):
        response = await client.get(f"/api/{DOMAIN}/backup{action}", headers=headers)
        assert response.status == 403
    for action in ("preview", "restore", "resume"):
        response = await client.post(
            f"/api/{DOMAIN}/backup/{action}", data=b"{}", headers=headers
        )
        assert response.status == 403
    response = await client.get(
        f"/api/{DOMAIN}/backup", headers={"Authorization": "Bearer invalid"}
    )
    assert response.status == 401


async def test_backup_upload_streams_files_larger_than_default_json_limit(
    hass, source, hass_client
):
    from custom_components.einkaufszettel.backup import encode_backup, read_backup

    await setup_app(hass, with_source=True)
    client = await hass_client()
    response = await client.get(f"/api/{DOMAIN}/backup")
    payload = read_backup(await response.read())
    payload["lists"][0]["snapshot"]["items"][0]["description"] = "x" * (1024 * 1024 + 1)
    uploaded = await client.post(
        f"/api/{DOMAIN}/backup/preview", data=encode_backup(payload)
    )
    assert uploaded.status == 200
    assert (await uploaded.json())["lists"][0]["items"] == 2


async def test_discover_activate_alias_hide_and_reload(hass, source, hass_ws_client):
    await setup_app(hass)
    client = await hass_ws_client(hass)
    discovered = await command(client, 1, "get_sources")
    assert discovered["success"]
    assert discovered["result"][0]["source_entity_id"] == SOURCE
    assert not discovered["result"][0]["enabled"]
    configured = await command(
        client,
        2,
        "configure_list",
        source_entity_id=SOURCE,
        name="Kaufland",
        enabled=True,
        auto_shopping_threshold=3,
    )
    assert configured["success"]
    entry_id = configured["result"]["entry_id"]
    await hass.async_block_till_done()
    lists = await command(client, 3, "get_lists")
    assert lists["result"] == [
        {
            "entry_id": entry_id,
            "name": "Kaufland",
            "source_entity_id": SOURCE,
            "auto_shopping_threshold": 3,
        }
    ]
    assert [state.entity_id for state in hass.states.async_all("todo")] == [SOURCE]
    assert source.name == "Alexa Long Shopping List"
    snapshot = await command(client, 4, "get_list", entry_id=entry_id)
    assert snapshot["result"]["auto_shopping_threshold"] == 3
    assert [item["summary"] for item in snapshot["result"]["items"]] == [
        "Milch",
        "Brot",
    ]
    hidden = await command(
        client,
        5,
        "configure_list",
        source_entity_id=SOURCE,
        name="Kurzname",
        enabled=False,
    )
    assert hidden["success"]
    assert (await command(client, 6, "get_lists"))["result"] == []
    entry = hass.config_entries.async_get_entry(entry_id)
    assert await hass.config_entries.async_reload(entry_id)
    assert entry.data["name"] == "Kurzname"
    assert entry.options["enabled"] is False
    assert entry.options["auto_shopping_threshold"] == 3
    assert len(entry.runtime_data.items) == 2


async def test_app_mutations_do_not_write_to_source(hass, source, hass_ws_client):
    entry = await setup_app(hass, with_source=True)
    client = await hass_ws_client(hass)
    uid = entry.runtime_data.items[0].uid
    result = await command(
        client,
        1,
        "update_item",
        entry_id=entry.entry_id,
        uid=uid,
        summary="Meine Milch",
        status="completed",
    )
    assert result["success"]
    assert source.todo_items[0].summary == "Milch"
    assert source.todo_items[0].status == TodoItemStatus.NEEDS_ACTION
    assert await hass.config_entries.async_unload(entry.entry_id)
    hass.states.async_set(SOURCE, "unavailable")
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.runtime_data.items[0].summary == "Meine Milch"
    assert entry.runtime_data.items[0].status == "completed"


async def test_failed_save_does_not_publish_or_mutate(hass, source, hass_ws_client):
    entry = await setup_app(hass, with_source=True)
    client = await hass_ws_client(hass)
    uid = entry.runtime_data.items[0].uid
    with patch.object(
        entry.runtime_data.store, "async_save", side_effect=OSError("disk full")
    ):
        result = await command(
            client,
            1,
            "update_item",
            entry_id=entry.entry_id,
            uid=uid,
            status="completed",
        )
    assert not result["success"]
    assert entry.runtime_data.items[0].status == "needs_action"


async def test_corrupt_storage_does_not_reimport(hass, source):
    entry = await setup_app(hass, with_source=True)
    assert await hass.config_entries.async_unload(entry.entry_id)
    with (
        patch(
            "custom_components.einkaufszettel.Store.async_load",
            return_value={"items": [{"summary": "broken"}]},
        ),
        patch(
            "custom_components.einkaufszettel.Store.async_save", new_callable=AsyncMock
        ) as save,
        patch(
            "custom_components.einkaufszettel.async_read_source", new_callable=AsyncMock
        ) as read,
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        save.assert_not_called()
        read.assert_not_called()
