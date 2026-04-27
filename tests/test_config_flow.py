"""Tests for the config flow."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.blaze504d.blaze_client import BlazeConnectionError
from custom_components.blaze504d.const import DOMAIN

DEVICE_INFO = {
    "model_name": "PowerZone 504D",
    "zone_count": 4,
    "serial": "SN123",
    "firmware": "1.0.0",
}


async def test_config_flow_happy_path(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.blaze504d.config_flow.BlazeClient.get_device_info",
        new_callable=AsyncMock,
        return_value=DEVICE_INFO,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "192.168.1.100", "name": "Living Room Amp"},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room Amp"
    assert result["data"]["host"] == "192.168.1.100"
    assert result["data"]["name"] == "Living Room Amp"


async def test_config_flow_cannot_connect(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "custom_components.blaze504d.config_flow.BlazeClient.get_device_info",
        new_callable=AsyncMock,
        side_effect=BlazeConnectionError("connection refused"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "192.168.1.100"},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_config_flow_duplicate_host(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "custom_components.blaze504d.config_flow.BlazeClient.get_device_info",
        new_callable=AsyncMock,
        return_value=DEVICE_INFO,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "192.168.1.100"},
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
