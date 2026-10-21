"""Test our lifecycle logic with explicit HA boundary doubles, not a HA runtime."""

import asyncio
import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

ROOT = Path(__file__).parents[2] / "custom_components" / "einkaufszettel"


@pytest.fixture
def integration(monkeypatch):
    """Load actual integration code against minimal external API boundaries."""

    def module(name, **attributes):
        value = ModuleType(name)
        value.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, value)
        return value

    class HAError(Exception):
        pass

    class NotReady(HAError):
        pass

    class Generic:
        def __class_getitem__(cls, key):
            return cls

    class Entity:
        def async_write_ha_state(self):
            self.writes = getattr(self, "writes", 0) + 1

    from dataclasses import dataclass
    from enum import IntFlag, StrEnum

    class Status(StrEnum):
        NEEDS_ACTION = "needs_action"
        COMPLETED = "completed"

    class Features(IntFlag):
        UPDATE_TODO_ITEM = 1
        SET_DESCRIPTION_ON_ITEM = 2
        SET_DUE_DATE_ON_ITEM = 4
        SET_DUE_DATETIME_ON_ITEM = 8
        CREATE_TODO_ITEM = 16
        DELETE_TODO_ITEM = 32

    @dataclass
    class Item:
        uid: str
        summary: str
        status: Status
        description: str | None = None
        due: object = None

    stores = {}

    class Store(Generic):
        def __new__(cls, _hass, _version, key):
            return stores.setdefault(
                key,
                SimpleNamespace(
                    async_load=AsyncMock(return_value=None),
                    async_save=AsyncMock(),
                ),
            )

    module("homeassistant")
    module("homeassistant.config_entries", ConfigEntry=Generic)
    components = module("homeassistant.components")
    frontend = module(
        "homeassistant.components.frontend",
        async_register_built_in_panel=Mock(),
        async_remove_panel=Mock(),
    )
    components.frontend = frontend
    module(
        "homeassistant.components.http",
        StaticPathConfig=lambda *args, **kwargs: (args, kwargs),
    )
    websocket_api = module(
        "homeassistant.components.websocket_api",
        async_register_command=Mock(),
        async_response=lambda function: function,
        websocket_command=lambda schema: lambda function: function,
    )
    components.websocket_api = websocket_api
    persistent_notification = module(
        "homeassistant.components.persistent_notification",
        async_create=Mock(),
    )
    components.persistent_notification = persistent_notification
    module(
        "voluptuous",
        Required=lambda key: key,
        Optional=lambda key: key,
        In=lambda values: values,
    )
    module(
        "homeassistant.const",
        Platform=SimpleNamespace(TODO="todo", BUTTON="button"),
        CONF_NAME="name",
        STATE_UNAVAILABLE="unavailable",
        STATE_UNKNOWN="unknown",
    )
    module("homeassistant.core", HomeAssistant=object)
    module(
        "homeassistant.exceptions",
        HomeAssistantError=HAError,
        ConfigEntryNotReady=NotReady,
    )
    module("homeassistant.helpers")
    network = module(
        "homeassistant.helpers.network",
        NoURLAvailableError=type("NoURLAvailableError", (Exception,), {}),
        get_url=Mock(return_value="https://ha.example.test"),
    )
    module("homeassistant.helpers.storage", Store=Store)
    dispatcher = module(
        "homeassistant.helpers.dispatcher",
        async_dispatcher_connect=Mock(),
        async_dispatcher_send=Mock(),
    )
    module(
        "homeassistant.helpers.entity_registry",
        async_get=lambda hass: SimpleNamespace(async_get=lambda entity_id: None),
    )
    module(
        "homeassistant.helpers.entity_platform", AddConfigEntryEntitiesCallback=object
    )
    module("homeassistant.components.button", ButtonEntity=Entity)
    module(
        "homeassistant.components.todo",
        TodoItem=Item,
        TodoItemStatus=Status,
        TodoListEntity=Entity,
        TodoListEntityFeature=Features,
    )
    spec = importlib.util.spec_from_file_location(
        "einkaufszettel_boundary_test",
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    package = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, package)
    spec.loader.exec_module(package)
    todo = importlib.import_module(f"{spec.name}.todo")
    button = importlib.import_module(f"{spec.name}.button")
    model = importlib.import_module(f"{spec.name}.model")
    websocket = importlib.import_module(f"{spec.name}.websocket")
    hass = SimpleNamespace(
        states=SimpleNamespace(get=lambda entity_id: SimpleNamespace(state="1")),
        services=SimpleNamespace(
            async_call=AsyncMock(
                return_value={
                    "todo.alexa": {
                        "items": [
                            {"uid": "a", "summary": "Milch", "status": "needs_action"}
                        ]
                    }
                }
            )
        ),
        config_entries=SimpleNamespace(
            async_forward_entry_setups=AsyncMock(),
            async_unload_platforms=AsyncMock(return_value=True),
            async_entries=Mock(return_value=[]),
            async_get_entry=Mock(),
        ),
    )
    entry = SimpleNamespace(
        entry_id="test-entry",
        data={"source_entity_id": "todo.alexa", "name": "Einkaufszettel"},
    )
    yield SimpleNamespace(
        package=package,
        todo=todo,
        button=button,
        dispatcher=dispatcher,
        model=model,
        websocket=websocket,
        websocket_api=websocket_api,
        frontend=frontend,
        persistent_notification=persistent_notification,
        network=network,
        hass=hass,
        entry=entry,
        store=stores.setdefault(
            "einkaufszettel.test-entry",
            SimpleNamespace(
                async_load=AsyncMock(return_value=None), async_save=AsyncMock()
            ),
        ),
        stores=stores,
        error=HAError,
        not_ready=NotReady,
        Item=Item,
        Status=Status,
    )
    for name in list(sys.modules):
        if name.startswith(f"{spec.name}."):
            del sys.modules[name]


