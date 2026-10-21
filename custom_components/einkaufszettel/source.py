"""Read the selected list through Home Assistant's public To-do service."""

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .model import ShoppingItem, import_items


async def async_read_source(hass: HomeAssistant, entity_id: str) -> list[ShoppingItem]:
    """Read a valid external To-do source; never write to it."""
    state = hass.states.get(entity_id)
    registered = er.async_get(hass).async_get(entity_id)
    if (
        not entity_id.startswith("todo.")
        or state is None
        or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)
        or (registered is not None and registered.platform == DOMAIN)
    ):
        raise HomeAssistantError("Select an available external To-do list")

    response = await hass.services.async_call(
        "todo",
        "get_items",
        {"entity_id": entity_id, "status": ["needs_action"]},
        blocking=True,
        return_response=True,
    )
    if not isinstance(response, dict) or not isinstance(
        result := response.get(entity_id), dict
    ):
        raise HomeAssistantError("The source returned no To-do response")
    try:
        return import_items(result.get("items"))
    except ValueError as err:
        raise HomeAssistantError(f"Invalid source list: {err}") from err


async def async_read_all_source(
    hass: HomeAssistant, entity_id: str
) -> list[ShoppingItem]:
    """Read open and completed items with stable source IDs for reconciliation."""
    state = hass.states.get(entity_id)
    registered = er.async_get(hass).async_get(entity_id)
    if (
        not entity_id.startswith("todo.")
        or state is None
        or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)
        or (registered is not None and registered.platform == DOMAIN)
    ):
        raise HomeAssistantError("Die Quellliste ist nicht verfügbar.")
    response = await hass.services.async_call(
        "todo",
        "get_items",
        {"entity_id": entity_id},
        blocking=True,
        return_response=True,
    )
    if (
        not isinstance(response, dict)
        or not isinstance(response.get(entity_id), dict)
        or not isinstance(response[entity_id].get("items"), list)
    ):
        raise HomeAssistantError("Die Quellliste hat keine gültige Antwort geliefert.")
    items = []
    seen = set()
    for raw in response[entity_id]["items"]:
        if not isinstance(raw, dict):
            raise ValueError("Invalid source item")
        uid = raw.get("uid")
        if not isinstance(uid, str) or not uid or uid in seen:
            raise ValueError("Die Quellliste benötigt eindeutige Artikel-IDs.")
        seen.add(uid)
        items.append(
            ShoppingItem(
                uid=uid,
                source_uid=uid,
                summary=raw.get("summary"),
                status=raw.get("status"),
                description=raw.get("description"),
                due=raw.get("due"),
            )
        )
    return items
