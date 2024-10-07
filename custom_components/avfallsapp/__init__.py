"""Main package for coordinator."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

import async_timeout
import requests

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

# from homeassistant.helpers.event import async_track_state_change_event
# from homeassistant.util import dt as dt_util
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# PLATFORMS = []
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

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=config_entry.data.get(CONF_NAME),
            # update_interval=timedelta(hours=1),
            update_interval=timedelta(seconds=20),
            update_method=self._async_update_data,
            # update_method=self._update_data,
            always_update=True,
        )
        self._hass = hass
        self_bins = []

    # @property
    # def name(self) -> str:
    #     """Name of instance."""
    #     return self._config.data["name"]

    def get_device_info(self) -> DeviceInfo:
        """Get device info to group entities."""
        return DeviceInfo(
            # identifiers={(DOMAIN, self._config.data[CONF_TYPE])},
            name=self.name,
            manufacturer="Avfallsapp.se",
            entry_type=DeviceEntryType.SERVICE,
        )

    def get_next_pickup(self):
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
        # https://community.home-assistant.io/t/garbage-sensor-from-api-json-help/155379/4
        # https://soderkoping.avfallsapp.se/wp-json/nova/v1/
        # https://soderkoping.avfallsapp.se/wp-json/nova/v1/recycle-stations?
        # https://soderkoping.avfallsapp.se/wp-json/nova/v1/next-pickup/list?
        # https://developers.home-assistant.io/docs/api/rest/

        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                response = await self._hass.async_add_executor_job(self.get_next_pickup)
                response.raise_for_status()
                data = response.json()
                _LOGGER.debug(response.text)
                _LOGGER.debug(data)
                # TODO: Store data for entities to read
                entries = []
                for entry in data:
                    address = entry.get("address")
                    # plant_id = entry.get("plant_id")
                    for bin in entry.get("bins"):
                        # icon = ICON_RECYCLE
                        waste_type = bin.get("type")
                        waste_type_full = f"{address} {waste_type}"
                        pickup_date = bin.get("pickup_date")
                        pickup_date = datetime.strptime(pickup_date, "%Y-%m-%d").date()
                        if waste_type and pickup_date:
                            _LOGGER.debug(
                                "Adding entry for %s with next pickup %s",
                                waste_type_full,
                                pickup_date.strftime("%Y-%m-%d"),
                            )
                            # entries.append(
                            #     Collection(
                            #         date=pickup_date, t=waste_type_full, icon=icon
                            #     )
                            # )

        except Exception as err:
            pass
            # raise UpdateFailed(f"Unknown error communicating with API: {err}") from err


# class AvfallsappEntity(Entity):
#     """Base class for Avfallsapp entities."""

#     def __init__(
#         self,
#         coordinator: AvfallsappCoordinator,
#     ) -> None:
#         """Initialize entity."""
#         # Input configs
#         self._coordinator = coordinator
#         self._attr_device_info = coordinator.get_device_info()
