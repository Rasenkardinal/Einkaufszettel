"""Set up the app and import sources selected in its list management."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_SOURCE, DOMAIN
from .source import async_read_source

_LOGGER = logging.getLogger(__name__)


class EinkaufszettelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up one app hub and internal source-bound entries."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return EinkaufszettelOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Open one app hub; sources are selected inside the app."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        if user_input is not None:
            return self.async_create_entry(
                title="Einkaufszettel", data={CONF_NAME: "Einkaufszettel"}
            )
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate an app-selected source before creating its internal entry."""
        if user_input is None:
            return self.async_abort(reason="cannot_read_source")
        source = user_input[CONF_SOURCE]
        name = user_input[CONF_NAME].strip()
        if not name:
            return self.async_abort(reason="empty_name")
        await self.async_set_unique_id(source)
        self._abort_if_unique_id_configured()
        try:
            await async_read_source(self.hass, source)
        except (HomeAssistantError, TimeoutError) as err:
            _LOGGER.warning("Cannot read selected To-do source %s: %s", source, err)
            return self.async_abort(reason="cannot_read_source")
        return self.async_create_entry(
            title=name,
            data={CONF_NAME: name, CONF_SOURCE: source},
            options={"enabled": user_input.get("enabled", True)},
        )


class EinkaufszettelOptionsFlow(OptionsFlow):
    """Open the authenticated file UI from the integration's Configure action."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_abort(reason="backup_link")
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={"backup_url": "/einkaufszettel_backup"},
        )
