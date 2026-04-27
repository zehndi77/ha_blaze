"""Tests for BlazeCoordinator."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.blaze504d.blaze_client import BlazeConnectionError
from custom_components.blaze504d.coordinator import BlazeCoordinator

ZONES = ["A", "B", "C", "D"]


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.get_gain = AsyncMock(return_value=-10.0)
    client.get_mute = AsyncMock(return_value=False)
    client.get_system_state = AsyncMock(return_value="ON")
    return client


async def test_coordinator_data_shape(hass: HomeAssistant, mock_client) -> None:
    coordinator = BlazeCoordinator(hass, mock_client, zones=ZONES)
    await coordinator.async_refresh()

    assert coordinator.data is not None
    for zone in ZONES:
        assert zone in coordinator.data
        assert "gain" in coordinator.data[zone]
        assert "muted" in coordinator.data[zone]
        assert isinstance(coordinator.data[zone]["gain"], float)
        assert isinstance(coordinator.data[zone]["muted"], bool)


async def test_coordinator_handles_connection_error_gracefully(
    hass: HomeAssistant, mock_client
) -> None:
    mock_client.get_gain = AsyncMock(side_effect=BlazeConnectionError("boom"))
    coordinator = BlazeCoordinator(hass, mock_client, zones=ZONES)
    data = await coordinator._async_update_data()
    for zone in ZONES:
        assert data[zone]["gain"] == 0.0