async def test_initial_import_persists_a_real_local_copy(integration):
    env = integration
    assert await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.assert_awaited_once_with(
        "todo",
        "get_items",
        {"entity_id": "todo.alexa", "status": ["needs_action"]},
        blocking=True,
        return_response=True,
    )
    saved = env.store.async_save.call_args.args[0]["items"]
    assert saved[0]["summary"] == "Milch"
    assert saved[0]["source_uid"] == "a"
    assert saved[0]["uid"] != "a"


@pytest.mark.parametrize(
    "items", [[], [{"uid": "local", "summary": "Milch", "status": "completed"}]]
)
async def test_reload_never_requires_source(integration, items):
    env = integration
    env.store.async_load.return_value = {"items": items}
    assert await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.assert_not_awaited()
    env.store.async_save.assert_not_awaited()
    assert [item.to_dict() for item in env.entry.runtime_data.items] == [
        env.model.ShoppingItem(
            value["uid"], value["summary"], value["status"]
        ).to_dict()
        for value in items
    ]


async def test_corrupt_storage_does_not_reimport(integration):
    env = integration
    env.store.async_load.return_value = {"items": [{"summary": "broken"}]}
    with pytest.raises(env.not_ready):
        await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.assert_not_awaited()
    env.store.async_save.assert_not_awaited()


async def test_migrates_matching_legacy_store_and_preserves_local_edits(integration):
    env = integration
    old_entry = SimpleNamespace(
        entry_id="old-entry",
        data={"source_entity_id": "todo.alexa", "name": "Einkaufszettel"},
    )
    env.hass.config_entries.async_entries.return_value = [old_entry]
    old_store = env.stores.setdefault(
        "easy_shopping.old-entry",
        SimpleNamespace(async_load=AsyncMock(), async_save=AsyncMock()),
    )
    snapshot = {
        "items": [
            {
                "uid": "local-id",
                "summary": "Meine Milch",
                "status": "completed",
                "description": "3 Flaschen",
                "due": None,
                "source_uid": "alexa-id",
            }
        ]
    }
    old_store.async_load.return_value = snapshot
    assert await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.assert_not_awaited()
    old_store.async_save.assert_not_awaited()
    assert env.entry.runtime_data.items[0].to_dict() == snapshot["items"][0]
    env.store.async_save.assert_awaited_once_with(snapshot)


async def test_ambiguous_legacy_stores_do_not_import_or_overwrite(integration):
    env = integration
    env.hass.config_entries.async_entries.return_value = [
        SimpleNamespace(
            entry_id="old-one",
            data={"source_entity_id": "todo.alexa"},
        ),
        SimpleNamespace(
            entry_id="old-two",
            data={"source_entity_id": "todo.alexa"},
        ),
    ]
    with pytest.raises(env.not_ready, match="More than one legacy entry"):
        await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.assert_not_awaited()
    env.store.async_save.assert_not_awaited()


