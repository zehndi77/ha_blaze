"""pytest configuration and shared fixtures."""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.blaze504d.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.100", "name": "Test Amp"},
        unique_id="192.168.1.100",
    )


ZONE_DATA_ALL_UNMUTED = {
    "A": {"gain": -10.0, "muted": False},
    "B": {"gain": -15.0, "muted": False},
    "C": {"gain": -20.0, "muted": False},
    "D": {"gain": -25.0, "muted": False},
}

ZONE_DATA_ALL_MUTED = {
    zone: {"gain": v["gain"], "muted": True}
    for zone, v in ZONE_DATA_ALL_UNMUTED.items()
}
