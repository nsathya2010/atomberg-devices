"""Support for switch entities of Atomberg integration."""

from logging import getLogger
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AtombergDataUpdateCoordinator
from .device import (
    ATTR_BUZZER_STATUS,
    ATTR_REV_MODE,
    ATTR_SLEEP,
    DEVICE_TYPE_FAN,
    DEVICE_TYPE_WATER_PURIFIER,
    AtombergDevice,
)
from .entity import AtombergEntity, platform_async_setup_entry

_LOGGER = getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Automatically setup the switch entities from the devices list."""
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        AtombergSleepModeSwitchEntity,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_FAN
        and device.supports_command(ATTR_SLEEP),
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        AtombergReverseModeSwitchEntity,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_FAN
        and device.supports_command(ATTR_REV_MODE),
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        AtombergBuzzerStatusSwitchEntity,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_FAN
        and device.supports_command(ATTR_BUZZER_STATUS),
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierIdleSleepSwitchEntity,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER
        and device.supports_command("idle_sleep"),
    )


class AtombergSleepModeSwitchEntity(AtombergEntity, SwitchEntity):
    """Sleep mode entity for atomberg Fan."""

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Init sleep mode entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_name = self._device.name + " sleep mode"
        self._attr_unique_id = self._get_unique_id(Platform.SWITCH, ATTR_SLEEP)
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        """Whether the fan sleep mode is on."""
        return self.device_state[ATTR_SLEEP]

    @property
    def icon(self) -> str | None:
        """Get dynamic icon."""
        return "mdi:sleep" if self.is_on else "mdi:sleep-off"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on entity."""
        await self._device.async_turn_on_sleep_mode()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off entity."""
        await self._device.async_turn_off_sleep_mode()


class AtombergReverseModeSwitchEntity(AtombergEntity, SwitchEntity):
    """Reverse mode entity for Atomberg fans."""

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Init reverse mode entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_name = self._device.name + " reverse mode"
        self._attr_unique_id = self._get_unique_id(Platform.SWITCH, ATTR_REV_MODE)
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:swap-horizontal"

    @property
    def is_on(self) -> bool:
        """Whether reverse mode is on."""
        return bool(self.device_state.get(ATTR_REV_MODE, False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on reverse mode."""
        await self._device.async_send_command({ATTR_REV_MODE: True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off reverse mode."""
        await self._device.async_send_command({ATTR_REV_MODE: False})


class AtombergBuzzerStatusSwitchEntity(AtombergEntity, SwitchEntity):
    """Buzzer status entity for Atomberg fans."""

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Init buzzer status entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_name = self._device.name + " buzzer"
        self._attr_unique_id = self._get_unique_id(
            Platform.SWITCH, ATTR_BUZZER_STATUS
        )
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        """Whether buzzer feedback is on."""
        return bool(self.device_state.get(ATTR_BUZZER_STATUS, False))

    @property
    def icon(self) -> str:
        """Return a dynamic icon."""
        return "mdi:volume-high" if self.is_on else "mdi:volume-off"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on buzzer feedback."""
        await self._device.async_send_command({ATTR_BUZZER_STATUS: True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off buzzer feedback."""
        await self._device.async_send_command({ATTR_BUZZER_STATUS: False})


class PurifierIdleSleepSwitchEntity(AtombergEntity, SwitchEntity):
    """Idle sleep switch for Atomberg water purifiers."""

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Init purifier idle sleep switch."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_name = self._device.name + " idle sleep"
        self._attr_unique_id = self._get_unique_id(Platform.SWITCH, "idle_sleep")
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:sleep"

    @property
    def is_on(self) -> bool:
        """Whether idle sleep is on."""
        return bool(self.device_state.get("idle_sleep", 0))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on idle sleep."""
        await self._device.async_send_command({"idle_sleep": 1})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off idle sleep."""
        await self._device.async_send_command({"idle_sleep": 0})
