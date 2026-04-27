"""Tests for BlazeZoneGain number entity."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.blaze504d.const import DOMAIN
from tests.conftest import ZONE_DATA_ALL_UNMUTED


def _full_mock_client(**extra) -> MagicMock:
    mc = MagicMock()
    mc.get_gain = AsyncMock(return_value=-10.0)
    mc.get_mute = AsyncMock(return_value=False)
    mc.get_system_state = AsyncMock(return_value="ON")
    mc.start_dyn_subscription = AsyncMock()
    mc.get_input_count = AsyncMock(return_value=4)
    mc.get_output_count = AsyncMock(return_value=4)
    mc.get_dyn_snapshot = MagicMock(return_value={})
    mc.close = AsyncMock()
    for attr, val in extra.items():
        setattr(mc, attr, val)
    return mc


async def test_zone_gain_state(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)

    with (
        patch("custom_components.blaze504d.BlazeClient") as mock_cls,
        patch(
            "custom_components.blaze504d.coordinator.BlazeCoordinator._async_update_data",
            new_callable=AsyncMock,
            return_value=ZONE_DATA_ALL_UNMUTED,
        ),
    ):
        mc = mock_cls.return_value
        mc.start_dyn_subscription = AsyncMock()
        mc.get_input_count = AsyncMock(return_value=4)
        mc.get_output_count = AsyncMock(return_value=4)
        mc.get_dyn_snapshot = MagicMock(return_value={})
        mc.close = AsyncMock()
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("number.zone_a_gain")
    assert state is not None
    assert float(state.state) == -10.0


async def test_zone_gain_set_value(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    mock_client = _full_mock_client(set_gain=AsyncMock(return_value=-20.0))

    with patch(
        "custom_components.blaze504d.BlazeClient",
        return_value=mock_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.zone_a_gain", "value": -20.0},
            blocking=True,
        )

    mock_client.set_gain.assert_awaited_once_with("A", -20.0)
