"""Sensor integration for Avfallsapp."""

from __future__ import annotations

import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, AvfallsappCoordinator, Bin

_LOGGER = logging.getLogger(__name__)

ICON_RECYCLE = "mdi:recycle"


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Sensor setup for the platform."""
    api_coordinator: AvfallsappCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    for b in api_coordinator.bins.values():
        _LOGGER.debug("Creating Bin sensor for %s", b.get_full_name())
        entities.append(PickupSensor(api_coordinator, b))
    if entities:
        async_add_entities(entities)
        return True
    return False


class PickupSensor(CoordinatorEntity, SensorEntity):
    """Base class for pickup date sensor."""

    def __init__(
        self,
        coordinator: AvfallsappCoordinator,
        bin: Bin,
    ) -> None:
        """Initialize my sensor."""
        super().__init__(coordinator, bin.get_full_name())
        self._bin = bin
        self._attr_name = bin.get_full_name()
        self._attr_unique_id = bin.get_bin_id()
        self._attr_icon = ICON_RECYCLE
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = UnitOfTime.DAYS
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, bin.get_address_id())},
            name=bin.get_full_address(),
            manufacturer="Avfallsapp",
        )
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for i, b in self.coordinator.bins.items():
            if i == self._bin.get_bin_id():
                self._attr_native_value = (
                    b.get_next_pickup() - datetime.datetime.now().date()
                ).days
                self._attr_extra_state_attributes = b.get_state_attr()
                break
        self.async_write_ha_state()
