"""Test our lifecycle logic with explicit HA boundary doubles, not a HA runtime."""

import asyncio
import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

ROOT = Path(__file__).parents[2] / "custom_components" / "easy_shopping"


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

    @dataclass
    class Item:
        uid: str
        summary: str
        status: Status
        description: str | None = None
        due: object = None

    store = SimpleNamespace(
        async_load=AsyncMock(return_value=None),
        async_save=AsyncMock(),
    )

    class Store(Generic):
        def __new__(cls, *args):
            return store

    module("homeassistant")
    module("homeassistant.config_entries", ConfigEntry=Generic)
    module(
        "homeassistant.const",
        Platform=SimpleNamespace(TODO="todo"),
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
    module("homeassistant.helpers.storage", Store=Store)
    module(
        "homeassistant.helpers.entity_registry",
        async_get=lambda hass: SimpleNamespace(async_get=lambda entity_id: None),
    )
    module(
        "homeassistant.helpers.entity_platform", AddConfigEntryEntitiesCallback=object
    )
    module("homeassistant.components")
    module(
        "homeassistant.components.todo",
        TodoItem=Item,
        TodoItemStatus=Status,
        TodoListEntity=Entity,
        TodoListEntityFeature=Features,
    )
    spec = importlib.util.spec_from_file_location(
        "easy_shopping_boundary_test",
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    package = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, package)
    spec.loader.exec_module(package)
    todo = importlib.import_module(f"{spec.name}.todo")
    model = importlib.import_module(f"{spec.name}.model")
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
        ),
    )
    entry = SimpleNamespace(
        entry_id="test-entry",
        data={"source_entity_id": "todo.alexa", "name": "Easy Shopping"},
    )
    yield SimpleNamespace(
        package=package,
        todo=todo,
        model=model,
        hass=hass,
        entry=entry,
        store=store,
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
    entity = env.todo.EasyShoppingTodo(data, "entry-id", "Easy Shopping")
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
    entity = env.todo.EasyShoppingTodo(
        env.entry.runtime_data, "entry-id", "Easy Shopping"
    )
    item = entity.todo_items[0]
    item.status = "completed"
    await entity.async_update_todo_item(item)
    assert env.entry.runtime_data.items[0].status == "completed"
