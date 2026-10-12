"""Cloud API for Atomberg."""

import datetime
import functools
from logging import getLogger
from typing import Literal

import jwt
import requests
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.dt import utcnow
from requests import Response

_LOGGER = getLogger(__name__)

SUPPORTED_DEVICE_TYPES = {"fan", "water_purifier", "lock"}


class AtombergCloudAPI:
    """Atomberg CloudAPI."""

    def __init__(self, hass: HomeAssistant, api_key: str, refresh_token: str) -> None:
        """Init Atomberg CloudAPI."""
        self._hass = hass
        self._base_url = "https://api.developer.atomberg-iot.com/v2"
        self._api_key = api_key
        self._refresh_token = refresh_token
        self._access_token = None
        self.device_list: dict[str, dict] = {}

    async def test_connection(self):
        """Test API connection."""
        try:
            await self.async_sync_list_of_devices()
        except KeyError as e:
            _LOGGER.error("Atomberg Cloud authentication failed")
            raise InvalidAuth("Failed to authenticate") from e
        except Exception as e:
            _LOGGER.error("Atomberg Cloud connection test failed")
            raise CannotConnect("Failed to connect") from e

    async def async_get_access_token(self):
        """Get access token."""

        async def get_access_token():
            try:
                resp = await self.async_make_request(
                    "/get_access_token",
                    headers={"Authorization": f"Bearer {self._refresh_token}"},
                )
            except requests.exceptions.ConnectionError:
                return ConnectionError

            if not resp.ok:
                return

            data = resp.json()
            if data["status"] == "Success":
                self._access_token = resp.json()["message"]["access_token"]
                return self._access_token

        access_token_expired = False
        if self._access_token:
            try:
                access_token_data = jwt.decode(
                    self._access_token, options={"verify_signature": False}
                )
                exp_timestamp = access_token_data["exp"]
                exp_datetime = datetime.datetime.fromtimestamp(
                    exp_timestamp, datetime.UTC
                )
                access_token_expired = utcnow() > exp_datetime
            except jwt.ExpiredSignatureError:
                access_token_expired = True

            if not access_token_expired:
                return self._access_token

        return await get_access_token()

    async def async_make_request(
        self,
        url: str,
        method: Literal["GET", "POST"] = "GET",
        body: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Make a request."""
        headers_base = {
            "X-API-Key": self._api_key,
        }
        headers_extra = (
            headers
            if headers
            else {"Authorization": f"Bearer {await self.async_get_access_token()}"}
        )
        full_url = self._base_url + url

        match method:
            case "POST":
                func = functools.partial(
                    requests.post,
                    full_url,
                    headers=dict(headers_base, **headers_extra),
                    json=body,
                )
            case _:
                func = functools.partial(
                    requests.get, full_url, headers=dict(headers_base, **headers_extra)
                )

        resp = await self._hass.async_add_executor_job(func)
        if not resp.ok and resp.status_code < 500:
            error_msg = resp.json()["message"]
            _LOGGER.error("Request failed due to %s", error_msg)
        return resp

    async def async_sync_list_of_devices(self) -> bool:
        """Get list of all devices connected to the account."""
        resp = await self.async_make_request("/get_list_of_devices")

        data = resp.json()
        status = False
        if data.get("status") == "Success":
            supported_devices = [
                device
                for device in data["message"]["devices_list"]
                if device.get("device_type") in SUPPORTED_DEVICE_TYPES
            ]
            states = await self.async_get_device_state(supported_devices)
            analytics = await self.async_get_device_analytics(supported_devices)
            states_by_id = {state["device_id"]: state for state in states or []}
            analytics_by_id = {
                analytics_row["device_id"]: analytics_row
                for analytics_row in analytics or []
            }

            self.device_list = {}
            for dev in supported_devices:
                device_id = dev["device_id"]
                state = states_by_id.get(device_id, self._default_state(dev))
                analytics_state = analytics_by_id.get(device_id, {})
                normalized_state = {**state, **analytics_state}
                normalized_state.pop("device_id", None)
                self.device_list[device_id] = {**dev, "state": normalized_state}
            _LOGGER.info("Found %d atomberg devices", len(self.device_list))
            status = True
        else:  # noqa: RET505
            _LOGGER.error(
                "Atomberg devices sync failed due to '%s'. Please check API credentials",
                data["message"],
            )
        return status

    async def async_get_device_state(
        self, devices: list[dict] | None = None
    ) -> list[dict] | None:
        """Get state of all/single device(s)."""
        resp = await self.async_make_request("/get_device_state?device_id=all")

        data = resp.json()
        if data["status"] == "Success":
            devices_by_id = {
                device["device_id"]: device for device in devices or self.device_list.values()
            }
            return [
                self._normalize_state(state, devices_by_id[state["device_id"]])
                for state in data["message"]["device_state"]
                if state["device_id"] in devices_by_id
            ]

        return None

    async def async_get_device_analytics(
        self, devices: list[dict] | None = None
    ) -> list[dict] | None:
        """Get analytics for devices that support it."""
        resp = await self.async_make_request("/get_device_analytics?device_id=all")

        data = resp.json()
        if data["status"] == "Success":
            devices_by_id = {
                device["device_id"]: device for device in devices or self.device_list.values()
            }
            return [
                analytics
                for analytics in data["message"]["device_state"]
                if analytics["device_id"] in devices_by_id
            ]

        return None

    async def async_refresh_devices(self) -> dict[str, dict]:
        """Refresh state and analytics for tracked devices."""
        states = await self.async_get_device_state()
        analytics = await self.async_get_device_analytics()

        merged_state: dict[str, dict] = {}
        if states:
            merged_state = {row["device_id"]: row for row in states}

        if analytics:
            for analytics_row in analytics:
                merged_state.setdefault(analytics_row["device_id"], {}).update(analytics_row)

        for device_id, state in merged_state.items():
            state.pop("device_id", None)
            if device_id in self.device_list:
                self.device_list[device_id]["state"].update(state)

        return {device_id: device["state"] for device_id, device in self.device_list.items()}

    async def async_send_command(self, device_id: str, command: dict) -> bool:
        """Send command to a device."""
        _LOGGER.debug("Sending command: '%s' to %s", command, device_id)
        payload = {"device_id": device_id, "command": command}
        resp = await self.async_make_request("/send_command", "POST", body=payload)
        data = resp.json()
        return data["status"] == "Success"

    async def async_get_lock_dynamic_pin(
        self,
        device_id: str,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict | None:
        """Get a dynamic guest PIN for a lock."""
        payload = {"device_id": device_id}
        if start_time is not None and end_time is not None:
            payload["start_time"] = start_time
            payload["end_time"] = end_time

        resp = await self.async_make_request(
            "/get_lock_dynamic_pin", "POST", body=payload
        )
        data = resp.json()
        if data.get("status") == "Success":
            return data["message"]["data"]

        return None

    def _default_state(self, device: dict) -> dict:
        """Build a safe default state for a device without reported state."""
        if device["device_type"] in {"water_purifier", "lock"}:
            return {"device_id": device["device_id"], "is_online": False}

        return {
            "device_id": device["device_id"],
            "is_online": False,
            "power": False,
            "speed": 1,
            "sleep": False,
            "led": False,
            "timer_hours": 0,
            "timer_time_elapsed_mins": 0,
        }

    def _normalize_state(self, state: dict, device: dict) -> dict:
        """Normalize API state for Home Assistant entities."""
        normalized_state = dict(state)

        if device["device_type"] == "fan":
            # Fan availability is driven by recent UDP broadcasts when available.
            normalized_state["is_online"] = False
            if "last_recorded_speed" in normalized_state:
                normalized_state["speed"] = normalized_state.pop("last_recorded_speed")
            if "sleep_mode" in normalized_state:
                normalized_state["sleep"] = normalized_state.pop("sleep_mode")
            if "last_recorded_brightness" in normalized_state:
                normalized_state["brightness"] = normalized_state.pop("last_recorded_brightness")
            if "last_recorded_color" in normalized_state:
                normalized_state["light_mode"] = normalized_state.pop("last_recorded_color")

        return normalized_state


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
