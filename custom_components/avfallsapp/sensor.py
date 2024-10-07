"""Sensor integration for Avfallsapp."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
        _LOGGER.debug("Creating Bin sensor for %s", b.get_identity())
        entities.append(MeasurementSensor(api_coordinator, b))
    if entities:
        async_add_entities(entities)
        return True
    return False


class MeasurementSensor(CoordinatorEntity, SensorEntity):
    """Base class for avfallsapp sensor."""

    def __init__(
        self,
        coordinator: AvfallsappCoordinator,
        bin: Bin,
    ) -> None:
        super().__init__(coordinator, bin.get_identity())
        self._bin = bin

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for i, b in self.coordinator.bins.items():
            if i == self._bin.get_identity():
                self._attr_native_value = b.get_next_pickup()
                break
        self.async_write_ha_state()

    # @property
    # def _attr_unique_id(self) -> str:
    #     return "%s_account%s_%s" % (
    #         self.coordinator.data.id,
    #         # self._account.id,
    #         # self._latest_measurement.parameter.replace(" ", "_")
    #         "".replace("-", "_").lower(),
    #     )

    # @property
    # def _attr_name(self) -> str:
    #     return "%s %s" % (self._account.full_name, self._latest_measurement.parameter)

    # @property
    # def _attr_device_info(self) -> DeviceInfo:
    #     """Return a inique set of attributes for each vehicle."""
    #     return DeviceInfo(
    #         identifiers={(DOMAIN, self._account.id)},
    #         name=self._account.full_name,
    #         model="%sm3" % self._account.volume,
    #         manufacturer="Avfallsapp",
    #     )

    # @property
    # def _attr_native_value(self):
    #     return self._latest_measurement.value

    # @property
    # def _attr_native_unit_of_measurement(self) -> str:
    #     return self._latest_measurement.unit.split(" ")[0]

    # @property
    # def _attr_state_class(self) -> SensorStateClass:
    #     return SensorStateClass.MEASUREMENT

    # @property
    # def _attr_icon(self) -> str:
    #     return "mdi:water-percent"

    # @property
    # def _attr_extra_state_attributes(self):
    #     """Provide attributes for the entity"""
    #     return {
    #         "measured_at": self._latest_measurement.timestamp,
    #         "measure": self._latest_measurement.id,
    #         "ideal_low": self._latest_measurement.ideal_low,
    #         "ideal_high": self._latest_measurement.ideal_high,
    #         "device_serial": self._latest_measurement.device_serial,
    #         "operator_name": self._latest_measurement.operator_name,
    #         "comment": self._latest_measurement.comment,
    #     }
