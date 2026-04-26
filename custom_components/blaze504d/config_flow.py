"""Config flow for Blaze Pascal series amplifiers."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .blaze_client import BlazeClient, BlazeConnectionError, BlazeProtocolError
from .const import DOMAIN, CONF_HOST, CONF_NAME, CONF_ZONE_COUNT, CONF_MODEL_NAME, CONF_SERIAL, CONF_FIRMWARE

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default=""): str,
    }
)


class BlazeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blaze Pascal series amplifiers."""

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
                info = await client.get_device_info()
            except (BlazeConnectionError, BlazeProtocolError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                friendly_name = user_input.get(CONF_NAME, "").strip() or info["model_name"] or host
                return self.async_create_entry(
                    title=friendly_name,
                    data={
                        CONF_HOST: host,
                        CONF_NAME: friendly_name,
                        CONF_ZONE_COUNT: info["zone_count"],
                        CONF_MODEL_NAME: info["model_name"],
                        CONF_SERIAL: info["serial"],
                        CONF_FIRMWARE: info["firmware"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
