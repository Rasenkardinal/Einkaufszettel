"""Expose the local shopping list in Home Assistant's To-do UI."""

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EinkaufszettelConfigEntry, EinkaufszettelData
from .const import update_signal
from .model import parse_due, update_item


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EinkaufszettelConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the independent To-do list."""
    async_add_entities(
        [EinkaufszettelTodo(entry.runtime_data, entry.entry_id, entry.data[CONF_NAME])]
    )


class EinkaufszettelTodo(TodoListEntity):
    """A locally persisted list, with check/uncheck and editing support."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_icon = "mdi:cart-outline"
    _attr_supported_features = (
        TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DUE_DATETIME_ON_ITEM
    )

    def __init__(self, data: EinkaufszettelData, unique_id: str, name: str) -> None:
        self._data = data
        self._attr_unique_id = unique_id
        self._update_signal = update_signal(unique_id)
        self._attr_name = name

    async def async_added_to_hass(self) -> None:
        """Refresh To-do subscriptions after a manual source copy."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._update_signal, self.async_write_ha_state
            )
        )

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return copies so HA cannot mutate the persisted snapshot."""
        return [
            TodoItem(
                uid=item.uid,
                summary=item.summary,
                status=TodoItemStatus(item.status),
                description=item.description,
                due=parse_due(item.due),
            )
            for item in self._data.items
        ]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Persist before publishing success; serialize concurrent edits."""
        if item.uid is None or item.summary is None or item.status is None:
            raise HomeAssistantError("The updated item needs UID, text and status")
        async with self._data.lock:
            try:
                updated = update_item(
                    self._data.items,
                    item.uid,
                    item.summary,
                    TodoItemStatus(item.status).value,
                    item.description,
                    item.due.isoformat() if item.due is not None else None,
                )
                await self._data.store.async_save(
                    {"items": [value.to_dict() for value in updated]}
                )
            except (ValueError, OSError, HomeAssistantError) as err:
                raise HomeAssistantError(f"Cannot save shopping item: {err}") from err
            self._data.items = updated
            self.async_write_ha_state()
