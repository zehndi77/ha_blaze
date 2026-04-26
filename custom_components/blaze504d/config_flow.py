"""Config flow for Blaze 504D integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .blaze_client import BlazeClient, BlazeConnectionError
from .const import DOMAIN, CONF_HOST, CONF_NAME

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default="Blaze 504D"): str,
    }
)


class BlazeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blaze 504D."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()

            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = BlazeClient(session, host)

            try:
                if not await client.validate_connection():
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME, host),
                        data={CONF_HOST: host, CONF_NAME: user_input.get(CONF_NAME, host)},
                    )
            except BlazeConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
