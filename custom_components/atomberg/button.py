"""Button platform for Atomberg integration."""

from logging import getLogger

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CONTROL_METHOD, DOMAIN, ENTRIES, MANUFACTURER, ControlMethod
from .coordinator import AtombergDataUpdateCoordinator
from .device import DEVICE_TYPE_LOCK, AtombergDevice
from .entity import AtombergEntity, platform_async_setup_entry
from .ir_button import async_setup_entry as ir_async_setup_entry

_LOGGER = getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Atomberg button entities from a config entry."""
    if entry.data.get(CONF_CONTROL_METHOD) == ControlMethod.IR:
        await ir_async_setup_entry(hass, entry, async_add_entities)
        return

    coordinator: AtombergDataUpdateCoordinator = hass.data[DOMAIN][ENTRIES][
        entry.entry_id
    ]
    async_add_entities([AtombergRefreshButton(coordinator, entry)])

    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        AtombergDeviceRefreshButton,
    )

    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        LockDynamicPinButton,
        device_filter=lambda device: device.device_type == DEVICE_TYPE_LOCK,
    )


class AtombergRefreshButton(CoordinatorEntity, ButtonEntity):
    """Button to force an immediate cloud state refresh for all devices."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the refresh button entity."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{MANUFACTURER}.{entry.entry_id}_refresh_now"
        self._attr_name = "Refresh now"
        self._attr_icon = "mdi:cloud-refresh"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Atomberg Account",
            manufacturer=MANUFACTURER,
            model="Cloud API",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_press(self) -> None:
        """Request an immediate cloud refresh for all devices."""
        await self.coordinator.async_request_refresh()


class AtombergDeviceRefreshButton(AtombergEntity, ButtonEntity):
    """Button to refresh device state from the cloud on the device page."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(Platform.BUTTON, "refresh_now")
        self._attr_name = "Refresh now"
        self._attr_icon = "mdi:refresh"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        """Keep the refresh button available while the integration is loaded."""
        return self.coordinator.last_update_success

    async def async_press(self) -> None:
        """Request an immediate cloud refresh."""
        await self.coordinator.async_request_refresh()


class LockDynamicPinButton(AtombergEntity, ButtonEntity):
    """Button to generate a guest PIN for a supported Atomberg lock."""

    def __init__(
        self, coordinator: AtombergDataUpdateCoordinator, device: AtombergDevice
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator, device, _LOGGER)

        self._attr_unique_id = self._get_unique_id(Platform.BUTTON, "guest_pin")
        self._attr_name = self._device.name + " guest PIN"
        self._attr_icon = "mdi:form-textbox-password"
        self._attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        """Generate a guest PIN and show it in a notification."""
        pin_data = await self._device.async_get_lock_dynamic_pin()
        if not pin_data:
            return

        pin = pin_data.get("otp", "unknown")
        valid_start = pin_data.get("validStartTime", "unknown")
        valid_end = pin_data.get("validEndTime", "unknown")
        persistent_notification.async_create(
            self.hass,
            (
                f"PIN: {pin}\n"
                f"Valid start: {valid_start}\n"
                f"Valid end: {valid_end}"
            ),
            title=f"{self._device.name} guest PIN",
            notification_id=f"atomberg_{self._device.id}_guest_pin",
        )
