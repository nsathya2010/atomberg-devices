"""Support for number entities of Atomberg integration."""

from logging import getLogger

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AtombergDataUpdateCoordinator
from .device import DEVICE_TYPE_WATER_PURIFIER, AtombergDevice
from .entity import AtombergEntity, platform_async_setup_entry

_LOGGER = getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Atomberg number entities."""
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        PurifierTDSThresholdNumber,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_WATER_PURIFIER
        and device.supports_command("tds_threshold"),
    )


class PurifierTDSThresholdNumber(AtombergEntity, NumberEntity):
    """TDS threshold number entity for Atomberg water purifiers."""

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(
            Platform.NUMBER, suffix="tds_threshold"
        )
        self._attr_name = self._device.name + " TDS threshold"
        self._attr_native_min_value = 100
        self._attr_native_max_value = 300
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "ppm"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:tune-variant"

    @property
    def native_value(self) -> float | None:
        """Get the configured threshold."""
        return self.device_state.get("tds_threshold")

    async def async_set_native_value(self, value: float) -> None:
        """Set the TDS threshold."""
        await self._device.async_send_command({"tds_threshold": int(value)})