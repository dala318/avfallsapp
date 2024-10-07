"""Main package for coordinator."""

from __future__ import annotations

import asyncio.timeouts
from datetime import datetime, timedelta
import logging

import requests

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    config_entry.async_on_unload(config_entry.add_update_listener(async_reload_entry))

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if config_entry.entry_id not in hass.data[DOMAIN]:
        coordinator = AvfallsappCoordinator(hass, config_entry)
        hass.data[DOMAIN][config_entry.entry_id] = coordinator

    # if config_entry is not None:
    #     if config_entry.source == SOURCE_IMPORT:
    #         hass.async_create_task(
    #             hass.config_entries.async_remove(config_entry.entry_id)
    #         )
    #         return False

    await hass.data[DOMAIN][config_entry.entry_id].async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading a config_flow entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)


class AvfallsappCoordinator(DataUpdateCoordinator):
    """API base class."""

    _bins = {}

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=config_entry.data.get(CONF_NAME),
            update_interval=timedelta(seconds=20),
            update_method=self._async_update_data,
            always_update=True,
        )
        self._hass = hass

    # @property
    # def name(self) -> str:
    #     """Name of instance."""
    #     return self._config.data["name"]

    @property
    def bins(self) -> dict[str, Bin]:
        """Name of instance."""
        return self._bins

    def get_device_info(self) -> DeviceInfo:
        """Get device info to group entities."""
        return DeviceInfo(
            # identifiers={(DOMAIN, self._config.data[CONF_TYPE])},
            name=self.name,
            manufacturer="Avfallsapp.se",
            entry_type=DeviceEntryType.SERVICE,
        )

    def get_next_pickup_dict(self):
        """Get next pickup date."""
        url = (
            self.config_entry.data.get(CONF_URL) + "/wp-json/nova/v1/next-pickup/list?"
        )
        if "http" not in url:
            url = "https://" + url
        headers = {
            "X-App-Identifier": self.config_entry.data.get(CONF_API_KEY),
        }
        return requests.get(url, headers=headers, timeout=10)

    async def _async_update_data(self):
        """Update call function."""
        _LOGGER.debug("Updating service")
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeouts.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                response = await self._hass.async_add_executor_job(
                    self.get_next_pickup_dict
                )
                response.raise_for_status()
                data = response.json()
                # _LOGGER.debug(response.text)
                _LOGGER.debug(data)
                for entry in data:
                    for b in entry.get("bins"):
                        bin = Bin(b)
                        if bin.is_valid():
                            if bin.get_bin_id() not in self._bins:
                                _LOGGER.debug(
                                    "Adding Bin entry for %s with next pickup %s",
                                    bin.get_full_name(),
                                    bin.get_next_pickup().strftime("%Y-%m-%d"),
                                )
                                self._bins[bin.get_bin_id()] = bin
                            else:
                                self._bins[bin.get_bin_id()].update_state(b)
                                _LOGGER.debug(
                                    "Updating existing Bin entry %s with next pickup %s",
                                    self._bins[bin.get_bin_id()].get_full_name(),
                                    self._bins[bin.get_bin_id()].get_next_pickup(),
                                )
        except Exception as err:
            pass
            # TODO: Initiate proper exeption
            # raise UpdateFailed(f"Unknown error communicating with API: {err}") from err


class Bin:
    """Bin specific class."""

    def __init__(self, bin_dict: dict) -> None:
        """Initialize my coordinator."""
        self._bin_dict = bin_dict
        self._customer_id = bin_dict.get("customer_id")
        self._plant_number = bin_dict.get("plant_number")
        self._id = bin_dict.get("id")

    def update_state(self, bin_dict: dict) -> None:
        """Set next pickup date of bin."""
        self._bin_dict = bin_dict

    def is_valid(self) -> bool:
        """ "Validate the necessary"""
        for key in [
            "customer_id",
            "plant_number",
            "address",
            "id",
            "type",
            "pickup_date",
        ]:
            if key not in self._bin_dict:
                _LOGGER.error("Failed to validate Bin with data %s", self._bin_dict)
                return False
        return True

    def get_full_address(self) -> str:
        """Bin address."""
        return self._bin_dict.get("address") + ", " + self._bin_dict.get("zip_city")

    def get_bin_id(self) -> str:
        """Get unique identifier for bin."""
        return self._customer_id + "_" + self._id

    def get_address_id(self) -> str:
        """Get unique identifier for address."""
        return self._customer_id + "_" + self._plant_number

    def get_full_name(self) -> str:
        """Get full name of bin."""
        return self._bin_dict.get("address") + " - " + self._bin_dict.get("type")

    def get_next_pickup(self) -> datetime.date:
        """Get next pickup date of bin."""
        return datetime.strptime(self._bin_dict.get("pickup_date"), "%Y-%m-%d").date()

    def get_state_attr(self) -> dict:
        """Get extra state attributes of bin."""
        return {
            "Address": self._bin_dict.get("address"),
            "City": self._bin_dict.get("zip_city"),
            "Deviating": self._bin_dict.get("deviating"),
            "Pickup date": self.get_next_pickup(),
        }
