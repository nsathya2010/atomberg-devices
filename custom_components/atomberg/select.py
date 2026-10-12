"""Support for select entities of Atomberg integration."""

from logging import getLogger

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AtombergDataUpdateCoordinator
from .device import (
    ATTR_TIMER_HOURS,
    ATTR_POWER,
    ATTR_SPEED,
    TIMER_MAPPING,
    DEVICE_TYPE_FAN,
    DEVICE_TYPE_WATER_PURIFIER,
    AtombergDevice,
)
from .entity import AtombergEntity, platform_async_setup_entry

_LOGGER = getLogger(__name__)

PURIFIER_MODE_OPTIONS = {
    "RO Only": 0,
    "Adaptive": 1,
    "TasteTune 50-100": 2,
    "TasteTune 75-125": 3,
    "TasteTune 100-150": 4,
    "Vacay": 10,
}

PURIFIER_FALLBACK_MODE_OPTIONS = {
    "RO Only": 0,
    "TasteTune 50-100": 2,
    "TasteTune 75-125": 3,
    "TasteTune 100-150": 4,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Automatically setup the select entities from the devices list."""
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        SetTimerSelect,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_FAN
        and device.supports_command("timer")
        and device.supports_command(ATTR_POWER)
        and device.supports_command(ATTR_SPEED),
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierModeSelect,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER
        and device.supports_command("mode"),
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierFallbackModeSelect,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER
        and device.supports_command("fallback_mode"),
    )


class SetTimerSelect(AtombergEntity, SelectEntity):
    """Set timer select entity."""

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(Platform.SELECT, suffix="set_timer")
        self._attr_name = self._device.name + " set timer"
        self._attr_icon = "mdi:av-timer"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def options(self) -> list[str]:
        """Get the available options."""
        return [_t[1] for _t in TIMER_MAPPING]

    @property
    def current_option(self) -> str:
        """Get the current option."""
        return next(
            filter(
                lambda _t: _t[0] == self.device_state[ATTR_TIMER_HOURS],
                TIMER_MAPPING,
            )
        )[1]

    async def async_select_option(self, option: str) -> None:
        """When selected an option."""
        await self._device.async_set_timer(self.options.index(option))


class PurifierBaseSelect(AtombergEntity, SelectEntity):
    """Base select entity for Atomberg water purifiers."""

    _command: str
    _options_map: dict[str, int]

    @property
    def options(self) -> list[str]:
        """Get the available options."""
        return list(self._options_map)

    @property
    def current_option(self) -> str | None:
        """Get the current option."""
        current_value = self.device_state.get(self._command)
        for label, value in self._options_map.items():
            if value == current_value:
                return label
        return None

    async def async_select_option(self, option: str) -> None:
        """Set purifier option."""
        await self._device.async_send_command({self._command: self._options_map[option]})


class PurifierModeSelect(PurifierBaseSelect):
    """Purifier mode selector."""

    _command = "mode"
    _options_map = PURIFIER_MODE_OPTIONS

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(Platform.SELECT, suffix="mode")
        self._attr_name = self._device.name + " mode"
        self._attr_icon = "mdi:water-boiler"
        self._attr_entity_category = EntityCategory.CONFIG


class PurifierFallbackModeSelect(PurifierBaseSelect):
    """Purifier fallback mode selector."""

    _command = "fallback_mode"
    _options_map = PURIFIER_FALLBACK_MODE_OPTIONS

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(
            Platform.SELECT, suffix="fallback_mode"
        )
        self._attr_name = self._device.name + " fallback mode"
        self._attr_icon = "mdi:water-sync"
        self._attr_entity_category = EntityCategory.CONFIG
