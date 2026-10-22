"""Test our lifecycle logic with explicit HA boundary doubles, not a HA runtime."""

import asyncio
import importlib
import importlib.util
import sys
from copy import deepcopy
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

    class ConfigFlow:
        def __init_subclass__(cls, **kwargs):
            pass

        def _async_current_entries(self):
            return self.hass.config_entries.async_entries("einkaufszettel")

        async def async_set_unique_id(self, unique_id):
            self.unique_id = unique_id

        def _abort_if_unique_id_configured(self):
            pass

        def async_abort(self, **kwargs):
            return {"type": "abort", **kwargs}

        def async_create_entry(self, **kwargs):
            return {"type": "create_entry", **kwargs}

        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

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
    module(
        "homeassistant.config_entries",
        ConfigEntry=Generic,
        ConfigFlow=ConfigFlow,
        ConfigFlowResult=dict,
    )
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
        Schema=lambda schema: schema,
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
    module(
        "homeassistant.helpers.event",
        async_track_time_interval=Mock(return_value=Mock()),
    )
    dispatcher = module(
        "homeassistant.helpers.dispatcher",
        async_dispatcher_connect=Mock(),
        async_dispatcher_send=Mock(),
    )
    module(
        "homeassistant.helpers.entity_registry",
        async_get=lambda hass: registry,
    )
    registry = SimpleNamespace(
        entities={},
        async_get=Mock(return_value=None),
        async_remove=Mock(),
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
    config_flow = importlib.import_module(f"{spec.name}.config_flow")
    hass = SimpleNamespace(
        data={},
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
            async_update_entry=Mock(),
            flow=SimpleNamespace(async_init=AsyncMock()),
        ),
    )
    entry = SimpleNamespace(
        entry_id="test-entry",
        data={"source_entity_id": "todo.alexa", "name": "Einkaufszettel"},
        options={},
    )
    yield SimpleNamespace(
        package=package,
        todo=todo,
        button=button,
        dispatcher=dispatcher,
        model=model,
        websocket=websocket,
        config_flow=config_flow,
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
        registry=registry,
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

    await env.websocket.websocket_update_item(
        env.hass,
        connection,
        {
            "id": 4,
            "entry_id": env.entry.entry_id,
            "uid": "offline-id",
            "summary": "Vollkornbrot",
        },
    )
    assert env.entry.runtime_data.items[-1].summary == "Vollkornbrot"
    assert env.entry.runtime_data.items[-1].status == "completed"

    await env.websocket.websocket_delete_item(
        env.hass,
        connection,
        {"id": 4, "entry_id": env.entry.entry_id, "uid": "offline-id"},
    )
    assert all(item.uid != "offline-id" for item in env.entry.runtime_data.items)


async def test_web_app_lists_loaded_entries_with_names_and_sources(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    second = SimpleNamespace(
        entry_id="edeka",
        data={"name": "Edeka", "source_entity_id": "todo.edeka"},
        runtime_data=SimpleNamespace(items=[]),
        options={},
    )
    unloaded = SimpleNamespace(entry_id="unloaded", runtime_data=None)
    env.hass.config_entries.async_entries.return_value = [
        env.entry,
        second,
        unloaded,
    ]
    env.hass.config_entries.async_entries.reset_mock()
    connection = Mock()
    await env.websocket.websocket_get_lists(env.hass, connection, {"id": 7})
    env.hass.config_entries.async_entries.assert_called_once_with("einkaufszettel")
    connection.send_result.assert_called_once_with(
        7,
        [
            {
                "entry_id": "test-entry",
                "name": "Einkaufszettel",
                "source_entity_id": "todo.alexa",
            },
            {
                "entry_id": "edeka",
                "name": "Edeka",
                "source_entity_id": "todo.edeka",
            },
        ],
    )


async def test_web_app_lists_empty_when_no_lists_are_loaded(integration):
    connection = Mock()
    await integration.websocket.websocket_get_lists(
        integration.hass, connection, {"id": 8}
    )
    connection.send_result.assert_called_once_with(8, [])


async def test_sources_discovered_without_extra_config_entries(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.states.async_all = Mock(
        return_value=[
            SimpleNamespace(entity_id="todo.alexa", name="Alexa Long Name", state="1"),
            SimpleNamespace(entity_id="todo.edeka", name="Alexa Edeka List", state="0"),
            SimpleNamespace(
                entity_id="todo.einkaufszettel", name="Duplicate", state="1"
            ),
        ]
    )
    env.registry.async_get.side_effect = lambda entity_id: (
        SimpleNamespace(platform="einkaufszettel")
        if entity_id == "todo.einkaufszettel"
        else None
    )
    env.hass.config_entries.async_entries.return_value = [env.entry]
    connection = Mock()
    await env.websocket.websocket_get_sources(env.hass, connection, {"id": 10})
    sources = connection.send_result.call_args.args[1]
    assert [source["source_entity_id"] for source in sources] == [
        "todo.alexa",
        "todo.edeka",
    ]
    assert sources[0]["name"] == "Einkaufszettel"
    assert sources[0]["enabled"]
    assert sources[1]["name"] == "Alexa Edeka List"
    assert not sources[1]["enabled"]


async def test_alias_and_visibility_update_shared_config_not_source(integration):
    env = integration
    env.hass.states.async_all = Mock(
        return_value=[
            SimpleNamespace(entity_id="todo.alexa", name="Alexa Long Name", state="1")
        ]
    )
    env.hass.config_entries.async_entries.return_value = [env.entry]
    connection = Mock(spec=["user", "send_result", "send_error"])
    connection.user = SimpleNamespace(is_admin=True)
    await env.websocket.websocket_configure_list(
        env.hass,
        connection,
        {
            "id": 11,
            "source_entity_id": "todo.alexa",
            "name": " Kaufland ",
            "enabled": False,
        },
    )
    env.hass.config_entries.async_update_entry.assert_called_once_with(
        env.entry,
        title="Kaufland",
        data={"name": "Kaufland", "source_entity_id": "todo.alexa"},
        options={"enabled": False},
    )
    env.hass.services.async_call.assert_not_awaited()
    connection.send_result.assert_called_once_with(11, {"entry_id": "test-entry"})


async def test_enabling_discovered_source_imports_it_without_user_config_flow(
    integration,
):
    env = integration
    env.hass.states.async_all = Mock(
        return_value=[
            SimpleNamespace(entity_id="todo.edeka", name="Alexa Edeka", state="1")
        ]
    )
    created = SimpleNamespace(
        entry_id="new",
        data={"name": "Edeka", "source_entity_id": "todo.edeka"},
        options={},
    )
    env.hass.config_entries.flow.async_init.return_value = {
        "type": "create_entry",
        "result": created,
    }
    connection = Mock()
    await env.websocket.websocket_configure_list(
        env.hass,
        connection,
        {"id": 12, "source_entity_id": "todo.edeka", "name": "Edeka", "enabled": True},
    )
    env.hass.config_entries.flow.async_init.assert_awaited_once_with(
        "einkaufszettel",
        context={"source": "import"},
        data={"source_entity_id": "todo.edeka", "name": "Edeka", "enabled": True},
    )
    connection.send_result.assert_called_once_with(12, {"entry_id": "new"})


@pytest.mark.parametrize(
    "name, source", [(" ", "todo.alexa"), ("x" * 101, "todo.alexa"), ("K", "todo.fake")]
)
async def test_manage_lists_rejects_invalid_input(integration, name, source):
    env = integration
    env.hass.states.async_all = Mock(
        return_value=[SimpleNamespace(entity_id="todo.alexa", name="Alexa", state="1")]
    )
    connection = Mock()
    await env.websocket.websocket_configure_list(
        env.hass,
        connection,
        {"id": 13, "source_entity_id": source, "name": name, "enabled": True},
    )
    connection.send_error.assert_called_once()
    env.hass.config_entries.async_update_entry.assert_not_called()
    env.hass.config_entries.flow.async_init.assert_not_awaited()


async def test_disabled_lists_not_offered_but_data_is_not_deleted(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    env.entry.options = {"enabled": False}
    env.hass.config_entries.async_entries.return_value = [env.entry]
    connection = Mock()
    await env.websocket.websocket_get_lists(env.hass, connection, {"id": 14})
    connection.send_result.assert_called_once_with(14, [])
    assert env.entry.runtime_data.items[0].summary == "Milch"


async def test_setup_removes_only_own_todo_entities(integration):
    env = integration
    env.registry.entities = {
        "own": SimpleNamespace(
            platform="einkaufszettel", entity_id="todo.einkaufszettel"
        ),
        "source": SimpleNamespace(platform="alexa", entity_id="todo.alexa"),
        "button": SimpleNamespace(
            platform="einkaufszettel", entity_id="button.install"
        ),
    }
    await env.package.async_setup_entry(env.hass, env.entry)
    env.registry.async_remove.assert_called_once_with("todo.einkaufszettel")
    env.hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        env.entry, ["button"]
    )


async def test_hub_setup_does_not_require_a_source(integration):
    env = integration
    env.entry.data = {"name": "Einkaufszettel"}
    await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.assert_not_awaited()
    assert env.entry.runtime_data.items == []


async def test_hub_flow_has_no_source_selector(integration):
    flow = integration.config_flow.EinkaufszettelConfigFlow()
    flow.hass = integration.hass
    result = await flow.async_step_user()
    assert result == {"type": "form", "step_id": "user", "data_schema": {}}
    result = await flow.async_step_user({})
    assert result["data"] == {"name": "Einkaufszettel"}
    assert result["type"] == "create_entry"


async def test_import_flow_reads_source_and_preserves_disabled_setting(integration):
    flow = integration.config_flow.EinkaufszettelConfigFlow()
    flow.hass = integration.hass
    result = await flow.async_step_import(
        {"source_entity_id": "todo.alexa", "name": " Kaufland ", "enabled": False}
    )
    assert result["type"] == "create_entry"
    assert result["data"] == {"source_entity_id": "todo.alexa", "name": "Kaufland"}
    assert result["options"] == {"enabled": False}
    assert flow.unique_id == "todo.alexa"


async def test_import_flow_reports_unreadable_source(integration):
    flow = integration.config_flow.EinkaufszettelConfigFlow()
    flow.hass = integration.hass
    integration.hass.services.async_call.side_effect = integration.error("Unavailable")
    result = await flow.async_step_import(
        {"source_entity_id": "todo.alexa", "name": "Kaufland", "enabled": True}
    )
    assert result == {"type": "abort", "reason": "cannot_read_source"}


@pytest.mark.parametrize("user", [None, SimpleNamespace(is_admin=False)])
async def test_list_management_requires_admin_before_discovering_or_writing(
    integration,
    user,
):
    env = integration
    connection = Mock(spec=["user", "send_result", "send_error"])
    connection.user = user
    await env.websocket.websocket_configure_list(
        env.hass,
        connection,
        {
            "id": 15,
            "source_entity_id": "todo.alexa",
            "name": "Market",
            "enabled": True,
        },
    )
    connection.send_error.assert_called_once_with(
        15, "unauthorized", "HA-Administratorrechte erforderlich."
    )
    connection.send_result.assert_not_called()
    env.hass.config_entries.async_update_entry.assert_not_called()
    env.hass.config_entries.flow.async_init.assert_not_awaited()


async def test_import_failure_is_reported_without_success(integration):
    env = integration
    env.hass.states.async_all = Mock(
        return_value=[
            SimpleNamespace(entity_id="todo.edeka", name="Edeka", state="unavailable")
        ]
    )
    env.hass.config_entries.flow.async_init.return_value = {
        "type": "form",
        "errors": {"base": "cannot_read_source"},
    }
    connection = Mock()
    await env.websocket.websocket_configure_list(
        env.hass,
        connection,
        {"id": 16, "source_entity_id": "todo.edeka", "name": "Edeka", "enabled": True},
    )
    connection.send_error.assert_called_once()
    connection.send_result.assert_not_called()
    env.hass.config_entries.async_update_entry.assert_not_called()


async def test_missing_configured_source_stays_manageable(integration):
    env = integration
    env.hass.states.async_all = Mock(return_value=[])
    env.hass.config_entries.async_entries.return_value = [env.entry]
    connection = Mock()
    await env.websocket.websocket_get_sources(env.hass, connection, {"id": 17})
    source = connection.send_result.call_args.args[1][0]
    assert source["source_entity_id"] == "todo.alexa"
    assert source["enabled"]
    assert not source["available"]


async def test_web_app_item_edits_stay_in_the_requested_list(integration):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    env.entry.domain = "einkaufszettel"
    second = SimpleNamespace(
        entry_id="edeka",
        domain="einkaufszettel",
        data={"name": "Edeka", "source_entity_id": "todo.edeka"},
        runtime_data=env.package.EinkaufszettelData(
            store=SimpleNamespace(async_save=AsyncMock()),
            items=[env.model.ShoppingItem(uid="edeka-bread", summary="Brot")],
        ),
    )
    entries = {env.entry.entry_id: env.entry, second.entry_id: second}
    env.hass.config_entries.async_get_entry.side_effect = entries.get
    original_items = list(env.entry.runtime_data.items)
    connection = Mock()
    await env.websocket.websocket_update_item(
        env.hass,
        connection,
        {
            "id": 9,
            "entry_id": "edeka",
            "uid": "edeka-bread",
            "summary": "Vollkornbrot",
        },
    )
    assert env.entry.runtime_data.items == original_items
    assert second.runtime_data.items[0].summary == "Vollkornbrot"
    assert second.runtime_data.items[0].status == "needs_action"
    second.runtime_data.store.async_save.assert_awaited_once()
    assert connection.send_result.call_args.args[1]["entry_id"] == "edeka"


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
    assert env.websocket_api.async_register_command.call_count == 20


async def test_catalog_shared_persistence_and_market_rename_preserves_categories(
    integration,
):
    env = integration
    connection = Mock(user=SimpleNamespace(is_admin=True))
    await env.websocket.websocket_get_catalog(
        env.hass, connection, {"id": 1, "type": "einkaufszettel/get_catalog"}
    )
    store = env.stores["einkaufszettel.supermarkets"]
    persisted = {"supermarkets": [{"id": "shop", "name": "Markt"}]}
    store.async_load.side_effect = lambda: persisted

    async def save(data):
        nonlocal persisted
        persisted = data

    store.async_save.side_effect = save
    await env.websocket.websocket_save_category(
        env.hass,
        connection,
        {
            "id": 2,
            "type": "einkaufszettel/save_category",
            "category_id": "",
            "name": "Obst",
        },
    )
    uid = persisted["categories"][0]["id"]
    await env.websocket.websocket_save_market_categories(
        env.hass,
        connection,
        {
            "id": 3,
            "type": "einkaufszettel/save_market_categories",
            "market_id": "shop",
            "category_ids": [uid],
        },
    )
    await env.websocket.websocket_save_supermarket(
        env.hass,
        connection,
        {
            "id": 4,
            "type": "einkaufszettel/save_supermarket",
            "market_id": "shop",
            "name": "Neu",
        },
    )
    image = "data:image/png;base64,AA=="
    await env.websocket.websocket_save_market_bonus_card(
        env.hass,
        connection,
        {
            "id": 5,
            "type": "einkaufszettel/save_market_bonus_card",
            "market_id": "shop",
            "bonus_card": image,
        },
    )
    assert persisted["categories"] == [{"id": uid, "name": "Obst"}]
    assert persisted["supermarkets"][0] == {
        "id": "shop",
        "name": "Neu",
        "category_ids": [uid],
        "bonus_card": image,
    }
    await env.websocket.websocket_delete_category(
        env.hass,
        connection,
        {
            "id": 6,
            "type": "einkaufszettel/delete_category",
            "category_id": uid,
        },
    )
    assert persisted["categories"] == []
    assert persisted["supermarkets"][0]["category_ids"] == []
    assert persisted["supermarkets"][0]["bonus_card"] == image
    env.hass.data.clear()
    await env.websocket.websocket_get_catalog(
        env.hass, connection, {"id": 7, "type": "einkaufszettel/get_catalog"}
    )
    connection.send_result.assert_called_with(7, {**persisted, "products": []})
    connection.send_error.assert_not_called()


@pytest.mark.parametrize(
    "action", ["save_category", "delete_category", "save_market_categories"]
)
@pytest.mark.parametrize("user", [None, SimpleNamespace(is_admin=False)])
async def test_catalog_writes_require_admin(integration, action, user):
    env = integration
    connection = Mock(user=user)
    await getattr(env.websocket, f"websocket_{action}")(
        env.hass, connection, {"id": 1, "type": f"einkaufszettel/{action}"}
    )
    connection.send_error.assert_called_with(
        1, "unauthorized", "HA-Administratorrechte erforderlich."
    )
    assert "einkaufszettel.supermarkets" not in env.stores


async def test_catalog_failed_save_reports_error_without_success(integration):
    env = integration
    connection = Mock(user=SimpleNamespace(is_admin=True))
    await env.websocket.websocket_get_catalog(
        env.hass, connection, {"id": 1, "type": "einkaufszettel/get_catalog"}
    )
    connection.reset_mock()
    env.stores["einkaufszettel.supermarkets"].async_save.side_effect = OSError(
        "Disk full"
    )
    await env.websocket.websocket_save_category(
        env.hass,
        connection,
        {
            "id": 2,
            "type": "einkaufszettel/save_category",
            "category_id": "",
            "name": "Obst",
        },
    )
    connection.send_error.assert_called_with(2, "cannot_manage_catalog", "Disk full")
    connection.send_result.assert_not_called()


async def test_supermarkets_shared_crud_and_restart(integration):
    env = integration
    connection = Mock(user=SimpleNamespace(is_admin=True))
    await env.websocket.websocket_get_supermarkets(
        env.hass, connection, {"id": 1, "type": "einkaufszettel/get_supermarkets"}
    )
    connection.send_result.assert_called_with(1, [])
    store = env.stores["einkaufszettel.supermarkets"]
    persisted = None

    async def save(data):
        nonlocal persisted
        persisted = data
        store.async_load.return_value = data

    store.async_save.side_effect = save
    await env.websocket.websocket_save_supermarket(
        env.hass,
        connection,
        {
            "id": 2,
            "type": "einkaufszettel/save_supermarket",
            "market_id": "",
            "name": " Edeka Nord ",
        },
    )
    market = persisted["supermarkets"][0]
    assert market["name"] == "Edeka Nord"
    uid = market["id"]
    await env.websocket.websocket_save_supermarket(
        env.hass,
        connection,
        {
            "id": 3,
            "type": "einkaufszettel/save_supermarket",
            "market_id": uid,
            "name": "Edeka Süd",
        },
    )
    assert persisted["supermarkets"] == [{"id": uid, "name": "Edeka Süd"}]
    env.hass.data.clear()
    await env.websocket.websocket_get_supermarkets(
        env.hass, connection, {"id": 4, "type": "einkaufszettel/get_supermarkets"}
    )
    connection.send_result.assert_called_with(4, persisted["supermarkets"])
    await env.websocket.websocket_delete_supermarket(
        env.hass,
        connection,
        {"id": 5, "type": "einkaufszettel/delete_supermarket", "market_id": uid},
    )
    assert persisted == {"supermarkets": []}
    env.store.async_save.assert_not_awaited()


@pytest.mark.parametrize("action", ["save_supermarket", "delete_supermarket"])
@pytest.mark.parametrize("user", [None, SimpleNamespace(is_admin=False)])
async def test_supermarket_writes_require_admin(integration, action, user):
    env = integration
    connection = Mock(user=user)
    await getattr(env.websocket, f"websocket_{action}")(
        env.hass,
        connection,
        {"id": 1, "type": f"einkaufszettel/{action}", "market_id": "", "name": "Markt"},
    )
    assert connection.send_error.call_args.args[1] == "unauthorized"
    connection.send_result.assert_not_called()
    assert "einkaufszettel.supermarkets" not in env.stores


@pytest.mark.parametrize(
    ("uid", "name"),
    [("", ""), ("", " " * 3), ("", "x" * 101), ("", "edeka"), ("missing", "Neu")],
)
async def test_supermarket_invalid_names_duplicates_and_stale_ids(
    integration, uid, name
):
    env = integration
    connection = Mock(user=SimpleNamespace(is_admin=True))
    await env.websocket.websocket_get_supermarkets(
        env.hass, connection, {"id": 1, "type": "einkaufszettel/get_supermarkets"}
    )
    store = env.stores["einkaufszettel.supermarkets"]
    store.async_load.return_value = {"supermarkets": [{"id": "a", "name": "Edeka"}]}
    connection.reset_mock()
    await env.websocket.websocket_save_supermarket(
        env.hass,
        connection,
        {
            "id": 2,
            "type": "einkaufszettel/save_supermarket",
            "market_id": uid,
            "name": name,
        },
    )
    connection.send_error.assert_called_once()
    connection.send_result.assert_not_called()
    store.async_save.assert_not_awaited()


async def test_supermarket_persistence_failure_is_not_success(integration):
    env = integration
    connection = Mock(user=SimpleNamespace(is_admin=True))
    await env.websocket.websocket_get_supermarkets(
        env.hass, connection, {"id": 1, "type": "einkaufszettel/get_supermarkets"}
    )
    store = env.stores["einkaufszettel.supermarkets"]
    store.async_save.side_effect = OSError("Disk full")
    connection.reset_mock()
    await env.websocket.websocket_save_supermarket(
        env.hass,
        connection,
        {
            "id": 2,
            "type": "einkaufszettel/save_supermarket",
            "market_id": "",
            "name": "Markt",
        },
    )
    connection.send_error.assert_called_with(
        2, "cannot_manage_supermarkets", "Disk full"
    )
    connection.send_result.assert_not_called()


async def test_supermarket_read_allowed_without_admin_and_corruption_reported(
    integration,
):
    env = integration
    connection = Mock(user=SimpleNamespace(is_admin=False))
    await env.websocket.websocket_get_supermarkets(
        env.hass, connection, {"id": 1, "type": "einkaufszettel/get_supermarkets"}
    )
    connection.send_result.assert_called_with(1, [])
    env.stores["einkaufszettel.supermarkets"].async_load.return_value = {
        "supermarkets": [None]
    }
    connection.reset_mock()
    await env.websocket.websocket_get_supermarkets(
        env.hass, connection, {"id": 2, "type": "einkaufszettel/get_supermarkets"}
    )
    connection.send_error.assert_called_once()
    connection.send_result.assert_not_called()


async def test_concurrent_supermarket_creates_keep_both_changes(integration):
    env = integration
    connection = Mock(user=SimpleNamespace(is_admin=True))
    await env.websocket.websocket_get_supermarkets(
        env.hass, connection, {"id": 1, "type": "einkaufszettel/get_supermarkets"}
    )
    store = env.stores["einkaufszettel.supermarkets"]
    persisted = {"supermarkets": []}

    async def load():
        await asyncio.sleep(0)
        return persisted

    async def save(data):
        nonlocal persisted
        await asyncio.sleep(0)
        persisted = data

    store.async_load.side_effect = load
    store.async_save.side_effect = save
    await asyncio.gather(
        *(
            env.websocket.websocket_save_supermarket(
                env.hass,
                connection,
                {
                    "id": index,
                    "type": "einkaufszettel/save_supermarket",
                    "market_id": "",
                    "name": name,
                },
            )
            for index, name in enumerate(("Kaufland", "Edeka"), start=2)
        )
    )
    assert {market["name"] for market in persisted["supermarkets"]} == {
        "Kaufland",
        "Edeka",
    }
    assert len({market["id"] for market in persisted["supermarkets"]}) == 2


@pytest.mark.parametrize("uid", ["", "missing"])
async def test_supermarket_delete_rejects_missing_selection(integration, uid):
    env = integration
    connection = Mock(user=SimpleNamespace(is_admin=True))
    await env.websocket.websocket_delete_supermarket(
        env.hass,
        connection,
        {"id": 1, "type": "einkaufszettel/delete_supermarket", "market_id": uid},
    )
    connection.send_error.assert_called_once()
    connection.send_result.assert_not_called()
    env.stores["einkaufszettel.supermarkets"].async_save.assert_not_awaited()


async def test_entry_registers_sidebar_app_panel_and_removes_it_on_unload(integration):
    env = integration
    assert await env.package.async_setup_entry(env.hass, env.entry)

    env.frontend.async_register_built_in_panel.assert_called_once_with(
        env.hass,
        "iframe",
        sidebar_title="Einkaufszettel",
        sidebar_icon="mdi:cart-outline",
        frontend_url_path="einkaufszettel_app",
        config={"url": "/einkaufszettel/app.html"},
    )

    assert await env.package.async_unload_entry(env.hass, env.entry)
    env.frontend.async_remove_panel.assert_called_once_with(
        env.hass, "einkaufszettel_app"
    )


async def test_multiple_lists_share_one_panel_until_last_unload(integration):
    env = integration
    other = SimpleNamespace(entry_id="other-list", data={"name": "Edeka"}, options={})
    assert await env.package.async_setup_entry(env.hass, env.entry)
    assert await env.package.async_setup_entry(env.hass, other)
    env.frontend.async_register_built_in_panel.assert_called_once()
    assert await env.package.async_unload_entry(env.hass, env.entry)
    env.frontend.async_remove_panel.assert_not_called()
    env.hass.config_entries.async_unload_platforms.return_value = False
    assert not await env.package.async_unload_entry(env.hass, other)
    env.frontend.async_remove_panel.assert_not_called()
    env.hass.config_entries.async_unload_platforms.return_value = True
    assert await env.package.async_unload_entry(env.hass, other)
    env.frontend.async_remove_panel.assert_called_once_with(
        env.hass, "einkaufszettel_app"
    )
    assert await env.package.async_setup_entry(env.hass, other)
    assert env.frontend.async_register_built_in_panel.call_count == 2


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


async def sync_environment(env, monkeypatch, *, features=49):
    """Use the real reconciler against an in-memory external To-do service."""
    await env.package.async_setup_entry(env.hass, env.entry)
    catalog_store = env.stores["einkaufszettel.supermarkets"]
    catalog = {"categories": [{"id": "dairy", "name": "Milchprodukte"}]}

    async def save_catalog(value):
        nonlocal catalog
        catalog = deepcopy(value)

    catalog_store.async_load.side_effect = lambda: deepcopy(catalog)
    catalog_store.async_save.side_effect = save_catalog
    sync = importlib.import_module(f"{env.package.__name__}.sync")
    source_sync = importlib.import_module(f"{env.package.__name__}.source_sync")
    remote = [{"uid": "a", "summary": "Milch", "status": "needs_action"}]
    calls = []

    async def service(domain, service, payload, **kwargs):
        assert domain == "todo"
        calls.append((service, dict(payload)))
        if service == "get_items":
            return {"todo.alexa": {"items": [dict(item) for item in remote]}}
        if service == "add_item":
            remote.append(
                {
                    "uid": f"created-{len(calls)}",
                    "summary": payload["item"],
                    "status": "needs_action",
                }
            )
        elif service == "update_item":
            item = next(item for item in remote if item["uid"] == payload["item"])
            for source, target in (("rename", "summary"), ("status", "status")):
                if source in payload:
                    item[target] = payload[source]
        elif service == "remove_item":
            remote[:] = [item for item in remote if item["uid"] != payload["item"]]
        else:
            raise AssertionError(service)

    env.hass.services.async_call.side_effect = service
    env.hass.states.get = lambda _id: SimpleNamespace(
        state="1", attributes={"supported_features": features}
    )
    monkeypatch.setattr(env.entry, "options", {})
    return SimpleNamespace(
        protocol=sync,
        source=source_sync,
        remote=remote,
        calls=calls,
        data=env.entry.runtime_data,
    )


async def conflict_environment(env, monkeypatch, *, ambiguous=False):
    ctx = await sync_environment(env, monkeypatch)
    await ctx.source.synchronize_source(env.hass, env.entry)
    await ctx.protocol.apply_operation(
        ctx.data,
        "pending-add",
        "add_item",
        "pending",
        {
            "summary": "Brot",
            "metadata": {"note": "Behalten"},
        },
    )
    state = deepcopy(ctx.data.sync)
    state["creates"]["pending"] = {"before": ["a"], "summary": "Brot"}
    await ctx.protocol.persist_items(ctx.data, ctx.data.items, state)
    if ambiguous:
        ctx.remote.extend(
            [
                {"uid": "b1", "summary": "Brot", "status": "needs_action"},
                {"uid": "b2", "summary": "Brot", "status": "needs_action"},
            ]
        )
    await ctx.source.synchronize_source(env.hass, env.entry)
    return ctx


@pytest.mark.parametrize("mode", ["create", "restart", "link", "rename"])
async def test_source_accepts_case_and_whitespace_normalization(
    integration, monkeypatch, mode
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.source.synchronize_source(env.hass, env.entry)
    real_service = env.hass.services.async_call.side_effect

    async def normalizing(domain, service, payload, **kwargs):
        result = await real_service(domain, service, payload, **kwargs)
        if service in ("add_item", "update_item"):
            for item in ctx.remote:
                item["summary"] = " ".join(item["summary"].split()).capitalize()
        return result

    env.hass.services.async_call.side_effect = normalizing
    await ctx.protocol.apply_operation(
        ctx.data,
        "add-normalized",
        "add_item",
        "normalized",
        {"summary": "SYNC TEST   Brot", "metadata": {"note": "Behalten"}},
    )
    if mode in ("restart", "link"):
        state = deepcopy(ctx.data.sync)
        state["creates"]["normalized"] = {
            "before": ["a"],
            "summary": "SYNC TEST   Brot",
            "needs_decision": mode == "link",
        }
        await ctx.protocol.persist_items(ctx.data, ctx.data.items, state)
        ctx.remote.append(
            {
                "uid": "normalized-source",
                "summary": "Sync test brot",
                "status": "needs_action",
            }
        )
        if mode == "link":
            conflict = ctx.source.source_conflicts(ctx.data)[0]
            await ctx.source.resolve_source_conflict(
                env.hass,
                env.entry,
                "normalized",
                conflict["token"],
                "link",
                "normalized-source",
            )
    await ctx.source.synchronize_source(env.hass, env.entry)
    if mode == "rename":
        await ctx.protocol.apply_operation(
            ctx.data,
            "rename-normalized",
            "update_item",
            "normalized",
            {"summary": "NEUER   Name", "status": "completed"},
        )
        await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.data.source_error is None
    assert not ctx.source.source_conflicts(ctx.data)
    assert not ctx.data.sync["creates"]
    article = next(item for item in ctx.data.items if item.uid == "normalized")
    assert article.source_uid
    assert article.metadata == {"note": "Behalten"}
    writes = sum(service != "get_items" for service, _ in ctx.calls)
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.data.source_error is None
    assert sum(service != "get_items" for service, _ in ctx.calls) == writes


async def test_deleted_local_only_conflicts_are_not_existing_articles(
    integration, monkeypatch
):
    env = integration
    ctx = await conflict_environment(env, monkeypatch)
    await ctx.protocol.apply_operation(
        ctx.data, "delete-pending", "delete_item", "pending", {}
    )
    conflict = ctx.source.source_conflicts(ctx.data)[0]
    await ctx.source.resolve_source_conflict(
        env.hass, env.entry, "pending", conflict["token"], "local"
    )
    assert not ctx.source.source_conflicts(ctx.data, include_local=True)
    assert "pending" in ctx.data.sync["deleted"]
    assert ctx.data.sync["creates"]["pending"]["local_only"]
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert not any(service == "add_item" for service, _ in ctx.calls)


async def test_deleted_article_rejects_earlier_link_decision(integration, monkeypatch):
    env = integration
    ctx = await conflict_environment(env, monkeypatch, ambiguous=True)
    before = ctx.source.source_conflicts(ctx.data)[0]
    await ctx.protocol.apply_operation(
        ctx.data, "delete-pending", "delete_item", "pending", {}
    )
    after = ctx.source.source_conflicts(ctx.data)[0]
    assert after["token"] != before["token"]
    with pytest.raises(ValueError, match="bereits geändert"):
        await ctx.source.resolve_source_conflict(
            env.hass, env.entry, "pending", before["token"], "link", "b1"
        )
    assert not ctx.data.sync["deleted"]["pending"].get("source_uid")


async def test_normalized_names_still_require_unique_new_source(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.protocol.apply_operation(
        ctx.data, "add", "add_item", "new", {"summary": "BROT"}
    )
    service = env.hass.services.async_call.side_effect

    async def ambiguous(domain, name, payload, **kwargs):
        result = await service(domain, name, payload, **kwargs)
        if name == "add_item":
            ctx.remote[-1]["summary"] = "Brot"
            ctx.remote.append(
                {"uid": "second-bread", "summary": "brot", "status": "needs_action"}
            )
        return result

    env.hass.services.async_call.side_effect = ambiguous
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.source.source_conflicts(ctx.data)[0]["reason"] == "multiple"
    assert next(item for item in ctx.data.items if item.uid == "new").source_uid is None
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert sum(name == "add_item" for name, _ in ctx.calls) == 1


@pytest.mark.parametrize(
    "changes", [{"summary": "Anderer Artikel"}, {"status": "completed"}]
)
async def test_normalization_does_not_acknowledge_unapplied_changes(
    integration, monkeypatch, changes
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.source.synchronize_source(env.hass, env.entry)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(ctx.data, "change", "update_item", uid, changes)
    service = env.hass.services.async_call.side_effect

    async def ignored_write(domain, name, payload, **kwargs):
        if name == "update_item":
            ctx.remote[0]["summary"] = ctx.remote[0]["summary"].lower()
            return None
        return await service(domain, name, payload, **kwargs)

    env.hass.services.async_call.side_effect = ignored_write
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert "noch nicht bestätigt" in ctx.data.source_error
    assert ctx.data.sync["source"]["a"]["status"] == "needs_action"


@pytest.mark.parametrize("ambiguous", [False, True])
async def test_conflict_does_not_block_other_items_and_requires_explicit_decision(
    integration, monkeypatch, ambiguous
):
    env = integration
    ctx = await conflict_environment(env, monkeypatch, ambiguous=ambiguous)
    uid = ctx.data.items[0].uid
    ctx.remote[0]["status"] = "completed"
    ctx.remote.append({"uid": "other", "summary": "Obst", "status": "needs_action"})
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.data.items[0].status == "completed"
    assert any(item.source_uid == "other" for item in ctx.data.items)
    conflicts = ctx.source.source_conflicts(ctx.data)
    assert len(conflicts) == 1
    assert conflicts[0]["uid"] == "pending"
    assert conflicts[0]["reason"] == ("multiple" if ambiguous else "unconfirmed")
    if ambiguous:
        ctx.remote[:] = [item for item in ctx.remote if item["uid"] != "b2"]
    else:
        ctx.remote.append({"uid": "b1", "summary": "Brot", "status": "needs_action"})
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.source.source_conflicts(ctx.data)
    assert (
        next(item for item in ctx.data.items if item.uid == "pending").source_uid
        is None
    )
    assert not any(service == "add_item" for service, _ in ctx.calls)
    assert uid == ctx.data.items[0].uid


async def test_link_conflict_preserves_metadata_and_rejects_stale_second_device(
    integration, monkeypatch
):
    env = integration
    ctx = await conflict_environment(env, monkeypatch, ambiguous=True)
    token = ctx.source.source_conflicts(ctx.data)[0]["token"]
    await ctx.source.resolve_source_conflict(
        env.hass, env.entry, "pending", token, "link", "b1"
    )
    assert next(item for item in ctx.data.items if item.uid == "pending").metadata == {
        "note": "Behalten"
    }
    assert (
        next(item for item in ctx.data.items if item.uid == "pending").source_uid
        == "b1"
    )
    assert not ctx.source.source_conflicts(ctx.data)
    with pytest.raises(ValueError, match="bereits geändert"):
        await ctx.source.resolve_source_conflict(
            env.hass, env.entry, "pending", token, "retry"
        )
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert not any(service == "add_item" for service, _ in ctx.calls)


async def test_local_only_choice_survives_restart_and_never_recreates(
    integration, monkeypatch
):
    env = integration
    ctx = await conflict_environment(env, monkeypatch)
    token = ctx.source.source_conflicts(ctx.data)[0]["token"]
    await ctx.source.resolve_source_conflict(
        env.hass, env.entry, "pending", token, "local"
    )
    env.store.async_load.return_value = env.store.async_save.call_args.args[0]
    await env.package.async_setup_entry(env.hass, env.entry)
    for _ in range(2):
        await ctx.source.synchronize_source(env.hass, env.entry)
    data = env.entry.runtime_data
    assert next(item for item in data.items if item.uid == "pending").metadata == {
        "note": "Behalten"
    }
    assert not ctx.source.source_conflicts(data)
    assert not any(service == "add_item" for service, _ in ctx.calls)
    assert data.source_error is None
    local = ctx.source.source_conflicts(data, include_local=True)[0]
    assert local["token"] != token
    with pytest.raises(ValueError):
        await ctx.source.resolve_source_conflict(
            env.hass, env.entry, "pending", token, "retry"
        )
    await ctx.source.resolve_source_conflict(
        env.hass, env.entry, "pending", local["token"], "retry"
    )
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert any(service == "add_item" for service, _ in ctx.calls)


async def test_product_category_survives_deletion_restart_and_source_recreation(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(
        ctx.data,
        "assign",
        "update_item",
        uid,
        {"metadata": {"category_id": "dairy", "quantity": "2"}},
    )
    await ctx.protocol.apply_operation(ctx.data, "delete", "delete_item", uid, {})
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert not ctx.data.items
    env.store.async_load.return_value = env.store.async_save.call_args.args[0]
    await env.package.async_setup_entry(env.hass, env.entry)
    ctx.remote.append(
        {"uid": "milk-new", "summary": " MILCH ", "status": "needs_action"}
    )
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert env.entry.runtime_data.items[0].metadata == {"category_id": "dairy"}
    assert env.entry.runtime_data.items[0].source_uid == "milk-new"
    assert env.entry.runtime_data.items[0].uid != uid


async def test_product_removal_clears_all_lists_without_deleting_articles_and_never_relearns(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(
        ctx.data,
        "assign",
        "update_item",
        uid,
        {"metadata": {"category_id": "dairy", "note": "bio"}},
    )
    second = SimpleNamespace(
        entry_id="second",
        domain="einkaufszettel",
        data={"name": "Zweite Liste"},
        options={},
    )
    await env.package.async_setup_entry(env.hass, second)
    protocol = ctx.protocol
    await protocol.apply_operation(
        second.runtime_data, "add", "add_item", "second-milk", {"summary": "milch"}
    )
    assert second.runtime_data.items[-1].metadata["category_id"] == "dairy"
    second_before = list(second.runtime_data.items)
    connection = Mock(user=SimpleNamespace(is_admin=True))
    await env.websocket.websocket_remove_category_product(
        env.hass,
        connection,
        {
            "id": 1,
            "type": "einkaufszettel/remove_category_product",
            "category_id": "dairy",
            "product_key": "milch",
        },
    )
    connection.send_error.assert_not_called()
    assert (
        connection.send_result.call_args.args[1]["products"][0]["category_id"] is None
    )
    await protocol.persist_items(ctx.data, ctx.data.items)
    await protocol.persist_items(second.runtime_data, second_before)
    assert len(ctx.data.items) == 1
    assert ctx.data.items[0].metadata == {"category_id": None, "note": "bio"}
    assert all(
        item.metadata["category_id"] is None for item in second.runtime_data.items
    )
    # A stale article saved again must not teach the removed category anew.
    await protocol.persist_items(second.runtime_data, second_before)
    assert all(
        item.metadata["category_id"] is None for item in second.runtime_data.items
    )
    await protocol.apply_operation(
        ctx.data, "new", "add_item", "new-milk", {"summary": "MILCH"}
    )
    assert ctx.data.items[-1].metadata["category_id"] is None
    await protocol.apply_operation(
        ctx.data, "manual", "update_item", uid, {"metadata": {"category_id": "dairy"}}
    )
    assert all(item.metadata["category_id"] == "dairy" for item in ctx.data.items)


async def test_product_assignment_retry_cannot_undo_later_manual_removal(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    uid = ctx.data.items[0].uid
    patch = {"metadata": {"category_id": "dairy"}}
    env.store.async_save.side_effect = OSError("list disk full")
    with pytest.raises(OSError):
        await ctx.protocol.apply_operation(ctx.data, "once", "update_item", uid, patch)
    assert "once" not in ctx.data.sync["receipts"]
    connection = Mock(user=SimpleNamespace(is_admin=True))
    await env.websocket.websocket_remove_category_product(
        env.hass,
        connection,
        {
            "id": 1,
            "type": "einkaufszettel/remove_category_product",
            "category_id": "dairy",
            "product_key": "milch",
        },
    )
    connection.send_error.assert_not_called()
    env.store.async_save.side_effect = None
    await ctx.protocol.apply_operation(ctx.data, "once", "update_item", uid, patch)
    assert ctx.data.items[0].metadata["category_id"] is None
    assert "once" in ctx.data.sync["receipts"]


async def test_product_retry_after_source_rename_keeps_original_assignment(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    uid = ctx.data.items[0].uid
    patch = {"metadata": {"category_id": "dairy"}}
    env.store.async_save.side_effect = OSError("list full")
    with pytest.raises(OSError):
        await ctx.protocol.apply_operation(ctx.data, "once", "update_item", uid, patch)
    env.store.async_save.side_effect = None
    ctx.data.items = [env.model.ShoppingItem(uid, "Hafermilch")]
    await ctx.protocol.apply_operation(ctx.data, "once", "update_item", uid, patch)
    catalog = await env.stores["einkaufszettel.supermarkets"].async_load()
    assert (
        next(product for product in catalog["products"] if product["key"] == "milch")[
            "category_id"
        ]
        == "dairy"
    )
    assert ctx.data.items[0].metadata["category_id"] == "dairy"


async def test_product_catalog_save_failure_does_not_acknowledge_assignment(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    env.stores["einkaufszettel.supermarkets"].async_save.side_effect = OSError(
        "catalog full"
    )
    with pytest.raises(OSError, match="catalog full"):
        await ctx.protocol.apply_operation(
            ctx.data,
            "assign",
            "update_item",
            ctx.data.items[0].uid,
            {"metadata": {"category_id": "dairy"}},
        )
    assert "assign" not in ctx.data.sync["receipts"]
    assert not ctx.data.items[0].metadata


async def test_migration_seeds_completed_and_deleted_items_but_respects_removal_markers(
    integration,
):
    env = integration
    await env.package.async_setup_entry(env.hass, env.entry)
    store = env.stores["einkaufszettel.supermarkets"]
    catalog = {
        "categories": [{"id": "dairy", "name": "Milchprodukte"}],
        "products": [{"key": "milch", "name": "Milch", "category_id": None}],
    }
    store.async_load.side_effect = lambda: deepcopy(catalog)

    async def save(value):
        nonlocal catalog
        catalog = deepcopy(value)

    store.async_save.side_effect = save
    state = importlib.import_module(f"{env.package.__name__}.sync").new_sync_state()
    state["deleted"]["deleted"] = env.model.ShoppingItem(
        "deleted", "Quark", metadata={"category_id": "dairy"}
    ).to_dict()
    env.store.async_load.return_value = {
        "items": [
            env.model.ShoppingItem(
                "milk", "Milch", metadata={"category_id": "dairy"}
            ).to_dict(),
            env.model.ShoppingItem(
                "yoghurt", "Joghurt", "completed", metadata={"category_id": "dairy"}
            ).to_dict(),
        ],
        "sync": state,
    }
    await env.package.async_setup_entry(env.hass, env.entry)
    rules = {product["key"]: product["category_id"] for product in catalog["products"]}
    assert rules == {"milch": None, "joghurt": "dairy", "quark": "dairy"}
    assert env.entry.runtime_data.items[0].metadata["category_id"] is None
    assert len(env.entry.runtime_data.items) == 2


@pytest.mark.parametrize("admin", [True, False])
async def test_product_remove_revalidates_category_and_permissions(
    integration, monkeypatch, admin
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.protocol.apply_operation(
        ctx.data,
        "assign",
        "update_item",
        ctx.data.items[0].uid,
        {"metadata": {"category_id": "dairy"}},
    )
    connection = Mock(user=SimpleNamespace(is_admin=admin))
    await env.websocket.websocket_remove_category_product(
        env.hass,
        connection,
        {
            "id": 1,
            "type": "einkaufszettel/remove_category_product",
            "category_id": "wrong-category",
            "product_key": "milch",
        },
    )
    connection.send_error.assert_called_once()
    connection.send_result.assert_not_called()
    assert ctx.data.items[0].metadata["category_id"] == "dairy"


async def test_get_list_projects_product_rules_without_source_write(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.protocol.apply_operation(
        ctx.data,
        "assign",
        "update_item",
        ctx.data.items[0].uid,
        {"metadata": {"category_id": "dairy"}},
    )
    # Existing items on another list can still contain an older materialized value.
    ctx.data.items = [
        env.model.ShoppingItem("other", "MILCH", metadata={"quantity": "4"})
    ]
    env.entry.domain = "einkaufszettel"
    env.hass.config_entries.async_get_entry.return_value = env.entry
    connection = Mock()
    ctx.calls.clear()
    await env.websocket.websocket_get_list(
        env.hass, connection, {"id": 8, "entry_id": env.entry.entry_id}
    )
    assert connection.send_result.call_args.args[1]["items"][0]["metadata"] == {
        "category_id": "dairy",
        "quantity": "4",
    }
    assert not ctx.calls


async def test_explicit_retry_creates_once_and_rejects_replayed_decision(
    integration, monkeypatch
):
    env = integration
    ctx = await conflict_environment(env, monkeypatch)
    token = ctx.source.source_conflicts(ctx.data)[0]["token"]
    await ctx.source.resolve_source_conflict(
        env.hass, env.entry, "pending", token, "retry"
    )
    with pytest.raises(ValueError):
        await ctx.source.resolve_source_conflict(
            env.hass, env.entry, "pending", token, "retry"
        )
    await ctx.source.synchronize_source(env.hass, env.entry)
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert sum(service == "add_item" for service, _ in ctx.calls) == 1
    assert not ctx.source.source_conflicts(ctx.data)


@pytest.mark.parametrize("invalid", ["linked", "missing", "retired"])
async def test_link_conflict_revalidates_target_and_keeps_intent_on_error(
    integration, monkeypatch, invalid
):
    env = integration
    ctx = await conflict_environment(env, monkeypatch, ambiguous=True)
    token = ctx.source.source_conflicts(ctx.data)[0]["token"]
    target = "a" if invalid == "linked" else "b1"
    if invalid == "missing":
        ctx.remote[:] = [item for item in ctx.remote if item["uid"] != "b1"]
    if invalid == "retired":
        ctx.data.sync["source"]["b1"] = {
            "summary": "Brot",
            "status": "completed",
            "present": True,
            "superseded": True,
        }
    with pytest.raises(ValueError, match="fehlt oder"):
        await ctx.source.resolve_source_conflict(
            env.hass, env.entry, "pending", token, "link", target
        )
    assert "pending" in ctx.data.sync["creates"]


async def test_failed_resolution_save_does_not_consume_conflict(
    integration, monkeypatch
):
    env = integration
    ctx = await conflict_environment(env, monkeypatch, ambiguous=True)
    token = ctx.source.source_conflicts(ctx.data)[0]["token"]
    env.store.async_save.side_effect = OSError("disk full")
    with pytest.raises(OSError):
        await ctx.source.resolve_source_conflict(
            env.hass, env.entry, "pending", token, "link", "b1"
        )
    assert "pending" in ctx.data.sync["creates"]
    assert (
        next(item for item in ctx.data.items if item.uid == "pending").source_uid
        is None
    )


async def test_inflight_create_is_not_presented_as_a_decision(integration, monkeypatch):
    ctx = await sync_environment(integration, monkeypatch)
    state = deepcopy(ctx.data.sync)
    state["creates"]["new"] = {"before": ["a"], "summary": "Brot"}
    await ctx.protocol.persist_items(ctx.data, ctx.data.items, state)
    assert not ctx.source.source_conflicts(ctx.data)
    assert not ctx.source.source_conflicts(ctx.data, include_local=True)


@pytest.mark.parametrize("failure", [None, "save", "stale", "list"])
async def test_conflict_websocket_persists_before_ack_and_returns_scoped_snapshot(
    integration, monkeypatch, failure
):
    env = integration
    ctx = await conflict_environment(env, monkeypatch, ambiguous=True)
    env.entry.domain = "einkaufszettel"
    env.hass.config_entries.async_get_entry.side_effect = (
        lambda key: env.entry if key == env.entry.entry_id else None
    )
    conflict = ctx.source.source_conflicts(ctx.data)[0]
    connection = Mock()
    env.dispatcher.async_dispatcher_send.reset_mock()
    if failure == "save":
        env.store.async_save.side_effect = OSError("disk full")
    await env.websocket.websocket_resolve_source_conflict(
        env.hass,
        connection,
        {
            "id": 73,
            "entry_id": "missing" if failure == "list" else env.entry.entry_id,
            "uid": "pending",
            "token": "outdated" if failure == "stale" else conflict["token"],
            "action": "local",
        },
    )
    if failure:
        connection.send_result.assert_not_called()
        connection.send_error.assert_called_once()
        env.dispatcher.async_dispatcher_send.assert_not_called()
        assert ctx.source.source_conflicts(ctx.data)
    else:
        connection.send_error.assert_not_called()
        snapshot = connection.send_result.call_args.args[1]
        assert snapshot["entry_id"] == env.entry.entry_id
        assert snapshot["source_conflicts"] == []
        assert snapshot["source_local_items"][0]["uid"] == "pending"
        saved = env.store.async_save.call_args.args[0]
        assert saved["sync"]["creates"]["pending"]["local_only"]
        env.dispatcher.async_dispatcher_send.assert_called_once()


async def test_deleted_conflict_links_for_deletion_but_cannot_retry(
    integration, monkeypatch
):
    env = integration
    ctx = await conflict_environment(env, monkeypatch, ambiguous=True)
    await ctx.protocol.apply_operation(
        ctx.data, "delete-pending", "delete_item", "pending", {}
    )
    conflict = ctx.source.source_conflicts(ctx.data)[0]
    assert conflict["deleted"]
    with pytest.raises(ValueError, match="gelöschter"):
        await ctx.source.resolve_source_conflict(
            env.hass, env.entry, "pending", conflict["token"], "retry"
        )
    await ctx.source.resolve_source_conflict(
        env.hass, env.entry, "pending", conflict["token"], "link", "b1"
    )
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert not any(item.uid == "pending" for item in ctx.data.items)
    assert not any(item["uid"] == "b1" for item in ctx.remote)
    assert not any(service == "add_item" for service, _ in ctx.calls)


async def test_failed_create_does_not_block_next_article(integration, monkeypatch):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    for uid, summary in (("first", "Brot"), ("second", "Obst")):
        await ctx.protocol.apply_operation(
            ctx.data, uid, "add_item", uid, {"summary": summary}
        )
    real_service = env.hass.services.async_call.side_effect

    async def service(domain, service, payload, **kwargs):
        if service == "add_item" and payload["item"] == "Brot":
            raise TimeoutError("reply lost")
        return await real_service(domain, service, payload, **kwargs)

    env.hass.services.async_call.side_effect = service
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.source.source_conflicts(ctx.data)[0]["uid"] == "first"
    assert next(item for item in ctx.data.items if item.uid == "second").source_uid
    assert ctx.data.source_error


@pytest.mark.parametrize("same_poll", [False, True])
async def test_alexa_readd_reuses_completed_item_and_retires_old_identity(
    integration, monkeypatch, same_poll
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.source.synchronize_source(env.hass, env.entry)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(
        ctx.data,
        "metadata",
        "update_item",
        uid,
        {
            "metadata": {"category_id": "dairy", "quantity": "2", "note": "bio"},
            "description": "Behalten",
        },
    )
    ctx.remote[0]["status"] = "completed"
    if not same_poll:
        await ctx.source.synchronize_source(env.hass, env.entry)
    ctx.remote.append(
        {"uid": "new-milk", "summary": "  MILCH  ", "status": "needs_action"}
    )
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert len(ctx.data.items) == 1
    item = ctx.data.items[0]
    assert (item.uid, item.source_uid, item.status) == (uid, "new-milk", "needs_action")
    assert item.metadata == {"category_id": "dairy", "quantity": "2", "note": "bio"}
    assert item.description == "Behalten"
    assert ctx.data.sync["source"]["a"]["superseded"] is True
    env.store.async_load.return_value = env.store.async_save.call_args.args[0]
    await env.package.async_setup_entry(env.hass, env.entry)
    ctx.remote[0]["status"] = "needs_action"
    await ctx.source.synchronize_source(env.hass, env.entry)
    data = env.entry.runtime_data
    assert len(data.items) == 1
    assert data.items[0].source_uid == "new-milk"
    assert data.items[0].status == "needs_action"
    assert not any(service != "get_items" for service, _ in ctx.calls)


@pytest.mark.parametrize(
    "case", ["open", "multiple_completed", "multiple_new", "different_name"]
)
async def test_source_readd_never_guesses_ambiguous_or_open_match(
    integration, monkeypatch, case
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.source.synchronize_source(env.hass, env.entry)
    if case != "open":
        ctx.remote[0]["status"] = "completed"
    if case == "multiple_completed":
        ctx.data.items.append(env.model.ShoppingItem("other", "Milch", "completed"))
    await ctx.source.synchronize_source(env.hass, env.entry)
    before = len(ctx.data.items)
    ctx.remote.append(
        {
            "uid": "new",
            "summary": "Hafermilch" if case == "different_name" else "Milch",
            "status": "needs_action",
        }
    )
    if case == "multiple_new":
        ctx.remote.append({"uid": "new2", "summary": "MILCH", "status": "needs_action"})
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert len(ctx.data.items) == before + (2 if case == "multiple_new" else 1)
    assert ctx.data.items[0].source_uid == "a"


async def test_source_readd_failed_save_leaves_old_mapping_intact(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.source.synchronize_source(env.hass, env.entry)
    ctx.remote[0]["status"] = "completed"
    await ctx.source.synchronize_source(env.hass, env.entry)
    ctx.remote.append({"uid": "new", "summary": "Milch", "status": "needs_action"})
    env.store.async_save.side_effect = OSError("disk full")
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert len(ctx.data.items) == 1
    assert ctx.data.items[0].source_uid == "a"
    assert not ctx.data.sync["source"]["a"].get("superseded")
    env.store.async_save.side_effect = None
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert len(ctx.data.items) == 1
    assert ctx.data.items[0].source_uid == "new"


async def test_repeated_readds_normalize_whitespace_and_delete_only_current_source(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.source.synchronize_source(env.hass, env.entry)
    ctx.remote[0]["summary"] = "Frische Milch"
    await ctx.source.synchronize_source(env.hass, env.entry)
    uid = ctx.data.items[0].uid
    for source_uid, name in (
        ("second", " FRISCHE\t Milch "),
        ("third", "frische   milch"),
    ):
        ctx.remote[-1]["status"] = "completed"
        ctx.remote.append(
            {"uid": source_uid, "summary": name, "status": "needs_action"}
        )
        await ctx.source.synchronize_source(env.hass, env.entry)
        assert len(ctx.data.items) == 1
        assert ctx.data.items[0].uid == uid
        assert ctx.data.items[0].source_uid == source_uid
    # Even a stale source reopening must not be copied back through the old API.
    ctx.remote[0]["status"] = "needs_action"
    button = env.button.CopySourceButton(env.entry)
    button.hass = env.hass
    await button.async_press()
    assert len(ctx.data.items) == 1
    await ctx.protocol.apply_operation(ctx.data, "delete", "delete_item", uid, {})
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert {item["uid"] for item in ctx.remote} == {"a", "second"}
    assert not ctx.data.items


async def test_receipts_survive_restart_and_retry_does_not_overwrite_newer_edit(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(
        ctx.data, "first", "update_item", uid, {"summary": "A"}
    )
    await ctx.protocol.apply_operation(
        ctx.data, "second", "update_item", uid, {"summary": "B"}
    )
    saved = env.store.async_save.call_args.args[0]
    env.store.async_load.return_value = saved
    await env.package.async_setup_entry(env.hass, env.entry)
    data = env.entry.runtime_data
    revision = data.sync["revision"]
    await ctx.protocol.apply_operation(
        data, "first", "update_item", uid, {"summary": "A"}
    )
    assert data.items[0].summary == "B"
    assert data.sync["revision"] == revision
    with pytest.raises(ValueError, match="already used"):
        await ctx.protocol.apply_operation(
            data, "first", "update_item", uid, {"summary": "C"}
        )


async def test_field_patches_preserve_metadata_and_last_accepted_field_wins(
    integration, monkeypatch
):
    ctx = await sync_environment(integration, monkeypatch)
    uid = ctx.data.items[0].uid
    for op, patch in (
        ("category", {"metadata": {"category_id": "dairy", "quantity": "2"}}),
        ("status", {"status": "completed"}),
        ("quantity", {"metadata": {"quantity": "3", "note": "bio"}}),
        ("rename", {"summary": "Hafermilch"}),
    ):
        await ctx.protocol.apply_operation(ctx.data, op, "update_item", uid, patch)
    item = ctx.data.items[0]
    assert item.summary == "Hafermilch"
    assert item.status == "completed"
    assert item.metadata == {"category_id": "dairy", "quantity": "3", "note": "bio"}
    assert ctx.data.sync["revision"] == 4


async def test_delete_wins_over_delayed_edit_and_creation(integration, monkeypatch):
    ctx = await sync_environment(integration, monkeypatch)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(ctx.data, "delete", "delete_item", uid, {})
    for op, action in (("late-edit", "update_item"), ("late-add", "add_item")):
        assert (
            await ctx.protocol.apply_operation(
                ctx.data, op, action, uid, {"summary": "Wieder da"}
            )
            == "deleted"
        )
    assert not ctx.data.items
    assert ctx.data.sync["deleted"][uid]["source_uid"] == "a"
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    assert not ctx.remote
    assert not ctx.data.items
    assert ctx.data.source_error is None


async def test_failed_operation_save_does_not_publish_or_acknowledge(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    uid = ctx.data.items[0].uid
    env.store.async_save.side_effect = OSError("disk full")
    env.hass.config_entries.async_get_entry.return_value = env.entry
    env.entry.domain = "einkaufszettel"
    connection = Mock()
    await env.websocket.websocket_apply_operation(
        env.hass,
        connection,
        {
            "id": 42,
            "entry_id": env.entry.entry_id,
            "operation_id": "save-fails",
            "action": "delete_item",
            "uid": uid,
            "changes": {},
        },
    )
    connection.send_result.assert_not_called()
    connection.send_error.assert_called_once()
    assert ctx.data.items[0].uid == uid
    assert not ctx.data.sync["receipts"]
    assert not ctx.data.sync["deleted"]


async def test_source_updates_preserve_local_metadata_and_do_not_echo(
    integration, monkeypatch
):
    ctx = await sync_environment(integration, monkeypatch)
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(
        ctx.data,
        "meta",
        "update_item",
        uid,
        {
            "metadata": {"product_id": "p1", "unit": "l", "quantity": "2"},
            "description": "Nur unsere Notiz",
        },
    )
    ctx.remote[0].update(summary="Sojamilch", status="completed")
    ctx.calls.clear()
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    item = ctx.data.items[0]
    assert (item.summary, item.status) == ("Sojamilch", "completed")
    assert item.description == "Nur unsere Notiz"
    assert item.metadata == {"product_id": "p1", "unit": "l", "quantity": "2"}
    assert all(service == "get_items" for service, _ in ctx.calls)


async def test_source_three_way_merge_writes_only_locally_changed_fields(
    integration, monkeypatch
):
    ctx = await sync_environment(integration, monkeypatch)
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(
        ctx.data, "local", "update_item", uid, {"summary": "Hafermilch"}
    )
    ctx.remote[0]["status"] = "completed"
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    assert ctx.data.items[0].summary == ctx.remote[0]["summary"] == "Hafermilch"
    assert ctx.data.items[0].status == ctx.remote[0]["status"] == "completed"
    writes = [payload for service, payload in ctx.calls if service == "update_item"]
    assert writes == [{"entity_id": "todo.alexa", "item": "a", "rename": "Hafermilch"}]
    ctx.calls.clear()
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    assert all(service == "get_items" for service, _ in ctx.calls)


async def test_source_change_observed_later_wins_same_field(integration, monkeypatch):
    ctx = await sync_environment(integration, monkeypatch)
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    await ctx.protocol.apply_operation(
        ctx.data, "rename", "update_item", ctx.data.items[0].uid, {"summary": "Lokal"}
    )
    ctx.remote[0]["summary"] = "Alexa"
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    assert ctx.data.items[0].summary == "Alexa"
    assert not any(service == "update_item" for service, _ in ctx.calls)


async def test_source_missing_means_completed_not_destroyed_and_reopen_creates_new_id(
    integration, monkeypatch
):
    ctx = await sync_environment(integration, monkeypatch)
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(
        ctx.data, "meta", "update_item", uid, {"metadata": {"note": "Behalten"}}
    )
    ctx.remote.clear()
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    assert ctx.data.items[0].status == "completed"
    assert ctx.data.items[0].metadata == {"note": "Behalten"}
    await ctx.protocol.apply_operation(
        ctx.data, "reopen", "update_item", uid, {"status": "needs_action"}
    )
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    assert ctx.data.items[0].uid == uid
    assert ctx.data.items[0].source_uid != "a"
    assert len(ctx.remote) == 1
    assert ctx.data.source_error is None


async def test_equal_names_keep_distinct_ids_on_both_sides(integration, monkeypatch):
    ctx = await sync_environment(integration, monkeypatch)
    await ctx.protocol.apply_operation(
        ctx.data, "add", "add_item", "local-second", {"summary": "Milch"}
    )
    ctx.remote.append(
        {"uid": "remote-second", "summary": "Milch", "status": "needs_action"}
    )
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    assert len(ctx.data.items) == len(ctx.remote) == 3
    assert len({item.source_uid for item in ctx.data.items}) == 3
    assert ctx.data.source_error is None


async def test_ambiguous_source_creation_is_not_retried_after_restart(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.protocol.apply_operation(
        ctx.data, "add", "add_item", "new", {"summary": "Brot"}
    )
    real_service = env.hass.services.async_call.side_effect

    async def uncertain(domain, service, payload, **kwargs):
        if service == "add_item":
            await real_service(domain, service, payload, **kwargs)
            raise TimeoutError("response lost")
        return await real_service(domain, service, payload, **kwargs)

    env.hass.services.async_call.side_effect = uncertain
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert "new" in ctx.data.sync["creates"]
    assert ctx.data.source_error
    saved = env.store.async_save.call_args.args[0]
    env.store.async_load.return_value = saved
    await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.side_effect = real_service
    await ctx.source.synchronize_source(env.hass, env.entry)
    data = env.entry.runtime_data
    conflict = ctx.source.source_conflicts(data)[0]
    assert conflict["candidates"][0]["uid"] == ctx.remote[-1]["uid"]
    assert data.source_error
    await ctx.source.resolve_source_conflict(
        env.hass, env.entry, "new", conflict["token"], "link", ctx.remote[-1]["uid"]
    )
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert not data.sync["creates"]
    assert len(ctx.remote) == 2
    assert sum(service == "add_item" for service, _ in ctx.calls) == 1
    assert data.source_error is None


async def test_unconfirmed_source_creation_does_not_guess_or_duplicate(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.protocol.apply_operation(
        ctx.data, "add", "add_item", "new", {"summary": "Brot"}
    )
    real_service = env.hass.services.async_call.side_effect
    attempts = 0

    async def uncertain(domain, service, payload, **kwargs):
        nonlocal attempts
        if service == "add_item":
            attempts += 1
            raise TimeoutError("request outcome unknown")
        return await real_service(domain, service, payload, **kwargs)

    env.hass.services.async_call.side_effect = uncertain
    await ctx.source.synchronize_source(env.hass, env.entry)
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert attempts == 1
    assert len(ctx.data.items) == 2
    assert "Sync-Konflikte auflösen" in ctx.data.source_error
    assert ctx.source.source_conflicts(ctx.data)[0]["reason"] == "unconfirmed"
    assert "new" in ctx.data.sync["creates"]


@pytest.mark.parametrize("bad_response", [None, {}, {"todo.alexa": {"items": None}}])
async def test_failed_source_read_does_not_remove_any_items(
    integration, monkeypatch, bad_response
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    before = list(ctx.data.items)
    env.hass.services.async_call.side_effect = None
    env.hass.services.async_call.return_value = bad_response
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.data.items == before
    assert ctx.data.source_error
    assert not ctx.data.sync["deleted"]


async def test_read_only_source_keeps_local_edits_and_exposes_pending_error(
    integration, monkeypatch
):
    ctx = await sync_environment(integration, monkeypatch, features=0)
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    await ctx.protocol.apply_operation(
        ctx.data, "edit", "update_item", ctx.data.items[0].uid, {"summary": "Lokal"}
    )
    await ctx.protocol.apply_operation(
        ctx.data, "add", "add_item", "new", {"summary": "Brot"}
    )
    await ctx.source.synchronize_source(integration.hass, integration.entry)
    assert ctx.data.items[0].summary == "Lokal"
    assert ctx.remote[0]["summary"] == "Milch"
    assert "unterstützt" in ctx.data.source_error
    assert all(service == "get_items" for service, _ in ctx.calls)


async def test_corrupt_receipts_abort_startup_instead_of_forgetting_history(
    integration,
):
    env = integration
    sync = importlib.import_module(f"{env.package.__name__}.sync")
    state = sync.new_sync_state()
    state["receipts"]["x"] = {"result": "applied"}
    env.store.async_load.return_value = {"items": [], "sync": state}
    with pytest.raises(env.not_ready, match="receipt"):
        await env.package.async_setup_entry(env.hass, env.entry)
    env.hass.services.async_call.assert_not_awaited()


async def test_source_write_then_failed_save_recovers_without_losing_local_fields(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.source.synchronize_source(env.hass, env.entry)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(
        ctx.data,
        "edit",
        "update_item",
        uid,
        {
            "summary": "Hafermilch",
            "metadata": {"quantity": "2"},
        },
    )
    env.store.async_save.side_effect = OSError("disk full")
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.remote[0]["summary"] == "Hafermilch"
    assert ctx.data.source_error == "disk full"
    assert ctx.data.items[0].metadata == {"quantity": "2"}
    env.store.async_save.side_effect = None
    ctx.calls.clear()
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.data.source_error is None
    assert ctx.data.sync["source"]["a"]["summary"] == "Hafermilch"
    assert not any(service == "update_item" for service, _ in ctx.calls)


async def test_ambiguous_new_source_ids_remain_unlinked_and_are_not_created_twice(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    await ctx.protocol.apply_operation(
        ctx.data, "add", "add_item", "new", {"summary": "Brot"}
    )
    real_service = env.hass.services.async_call.side_effect

    async def racing(domain, service, payload, **kwargs):
        result = await real_service(domain, service, payload, **kwargs)
        if service == "add_item":
            ctx.remote.append(
                {
                    "uid": "other-new",
                    "summary": payload["item"],
                    "status": "needs_action",
                }
            )
        return result

    env.hass.services.async_call.side_effect = racing
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.data.source_error
    assert next(item for item in ctx.data.items if item.uid == "new").source_uid is None
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert "Sync-Konflikte auflösen" in ctx.data.source_error
    assert ctx.source.source_conflicts(ctx.data)[0]["reason"] == "multiple"
    assert sum(service == "add_item" for service, _ in ctx.calls) == 1


async def test_deleted_metadata_and_source_mapping_survive_restart(
    integration, monkeypatch
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    uid = ctx.data.items[0].uid
    await ctx.protocol.apply_operation(
        ctx.data, "meta", "update_item", uid, {"metadata": {"note": "bio"}}
    )
    await ctx.protocol.apply_operation(ctx.data, "delete", "delete_item", uid, {})
    env.store.async_load.return_value = env.store.async_save.call_args.args[0]
    await env.package.async_setup_entry(env.hass, env.entry)
    data = env.entry.runtime_data
    assert data.sync["deleted"][uid]["metadata"] == {"note": "bio"}
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert not data.items
    assert not ctx.remote
    assert (
        await ctx.protocol.apply_operation(
            data, "delayed", "add_item", uid, {"summary": "Alt"}
        )
        == "deleted"
    )


@pytest.mark.parametrize(
    "bad_items",
    [
        [
            {"uid": "x", "summary": "A", "status": "needs_action"},
            {"uid": "x", "summary": "B", "status": "completed"},
        ],
        [{"summary": "A", "status": "needs_action"}],
    ],
)
async def test_invalid_source_identity_never_imports_or_deletes(
    integration, monkeypatch, bad_items
):
    env = integration
    ctx = await sync_environment(env, monkeypatch)
    before = list(ctx.data.items)
    env.hass.services.async_call.side_effect = None
    env.hass.services.async_call.return_value = {"todo.alexa": {"items": bad_items}}
    await ctx.source.synchronize_source(env.hass, env.entry)
    assert ctx.data.items == before
    assert ctx.data.source_error
    assert not ctx.data.sync["deleted"]


async def test_source_timer_registered_and_cancelled_on_unload(integration):
    env = integration
    events = sys.modules["homeassistant.helpers.event"]
    await env.package.async_setup_entry(env.hass, env.entry)
    callback = events.async_track_time_interval.call_args.args[1]
    assert events.async_track_time_interval.call_args.args[2].total_seconds() == 30
    env.hass.services.async_call.side_effect = env.error("Offline")
    await callback(None)
    assert env.entry.runtime_data.source_error == "Offline"
    assert await env.package.async_unload_entry(env.hass, env.entry)
    events.async_track_time_interval.return_value.assert_called_once()
