"""Exercise the Config Flow, services, entity lifecycle and persistence in HA."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.einkaufszettel.const import DOMAIN

SOURCE = "todo.alexa"


class SourceList(TodoListEntity):
    """Expose actual HA To-do services rather than mocking get_items."""

    _attr_name = "Alexa"
    _attr_should_poll = False
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM
    _attr_todo_items = [
        TodoItem(uid="source-1", summary="Milch", status=TodoItemStatus.NEEDS_ACTION),
        TodoItem(
            uid="source-2",
            summary="Brot",
            status=TodoItemStatus.NEEDS_ACTION,
            description="Vom Baecker",
        ),
        TodoItem(uid="source-3", summary="Eier", status=TodoItemStatus.COMPLETED),
    ]
    entity_id = SOURCE


@pytest.fixture
async def source(hass: HomeAssistant):
    assert await async_setup_component(hass, "todo", {})
    entity = SourceList()
    await hass.data["todo"].async_add_entities([entity])
    return entity


async def setup_copy(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Einkaufszettel",
        unique_id=SOURCE,
        data={"source_entity_id": SOURCE, "name": "Einkaufszettel"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def read_items(hass: HomeAssistant):
    result = await hass.services.async_call(
        "todo",
        "get_items",
        {
            "entity_id": "todo.einkaufszettel",
            "status": ["needs_action", "completed"],
        },
        blocking=True,
        return_response=True,
    )
    return result["todo.einkaufszettel"]["items"]


async def test_flow_uses_todo_selector_and_creates_entry(hass, source):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    fields = result["data_schema"].schema
    selector = next(value for key, value in fields.items() if key == "source_entity_id")
    assert selector.config["domain"] == "todo"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"source_entity_id": SOURCE, "name": "Einkaufszettel"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"source_entity_id": SOURCE, "name": "Einkaufszettel"}
    await hass.async_block_till_done()
    assert hass.states.get("todo.einkaufszettel").state == "2"


async def test_flow_reports_unavailable_source(hass, source):
    hass.states.async_set(SOURCE, "unavailable")
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={"source_entity_id": SOURCE, "name": "Einkaufszettel"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_read_source"}


async def test_flow_rejects_blank_name(hass, source):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={"source_entity_id": SOURCE, "name": "   "},
    )
    assert result["errors"] == {"name": "empty_name"}


async def test_flow_prevents_duplicate_source(hass, source):
    await setup_copy(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={"source_entity_id": SOURCE, "name": "Another copy"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_copy_display_check_uncheck_and_reload_without_source(hass, source):
    entry = await setup_copy(hass)
    assert hass.states.get("todo.einkaufszettel").state == "2"
    items = await read_items(hass)
    assert [item["summary"] for item in items] == ["Milch", "Brot"]
    assert items[1]["description"] == "Vom Baecker"
    assert items[0]["uid"] != "source-1"
    uid = items[0]["uid"]
    for status, count in [
        ("completed", "1"),
        ("needs_action", "2"),
        ("completed", "1"),
    ]:
        await hass.services.async_call(
            "todo",
            "update_item",
            {"entity_id": "todo.einkaufszettel", "item": uid, "status": status},
            blocking=True,
        )
        assert hass.states.get("todo.einkaufszettel").state == count
    assert source.todo_items[0].status == TodoItemStatus.NEEDS_ACTION
    await hass.config_entries.async_unload(entry.entry_id)
    hass.states.async_set(SOURCE, "unavailable")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("todo.einkaufszettel").state == "1"
    assert (await read_items(hass))[0]["uid"] == uid
    assert (await read_items(hass))[0]["status"] == "completed"


async def test_failed_save_does_not_publish_or_mutate(hass, source):
    entry = await setup_copy(hass)
    uid = entry.runtime_data.items[0].uid
    with patch.object(
        entry.runtime_data.store, "async_save", side_effect=OSError("disk full")
    ):
        with pytest.raises(HomeAssistantError, match="Cannot save"):
            await hass.services.async_call(
                "todo",
                "update_item",
                {
                    "entity_id": "todo.einkaufszettel",
                    "item": uid,
                    "status": "completed",
                },
                blocking=True,
            )
    assert entry.runtime_data.items[0].status == "needs_action"
    assert hass.states.get("todo.einkaufszettel").state == "2"


async def test_concurrent_checks_on_different_items(hass, source):
    entry = await setup_copy(hass)
    await asyncio.gather(
        *(
            hass.services.async_call(
                "todo",
                "update_item",
                {
                    "entity_id": "todo.einkaufszettel",
                    "item": item.uid,
                    "status": "completed",
                },
                blocking=True,
            )
            for item in entry.runtime_data.items
        )
    )
    assert hass.states.get("todo.einkaufszettel").state == "0"
    assert all(item.status == "completed" for item in entry.runtime_data.items)


async def test_empty_copy_is_not_reimported(hass, source):
    source._attr_todo_items = []
    source.async_write_ha_state()
    entry = await setup_copy(hass)
    assert await read_items(hass) == []
    await hass.config_entries.async_unload(entry.entry_id)
    source._attr_todo_items = [
        TodoItem(uid="new", summary="Neue Milch", status=TodoItemStatus.NEEDS_ACTION)
    ]
    source.async_write_ha_state()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert await read_items(hass) == []


async def test_corrupt_storage_does_not_overwrite_or_reimport(hass, source):
    entry = await setup_copy(hass)
    await hass.config_entries.async_unload(entry.entry_id)
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


async def test_button_appends_and_refreshes_todo_state(hass, source):
    entry = await setup_copy(hass)
    original_uid = entry.runtime_data.items[0].uid
    await hass.services.async_call(
        "todo",
        "update_item",
        {
            "entity_id": "todo.einkaufszettel",
            "item": original_uid,
            "status": "completed",
        },
        blocking=True,
    )
    source._attr_todo_items = [
        *source.todo_items,
        TodoItem(
            uid="new-source", summary="Butter", status=TodoItemStatus.NEEDS_ACTION
        ),
    ]
    source.async_write_ha_state()
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    button_id = registry.async_get_entity_id(
        "button", DOMAIN, f"{entry.entry_id}_copy_source"
    )
    assert button_id is not None
    for _ in range(2):
        await hass.services.async_call(
            "button", "press", {"entity_id": button_id}, blocking=True
        )
        await hass.async_block_till_done()
        assert hass.states.get("todo.einkaufszettel").state == "2"
        assert len(await read_items(hass)) == 3
    assert entry.runtime_data.items[0].uid == original_uid
    assert entry.runtime_data.items[0].status == "completed"
