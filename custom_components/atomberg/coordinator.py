"""Data update coordinator for the Atomberg integration."""

from datetime import timedelta
from logging import getLogger

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import AtombergCloudAPI
from .const import MANUFACTURER
from .device import AtombergDevice
from .udp_listener import UDPListener

_LOGGER = getLogger(__name__)

POLL_INTERVAL = timedelta(minutes=1)


class AtombergDataUpdateCoordinator(DataUpdateCoordinator):
    """Atomberg data update coordinator."""

    def __init__(
        self, hass: HomeAssistant, api: AtombergCloudAPI, udp_listener: UDPListener
    ) -> None:
        """Init data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{MANUFACTURER} Coordinator",
            update_interval=POLL_INTERVAL,
        )

        self.api = api
        self.udp_listener = udp_listener
        self.devices = [
            AtombergDevice(data=data, api=self.api, config_entry=self.config_entry)
            for data in self.api.device_list.values()
        ]

        # Add callback on udp listener
        self.udp_listener.add_callback(self.config_entry, self._handle_udp_update)

    def _handle_udp_update(self, data: dict) -> None:
        """Forward UDP updates to listeners."""
        self.async_set_updated_data(data)

    async def _async_update_data(self) -> dict[str, str]:
        """Poll cloud state for devices without local push updates."""
        try:
            await self.api.async_refresh_devices()
        except Exception as err:
            raise UpdateFailed("Failed to refresh Atomberg devices") from err

        return {"source": "poll"}
