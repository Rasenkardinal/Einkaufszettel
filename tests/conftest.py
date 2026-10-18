"""Load the HA test plugin only in environments where it is installed."""

from importlib.util import find_spec

pytest_plugins = (
    ["pytest_homeassistant_custom_component"]
    if find_spec("pytest_homeassistant_custom_component") is not None
    else []
)
