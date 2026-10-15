"""Data update coordinator for the Atomberg integration."""

from datetime import timedelta
from logging import getLogger

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import AtombergCloudAPI
from .const import (
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL_MINUTES,
    MANUFACTURER,
    MAX_POLL_INTERVAL_MINUTES,
    MIN_POLL_INTERVAL_MINUTES,
)
from .device import (
    ATTR_BRIGHTNESS,
    ATTR_IS_ONLINE,
    ATTR_LED,
    ATTR_LIGHT_MODE,
    ATTR_POWER,
    ATTR_SLEEP,
    ATTR_SPEED,
    ATTR_TIMER_HOURS,
    ATTR_TIMER_TIME_ELAPSED_MINS,
    DEVICE_TYPE_FAN,
    AtombergDevice,
)
from .udp_listener import UDPListener

_LOGGER = getLogger(__name__)

# Fan state fields that are kept in sync via UDP broadcasts. Cloud polling
# must not overwrite them, otherwise a fan would flicker to "unavailable"
# or revert to a stale speed/power value every poll interval.
FAN_PUSH_DRIVEN_ATTRS = {
    ATTR_IS_ONLINE,
    ATTR_POWER,
    ATTR_SPEED,
    ATTR_SLEEP,
    ATTR_LED,
    ATTR_LIGHT_MODE,
    ATTR_BRIGHTNESS,
    ATTR_TIMER_HOURS,
    ATTR_TIMER_TIME_ELAPSED_MINS,
}


def _get_poll_interval_minutes(options: dict) -> int:
    """Get the configured cloud poll interval, clamped to its allowed range."""
    minutes = options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_MINUTES)
    return max(MIN_POLL_INTERVAL_MINUTES, min(MAX_POLL_INTERVAL_MINUTES, minutes))


class AtombergDataUpdateCoordinator(DataUpdateCoordinator):
    """Atomberg data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: AtombergCloudAPI,
        udp_listener: UDPListener,
    ) -> None:
        """Init data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{MANUFACTURER} Coordinator",
            config_entry=config_entry,
        )

        self.update_interval = timedelta(
            minutes=_get_poll_interval_minutes(self.config_entry.options)
        )

        self.api = api
        self.udp_listener = udp_listener
        self.devices = [
            AtombergDevice(data=data, api=self.api, config_entry=self.config_entry)
            for data in self.api.device_list.values()
        ]

        # Add callback on udp listener
        self.udp_listener.add_callback(self.config_entry, self._handle_udp_update)

        # Re-apply the poll interval whenever options change (e.g. the user
        # adjusts the poll interval from the integration's options).
        self.config_entry.async_on_unload(
            self.config_entry.add_update_listener(self._handle_options_update)
        )

    def _handle_udp_update(self, data: dict) -> None:
        """Forward UDP updates to listeners."""
        self.async_set_updated_data(data)

    async def _handle_options_update(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Apply a new poll interval after options are updated."""
        new_interval = timedelta(minutes=_get_poll_interval_minutes(entry.options))
        if new_interval != self.update_interval:
            _LOGGER.debug("Updating poll interval to %s", new_interval)
            self.update_interval = new_interval

    async def _async_update_data(self) -> dict[str, str]:
        """Poll cloud state for devices without local push updates."""
        try:
            refreshed_states = await self.api.async_refresh_devices()
        except Exception as err:
            raise UpdateFailed("Failed to refresh Atomberg devices") from err

        for device in self.devices:
            state = refreshed_states.get(device.id)
            if not state:
                continue

            if device.device_type == DEVICE_TYPE_FAN:
                # Only merge analytics-style fields (e.g. power_consumption,
                # runtime); live control state is driven by UDP broadcasts.
                state = {
                    key: value
                    for key, value in state.items()
                    if key not in FAN_PUSH_DRIVEN_ATTRS
                }

            if state:
                device.update_state(state)

        return {"source": "poll"}
