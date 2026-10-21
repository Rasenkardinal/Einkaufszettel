"""Select the source list for the initial copy."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import CONF_SOURCE, DOMAIN
from .source import async_read_source

_LOGGER = logging.getLogger(__name__)


class EinkaufszettelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure one local shopping list per source."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            source = user_input[CONF_SOURCE]
            name = user_input[CONF_NAME].strip()
            await self.async_set_unique_id(source)
            self._abort_if_unique_id_configured()
            if not name:
                errors[CONF_NAME] = "empty_name"
            else:
                try:
                    await async_read_source(self.hass, source)
                except (HomeAssistantError, TimeoutError) as err:
                    _LOGGER.warning(
                        "Cannot read selected To-do source %s: %s", source, err
                    )
                    errors["base"] = "cannot_read_source"
                else:
                    return self.async_create_entry(
                        title=name, data={CONF_NAME: name, CONF_SOURCE: source}
                    )

        excluded = [
            entity.entity_id
            for entity in er.async_get(self.hass).entities.values()
            if entity.platform == DOMAIN
        ]
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SOURCE,
                        **({"default": user_input[CONF_SOURCE]} if user_input else {}),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="todo", exclude_entities=excluded
                        )
                    ),
                    vol.Required(
                        CONF_NAME,
                        default=user_input[CONF_NAME]
                        if user_input
                        else "Einkaufszettel",
                    ): selector.TextSelector(),
                }
            ),
            errors=errors,
        )
