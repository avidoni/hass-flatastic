"""Init file for Flatastic To-do"""
from homeassistant.core import HomeAssistant

DOMAIN = "flatastic"

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass, entry):
    return True