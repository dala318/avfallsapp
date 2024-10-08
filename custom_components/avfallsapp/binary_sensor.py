"""Sensor integration for Avfallsapp."""

from __future__ import annotations

import datetime
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    # BinarySensorStateClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, AvfallsappCoordinator, RecycleStation

_LOGGER = logging.getLogger(__name__)

ICON_RECYCLE = "mdi:recycle"


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Binary Sensor setup for the platform."""
    api_coordinator: AvfallsappCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    for r in api_coordinator.rss.values():
        _LOGGER.debug(
            "Creating Recycle Station binary sensor for %s", r.get_full_name()
        )
        entities.append(OpenSensor(api_coordinator, r))
    if entities:
        async_add_entities(entities)
        return True
    return False


class OpenSensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for pickup opening binary sensor."""

    def __init__(
        self,
        coordinator: AvfallsappCoordinator,
        rs: RecycleStation,
    ) -> None:
        """Initialize my sensor."""
        super().__init__(coordinator, rs.get_full_name())
        self._rs = rs
        self._attr_name = rs.get_full_name()
        self._attr_unique_id = rs.get_rs_id()
        self._attr_icon = ICON_RECYCLE
        self._attr_device_class = BinarySensorDeviceClass.OPENING
        # self._attr_native_unit_of_measurement = UnitOfTime.DAYS
        # self._attr_device_info = DeviceInfo(
        #     identifiers={(DOMAIN, rs.get_address_id())},
        #     name=rs.get_full_address(),
        #     manufacturer="Avfallsapp",
        # )
        # self._attr_state_class = BinarySensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for i, rs in self.coordinator.rss.items():
            if i == self._rs.get_rs_id():
                self._attr_is_on = (
                    rs.get_opens_at() < datetime.datetime.now().time()
                    and rs.get_closes_at() > datetime.datetime.now().time()
                )
                self._attr_extra_state_attributes = rs.get_state_attr()
                break
        self.async_write_ha_state()
