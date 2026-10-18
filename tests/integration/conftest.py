"""Real Home Assistant integration tests (Linux test environment)."""

import pytest


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Allow the real HA loader to discover this custom integration."""
