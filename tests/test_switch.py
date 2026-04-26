"""Tests for BlazeZoneMute and BlazeAllMute switch entities."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from tests.conftest import ZONE_DATA_ALL_MUTED, ZONE_DATA_ALL_UNMUTED


async def test_zone_mute_state_off(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.blaze504d.coordinator.BlazeCoordinator._async_update_data",
        new_callable=AsyncMock,
        return_value=ZONE_DATA_ALL_UNMUTED,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("switch.zone_a_mute")
    assert state is not None
    assert state.state == "off"


async def test_all_mute_on_when_all_zones_muted(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.blaze504d.coordinator.BlazeCoordinator._async_update_data",
        new_callable=AsyncMock,
        return_value=ZONE_DATA_ALL_MUTED,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("switch.all_zones_mute")
    assert state is not None
    assert state.state == "on"


async def test_all_mute_off_when_any_zone_unmuted(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    partial = {**ZONE_DATA_ALL_MUTED, "D": {"gain": -25.0, "muted": False}}

    with patch(
        "custom_components.blaze504d.coordinator.BlazeCoordinator._async_update_data",
        new_callable=AsyncMock,
        return_value=partial,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("switch.all_zones_mute")
    assert state.state == "off"


async def test_zone_mute_turn_on(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    mock_client = MagicMock()
    mock_client.set_mute = AsyncMock()
    mock_client.get_gain = AsyncMock(return_value=-10.0)
    mock_client.get_mute = AsyncMock(return_value=False)

    with patch("custom_components.blaze504d.BlazeClient", return_value=mock_client):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        await hass.services.async_call(
            "switch", "turn_on",
            {"entity_id": "switch.zone_b_mute"},
            blocking=True,
        )

    mock_client.set_mute.assert_awaited_once_with("B", True)
