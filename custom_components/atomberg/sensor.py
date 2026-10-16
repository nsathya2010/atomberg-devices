"""Support for sensor entities of Atomberg integration."""

from logging import getLogger

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AtombergDataUpdateCoordinator
from .device import (
    ATTR_TIMER_HOURS,
    ATTR_TIMER_TIME_ELAPSED_MINS,
    DEVICE_TYPE_FAN,
    DEVICE_TYPE_LOCK,
    DEVICE_TYPE_WATER_PURIFIER,
    AtombergDevice,
)
from .entity import AtombergEntity, platform_async_setup_entry

_LOGGER = getLogger(__name__)

PURIFIER_FAULT_FIELDS = {
    "choking_faults": "choking faults",
    "system_faults": "system faults",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Automatically setup the sensor entities from the devices list."""
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        TimerElapsedTimeSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_FAN
        and device.supports_command("timer"),
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        FanPowerConsumptionSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_FAN,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        FanRuntimeSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_FAN,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierInputTDSSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierTankTDSSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierWaterSavedSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierUvRuntimeSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierChokingFaultSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierSystemFaultSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        LockBatterySensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_LOCK,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        LockUnlockCountSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_LOCK,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        LockFirmwareSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_LOCK,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        LockGuestPinSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_LOCK,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        LockGuestPinValidStartSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_LOCK,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        LockGuestPinValidEndSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_LOCK,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        LockSettingsSensor,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_LOCK,
    )


class TimerElapsedTimeSensor(AtombergEntity, SensorEntity):
    """Timer elapsed time sensor entity."""

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="timer_elapsed_time"
        )
        self._attr_name = self._device.name + " timer elapsed time"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "min"

    @property
    def icon(self) -> str:
        """Get icon dynamically."""
        icons = [
            "mdi:clock-time-twelve-outline",
            "mdi:clock-time-one-outline",
            "mdi:clock-time-two-outline",
            "mdi:clock-time-three-outline",
            "mdi:clock-time-four-outline",
            "mdi:clock-time-five-outline",
            "mdi:clock-time-six-outline",
            "mdi:clock-time-seven-outline",
            "mdi:clock-time-eight-outline",
            "mdi:clock-time-nine-outline",
            "mdi:clock-time-ten-outline",
            "mdi:clock-time-eleven-outline",
        ]
        timer_mins = self.device_state[ATTR_TIMER_HOURS] * 60
        if not timer_mins:
            return icons[0]

        return icons[round(self.native_value / timer_mins * (len(icons) - 1))]

    @property
    def native_value(self) -> int:
        """Get value in minutes."""
        return self.device_state[ATTR_TIMER_TIME_ELAPSED_MINS]


class FanAnalyticsSensor(AtombergEntity, SensorEntity):
    """Base analytics sensor for Atomberg fans."""

    _state_key: str

    @property
    def native_value(self):
        """Return the current analytics value."""
        return self.device_state.get(self._state_key)


class FanPowerConsumptionSensor(FanAnalyticsSensor):
    """Power consumption analytics sensor for Atomberg fans."""

    _state_key = "power_consumption"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="power_consumption"
        )
        self._attr_name = self._device.name + " power consumption"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class FanRuntimeSensor(FanAnalyticsSensor):
    """Runtime analytics sensor for Atomberg fans."""

    _state_key = "runtime"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(Platform.SENSOR, suffix="runtime")
        self._attr_name = self._device.name + " runtime"
        self._attr_native_unit_of_measurement = "h"
        self._attr_icon = "mdi:clock-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class PurifierBaseSensor(AtombergEntity, SensorEntity):
    """Base sensor for Atomberg water purifiers."""

    _state_key: str

    @property
    def native_value(self):
        """Return the current sensor value."""
        return self.device_state.get(self._state_key)


class PurifierInputTDSSensor(PurifierBaseSensor):
    """Input TDS sensor."""

    _state_key = "input_tds"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(Platform.SENSOR, suffix="input_tds")
        self._attr_name = self._device.name + " input TDS"
        self._attr_native_unit_of_measurement = "ppm"
        self._attr_icon = "mdi:waves-arrow-up"


class PurifierTankTDSSensor(PurifierBaseSensor):
    """Tank TDS sensor."""

    _state_key = "tank_tds"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(Platform.SENSOR, suffix="tank_tds")
        self._attr_name = self._device.name + " tank TDS"
        self._attr_native_unit_of_measurement = "ppm"
        self._attr_icon = "mdi:waves-arrow-down"


class PurifierWaterSavedSensor(PurifierBaseSensor):
    """Water saved analytics sensor."""

    _state_key = "water_saved_liters"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="water_saved_liters"
        )
        self._attr_name = self._device.name + " water saved"
        self._attr_native_unit_of_measurement = "L"
        self._attr_icon = "mdi:water-plus"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class PurifierUvRuntimeSensor(PurifierBaseSensor):
    """UV runtime analytics sensor."""

    _state_key = "uv_runtime_hours"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="uv_runtime_hours"
        )
        self._attr_name = self._device.name + " UV runtime"
        self._attr_native_unit_of_measurement = "h"
        self._attr_icon = "mdi:lightbulb-cfl"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class PurifierFaultSensor(AtombergEntity, SensorEntity):
    """Base fault sensor for Atomberg water purifiers."""

    _state_key: str

    @property
    def native_value(self) -> str | None:
        """Return the summarized fault state."""
        fault_state = self.device_state.get(self._state_key)
        if fault_state is None:
            return None
        if fault_state.get("healthy", True):
            return "healthy"

        return ", ".join(fault_state.get("codes", [])) or "fault"


class PurifierChokingFaultSensor(PurifierFaultSensor):
    """Choking fault sensor."""

    _state_key = "choking_faults"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="choking_faults"
        )
        self._attr_name = self._device.name + " choking faults"
        self._attr_icon = "mdi:water-alert"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class PurifierSystemFaultSensor(PurifierFaultSensor):
    """System fault sensor."""

    _state_key = "system_faults"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="system_faults"
        )
        self._attr_name = self._device.name + " system faults"
        self._attr_icon = "mdi:alert-circle-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class LockBaseSensor(AtombergEntity, SensorEntity):
    """Base sensor for Atomberg locks."""

    _state_key: str

    @property
    def native_value(self):
        """Return the current sensor value."""
        return self.device_state.get(self._state_key)


class LockBatterySensor(LockBaseSensor):
    """Battery level sensor for Atomberg locks."""

    _state_key = "battery"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)
        self._attr_unique_id = self._get_unique_id(Platform.SENSOR, suffix="battery")
        self._attr_name = self._device.name + " battery"
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:battery"


class LockUnlockCountSensor(LockBaseSensor):
    """Unlock counter sensor for Atomberg locks."""

    _state_key = "n_unlocks"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)
        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="unlock_count"
        )
        self._attr_name = self._device.name + " unlock count"
        self._attr_icon = "mdi:counter"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class LockFirmwareSensor(LockBaseSensor):
    """Firmware sensor for Atomberg locks."""

    _state_key = "esp_fw_version"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)
        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="firmware"
        )
        self._attr_name = self._device.name + " firmware"
        self._attr_icon = "mdi:chip"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class LockGuestPinSensor(LockBaseSensor):
    """Last generated guest PIN sensor for Atomberg locks."""

    _state_key = "last_guest_pin"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)
        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="last_guest_pin"
        )
        self._attr_name = self._device.name + " last guest PIN"
        self._attr_icon = "mdi:key-wireless"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class LockGuestPinValidStartSensor(LockBaseSensor):
    """Guest PIN valid start sensor for Atomberg locks."""

    _state_key = "last_guest_pin_valid_start"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)
        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="last_guest_pin_valid_start"
        )
        self._attr_name = self._device.name + " guest PIN valid start"
        self._attr_icon = "mdi:calendar-start"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class LockGuestPinValidEndSensor(LockBaseSensor):
    """Guest PIN valid end sensor for Atomberg locks."""

    _state_key = "last_guest_pin_valid_end"

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)
        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="last_guest_pin_valid_end"
        )
        self._attr_name = self._device.name + " guest PIN valid end"
        self._attr_icon = "mdi:calendar-end"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class LockSettingsSensor(AtombergEntity, SensorEntity):
    """Settings summary sensor for Atomberg locks."""

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)
        self._attr_unique_id = self._get_unique_id(
            Platform.SENSOR, suffix="settings"
        )
        self._attr_name = self._device.name + " settings"
        self._attr_icon = "mdi:cog"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        """Return a summary state for lock settings."""
        return "configured"

    @property
    def extra_state_attributes(self) -> dict:
        """Return lock settings as attributes."""
        return self.device_state.get("settings", {})
