"""Support for Envisalink zone bypass switches."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .config_flow import find_yaml_zone_info
from .models import EnvisalinkDevice
from .const import (
    CONF_CREATE_ZONE_BYPASS_SWITCHES,
    CONF_NUM_ZONES,
    CONF_ZONENAME,
    CONF_ZONES,
    DEFAULT_NUM_ZONES,
    DOMAIN,
    LOGGER,
    STATE_UPDATE_TYPE_ZONE_BYPASS,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    controller = hass.data[DOMAIN][entry.entry_id]

    create_bypass_switches = entry.options.get(CONF_CREATE_ZONE_BYPASS_SWITCHES)
    if create_bypass_switches:
        zone_info = entry.data.get(CONF_ZONES)
        entities = []
        for zone_num in range(1, entry.options.get(CONF_NUM_ZONES, DEFAULT_NUM_ZONES) + 1):
            zone_entry = find_yaml_zone_info(zone_num, zone_info)

            entity = EnvisalinkSwitch(
                hass,
                zone_num,
                zone_entry,
                controller,
            )
            entities.append(entity)

        async_add_entities(entities)


class EnvisalinkSwitch(EnvisalinkDevice, SwitchEntity):
    """Representation of an Envisalink switch."""

    def __init__(self, hass, zone_number, zone_info, controller):
        """Initialize the switch."""
        self._zone_number = zone_number
        name_suffix = f"zone_{self._zone_number}_bypass"
        self._attr_unique_id = f"{controller.unique_id}_{name_suffix}"

        name = f"{controller.alarm_name}_{name_suffix}"
        if zone_info:
            # Override the name if there is info from the YAML configuration
            if CONF_ZONENAME in zone_info:
                name = f"{zone_info[CONF_ZONENAME]}_bypass"

        LOGGER.debug("Setting up zone: %s", name)
        super().__init__(name, controller, STATE_UPDATE_TYPE_ZONE_BYPASS, zone_number)

    @property
    def _info(self):
        return self._controller.controller.alarm_state["zone"][self._zone_number]

    @property
    def is_on(self):
        """Return the boolean response if the zone is bypassed."""
        return self._info["bypassed"]

    async def async_turn_on(self, **kwargs):
        """Send the bypass keypress sequence to toggle the zone bypass."""
        await self._controller.controller.toggle_zone_bypass(self._zone_number)

    async def async_turn_off(self, **kwargs):
        """Send the bypass keypress sequence to toggle the zone bypass."""
        await self._controller.controller.toggle_zone_bypass(self._zone_number)