@pytest.mark.parametrize(
    "response", [None, {}, {"todo.alexa": {}}, {"todo.alexa": {"items": None}}]
)
async def test_bad_source_response_does_not_publish_empty_copy(integration, response):
    env = integration
    env.hass.services.async_call.return_value = response
    with pytest.raises(env.not_ready):
        await env.package.async_setup_entry(env.hass, env.entry)
    env.store.async_save.assert_not_awaited()
    env.hass.config_entries.async_forward_entry_setups.assert_not_awaited()


async def test_failed_initial_save_does_not_publish_list(integration):
    env = integration
    env.store.async_save.side_effect = OSError("disk full")
    with pytest.raises(env.not_ready):
        await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.config_entries.async_forward_entry_setups.assert_not_awaited()


async def test_check_persistence_error_and_concurrent_updates(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    data = env.entry.runtime_data
    data.items.append(env.model.ShoppingItem("second", "Brot"))
    entity = env.todo.EinkaufszettelTodo(data, "entry-id", "Einkaufszettel")
    entity.async_write_ha_state = Mock()
    items = entity.todo_items
    items[0].status = env.Status.COMPLETED
    items[1].status = env.Status.COMPLETED
    env.store.async_save.side_effect = OSError("disk full")
    with pytest.raises(env.error, match="Cannot save"):
        await entity.async_update_todo_item(items[0])
    assert data.items[0].status == "needs_action"
    entity.async_write_ha_state.assert_not_called()
    env.store.async_save.side_effect = None
    await asyncio.gather(*(entity.async_update_todo_item(item) for item in items))
    assert [item.status for item in data.items] == ["completed", "completed"]
    assert data.items[0].source_uid == "a"
    assert entity.async_write_ha_state.call_count == 2
    assert [
        item["status"] for item in env.store.async_save.call_args.args[0]["items"]
    ] == ["completed", "completed"]


async def test_service_can_supply_status_as_string(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    entity = env.todo.EinkaufszettelTodo(
        env.entry.runtime_data, "entry-id", "Einkaufszettel"
    )
    item = entity.todo_items[0]
    item.status = "completed"
    await entity.async_update_todo_item(item)
    assert env.entry.runtime_data.items[0].status == "completed"


async def test_copy_button_appends_once_and_keeps_local_edits(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    data = env.entry.runtime_data
    original = data.items[0]
    data.items = [
        env.model.ShoppingItem(
            original.uid, "Meine Milch", "completed", "3 Flaschen", source_uid="a"
        )
    ]
    env.hass.services.async_call.return_value = {
        "todo.alexa": {
            "items": [
                {"uid": "a", "summary": "Milch", "status": "needs_action"},
                {"uid": "b", "summary": "Milch", "status": "needs_action"},
            ]
        }
    }
    button = env.button.CopySourceButton(env.entry)
    button.hass = env.hass
    await button.async_press()
    assert len(data.items) == 2
    assert data.items[0].summary == "Meine Milch"
    assert data.items[0].status == "completed"
    assert data.items[0].description == "3 Flaschen"
    assert data.items[1].source_uid == "b"


async def test_web_app_api_supports_offline_retryable_mutations(integration):
    env = integration
    assert await env.package.async_setup_entry(env.hass, env.entry)
    env.entry.domain = "einkaufszettel"
    env.hass.config_entries.async_get_entry.return_value = env.entry
    connection = Mock()

    await env.websocket.websocket_add_item(
        env.hass,
        connection,
        {
            "id": 1,
            "entry_id": env.entry.entry_id,
            "uid": "offline-id",
            "summary": "Brot",
        },
    )
    assert env.entry.runtime_data.items[-1].uid == "offline-id"
    connection.send_result.assert_called_once()
    env.store.async_save.assert_awaited()

    await env.websocket.websocket_add_item(
        env.hass,
        connection,
        {
            "id": 2,
            "entry_id": env.entry.entry_id,
            "uid": "offline-id",
            "summary": "Brot",
        },
    )
    assert [item.uid for item in env.entry.runtime_data.items].count("offline-id") == 1

    await env.websocket.websocket_update_item(
        env.hass,
        connection,
        {
            "id": 3,
            "entry_id": env.entry.entry_id,
            "uid": "offline-id",
            "status": "completed",
        },
    )
    assert env.entry.runtime_data.items[-1].status == "completed"

    await env.websocket.websocket_delete_item(
        env.hass,
        connection,
        {"id": 4, "entry_id": env.entry.entry_id, "uid": "offline-id"},
    )
    assert all(item.uid != "offline-id" for item in env.entry.runtime_data.items)


async def test_todo_entity_can_add_and_delete_items(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    entity = env.todo.EinkaufszettelTodo(
        env.entry.runtime_data, env.entry.entry_id, "Einkaufszettel"
    )
    entity.async_write_ha_state = Mock()

    await entity.async_create_todo_item(env.Item(uid=None, summary="Brot", status=None))
    assert env.entry.runtime_data.items[-1].summary == "Brot"
    created_uid = env.entry.runtime_data.items[-1].uid
    await entity.async_delete_todo_items([created_uid])
    assert all(item.uid != created_uid for item in env.entry.runtime_data.items)
    assert entity.async_write_ha_state.call_count == 2


async def test_copy_button_noop_does_not_save_unchanged_list(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.return_value = {
        "todo.alexa": {
            "items": [{"uid": "a", "summary": "Milch", "status": "needs_action"}]
        }
    }
    button = env.button.CopySourceButton(env.entry)
    button.hass = env.hass
    saved = env.store.async_save.await_count
    await button.async_press()
    assert len(env.entry.runtime_data.items) == 1
    assert env.store.async_save.await_count == saved


async def test_install_button_uses_configured_external_url(integration):
    env = integration
    button = env.button.InstallWebAppButton(env.entry)
    button.hass = env.hass

    await button.async_press()

    env.network.get_url.assert_called_once_with(env.hass, prefer_external=True)
    message = env.persistent_notification.async_create.call_args.args[1]
    assert (
        "[Web-App öffnen und installieren]"
        "(https://ha.example.test/einkaufszettel/app.html?entry_id=test-entry)"
        in message
    )
    assert (
        "https://ha.example.test/einkaufszettel/app.html?entry_id=test-entry" in message
    )


async def test_async_setup_serves_app_and_registers_websocket_api(integration):
    env = integration
    env.hass.http = SimpleNamespace(async_register_static_paths=AsyncMock())
    assert await env.package.async_setup(env.hass, {})
    env.hass.http.async_register_static_paths.assert_awaited_once()
    assert env.websocket_api.async_register_command.call_count == 5


async def test_entry_registers_sidebar_app_panel_and_removes_it_on_unload(integration):
    env = integration
    assert await env.package.async_setup_entry(env.hass, env.entry)

    env.frontend.async_register_built_in_panel.assert_called_once_with(
        env.hass,
        "iframe",
        sidebar_title="Einkaufszettel",
        sidebar_icon="mdi:cart-outline",
        frontend_url_path="einkaufszettel_test-entry",
        config={"url": "/einkaufszettel/app.html?entry_id=test-entry"},
    )

    assert await env.package.async_unload_entry(env.hass, env.entry)
    env.frontend.async_remove_panel.assert_called_once_with(
        env.hass, "einkaufszettel_test-entry"
    )


@pytest.mark.parametrize("failure", ["read", "save", "missing_uid"])
async def test_copy_button_failure_preserves_snapshot(integration, failure):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    original = list(env.entry.runtime_data.items)
    env.hass.services.async_call.return_value = {
        "todo.alexa": {
            "items": [
                {
                    "uid": "b" if failure != "missing_uid" else None,
                    "summary": "Brot",
                    "status": "needs_action",
                }
            ]
        }
    }
    if failure == "read":
        env.hass.services.async_call.side_effect = env.error("Source unavailable")
    if failure == "save":
        env.store.async_save.side_effect = OSError("Disk full")
    button = env.button.CopySourceButton(env.entry)
    button.hass = env.hass
    with pytest.raises(env.error, match="Cannot copy"):
        await button.async_press()
    assert env.entry.runtime_data.items == original
    env.dispatcher.async_dispatcher_send.assert_not_called()


async def test_simultaneous_copy_presses_do_not_duplicate_items(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.return_value = {
        "todo.alexa": {
            "items": [{"uid": "new", "summary": "Brot", "status": "needs_action"}]
        }
    }
    button = env.button.CopySourceButton(env.entry)
    button.hass = env.hass
    await asyncio.gather(button.async_press(), button.async_press())
    assert len(env.entry.runtime_data.items) == 2
