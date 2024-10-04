"""Config flow for Avfallsapp integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_API_KEY, CONF_URL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AvfallsappConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Avfallsapp config flow."""

    VERSION = 0
    MINOR_VERSION = 1
    data = None
    options = None
    _reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.data = user_input

            self.options = {}
            await self.async_set_unique_id(
                self.data[CONF_NAME] + "_"
                # + self.data[CONF_TYPE]
            )
            self._abort_if_unique_id_configured()

            _LOGGER.debug(
                'Creating entry "%s" with data "%s" and oprions %s',
                self.unique_id,
                self.data,
                self.options,
            )
            return self.async_create_entry(
                title=self.data[CONF_NAME], data=self.data, options=self.options
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,  # cv.string,
                vol.Required(CONF_URL): str,  # cv.url,
                vol.Required(CONF_API_KEY): str,  # cv.string,
            }
        )

        placeholders = {
            #     CONF_TYPE: CONF_TYPE_LIST,
            #     CONF_NP_ENTITY: selected_entities,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders=placeholders,
            errors=errors,
        )

    # async def async_step_import(
    #     self, user_input: Optional[Dict[str, Any]] | None = None
    # ) -> FlowResult:
    #     """Import avfallsapp config from configuration.yaml."""
    #     return await self.async_step_user(import_data)
