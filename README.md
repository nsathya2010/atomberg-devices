# Atomberg Smart Devices

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

*Standalone Home Assistant integration for **Atomberg smart fans, water purifiers, and smart locks***

This project is based on the original [dasshubham762/atomberg-integration](https://github.com/dasshubham762/atomberg-integration) repository and extends it with broader public API device coverage.

## Tested on
- **[Atomberg Renesa+ Ceiling Fan](https://atomberg.com/atomberg-renesa-smart-iot-enabled-ceiling-fans-with-bldc-motor-and-remote)**
- **[Atomberg Aris Ceiling Fan](https://atomberg.com/aris-ceiling-fan)**
- **[Atomberg Erica Ceiling Fan](https://atomberg.com/erica-ceiling-fan)**
- **Atomberg Intellon Water Purifier API model W2**
- **Atomberg Cypheo Elite / G1 Smart Lock API**

## Installation

### Method 1: Using HACS

1. Open your Home Assistant UI.
2. Go to "HACS" (Home Assistant Community Store).
3. Search for "Atomberg" in the search bar.
4. You should see the Atomberg integration listed.
5. Click "Install" and follow any prompts to complete the installation.

### Method 2: Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `atomberg`.
4. Download _all_ the files from the `custom_components/atomberg/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant.

## Configuration

### Step 1: Generate API Key and Refresh Token
1. Go to [Atomberg Developer Portal](https://developer.atomberg-iot.com/#overview).
2. Follow the instructions to generate your `api_key` and `refresh_token`.

### Step 2: Add Atomberg Integration to Home Assistant
1. Open your Home Assistant UI.
2. Navigate to "Configuration" -> "Integrations".
3. Click the "+" icon to add a new integration.
4. Search for "Atomberg" in the integration search bar and select it.

### Step 3: Enter API Key and Refresh Token
1. Enter your `api_key` and `refresh_token` in the appropriate fields.
2. Submit the form.

## Compatibility and Requirements

- Please note that this integration is designed for Atomberg devices supported by the public developer API, including supported smart fans, the Intellon water purifier, and supported smart locks.
- The integration relies on cloud APIs for initialization (cloud control mode).
- This integration uses UDP port `5625` for updating fan state locally. Water purifier and smart lock state are refreshed through the cloud API, so no local UDP updates are required for those device types.

## Control Methods

This integration supports two control methods. You choose which one to use during setup.

### Cloud API Control

Uses the Atomberg cloud APIs for supported fan, water purifier, and smart lock integration. Requires an `api_key` and `refresh_token` from the [Atomberg Developer Portal](https://developer.atomberg-iot.com/#overview). Provides fan controls, water purifier mode and telemetry entities, lock state and diagnostic entities, and guest PIN generation for supported locks.

The cloud setup creates entities based on each device's `device_type`, reported state, analytics data, and `supported_commands`. This means the integration only exposes features that the Atomberg API says a given device actually supports.

#### Fan entity coverage

Fan features are enabled from each device's `supported_commands` list returned by the Atomberg API. The integration does not assume every fan model supports every advanced feature.

Cloud fan entities currently map as follows:

| API capability | Home Assistant entity | Availability |
| --- | --- | --- |
| `power`, `speed` | `fan` | Supported fan models |
| `sleep` | `switch` | Only when `sleep` is listed in `supported_commands` |
| `timer` | `select` and elapsed-time `sensor` | Only when `timer` is listed in `supported_commands` |
| `led` | `light` | Only when `led` is listed in `supported_commands` |
| `brightness` | `light` brightness | Only when `brightness` is listed in `supported_commands` |
| `light_mode` | `light` effect | Only when `light_mode` is listed in `supported_commands` |
| `rev_mode` | `switch` | Only when `rev_mode` is listed in `supported_commands` |
| `buzzer_status` | `switch` | Only when `buzzer_status` is listed in `supported_commands` |
| analytics | diagnostic `sensor`s | Available for fan models that return analytics |

This was validated against the integration's bundled [openapi.yaml](c:/Users/z004u01a/Documents/esp-home/atomberg/atomberg-integration/openapi.yaml), which documents `supported_commands` as the source of truth for per-model fan feature support.

#### Water purifier entity coverage

Cloud water purifier entities currently map as follows:

| API capability | Home Assistant entity | Availability |
| --- | --- | --- |
| `mode` | `select` | Only when `mode` is listed in `supported_commands` |
| `fallback_mode` | `select` | Only when `fallback_mode` is listed in `supported_commands` |
| `idle_sleep` | `switch` | Only when `idle_sleep` is listed in `supported_commands` |
| `tds_threshold` | `number` | Only when `tds_threshold` is listed in `supported_commands` |
| `input_tds` | diagnostic `sensor` | When reported by the device state API |
| `tank_tds` | diagnostic `sensor` | When reported by the device state API |
| `choking_faults` | diagnostic `sensor` | When reported by the device state API |
| `system_faults` | diagnostic `sensor` | When reported by the device state API |
| `water_saved_liters` | diagnostic `sensor` | When returned by the analytics API |
| `uv_runtime_hours` | diagnostic `sensor` | When returned by the analytics API |

Current purifier limitation:

- The public API supports `sleep_mode`, `start_utc`, and `stop_utc`, but the integration does not yet expose purifier sleep-window entities.

#### Smart lock entity coverage

Cloud smart lock entities currently map as follows:

| API capability | Home Assistant entity | Availability |
| --- | --- | --- |
| `battery` | diagnostic `sensor` | When reported by the device state API |
| `n_unlocks` | diagnostic `sensor` | When reported by the device state API |
| `esp_fw_version` | diagnostic `sensor` | When reported by the device state API |
| `settings` | diagnostic `sensor` with extra attributes | When reported by the device state API |
| guest PIN generation | `button` | For supported lock models via `get_lock_dynamic_pin` |
| generated guest PIN window | diagnostic `sensor`s | Stored after generating a PIN from the button |

Current lock notes:

- Locks do not support `send_command` through the public API, so the integration does not create control switches or selects for lock actuation.
- Pressing the guest PIN button creates a Home Assistant persistent notification with the PIN and validity window.
- For `smart_lock_black`, the integration currently requests a 4-hour PIN window, matching the API's required `start_time` and `end_time` flow.

#### Cloud behavior notes

- Fan availability is refreshed locally from UDP broadcasts when available.
- Water purifier and smart lock state are refreshed through the cloud API on the coordinator polling interval.
- Fan and purifier analytics come from the `get_device_analytics` endpoint. Locks do not expose analytics through the API.

### Infrared (IR) Control

Uses an infrared transmitter to send NEC protocol commands directly to your Atomberg fan. No cloud credentials needed. Requires Home Assistant 2026.4.0 or later.

#### Prerequisites

1. **Home Assistant 2026.4.0+** — The integration depends on HA's built-in `infrared` entity platform.
2. **An IR emitter device** — Any device that exposes an infrared transmitter entity to Home Assistant. Common options:
   - **ESPHome IR proxy** — ESP32/ESP8266 with an IR LED, using the [`ir_rf_proxy`](https://esphome.io/components/ir_rf_proxy/) component.
   - **Seeed XIAO IR Mate** — Dedicated IR blaster device.
   - **Broadlink RM devices** — Via the Broadlink integration's infrared transmitter entities.

#### Setup

1. Ensure your IR emitter device is already set up in Home Assistant and appears as an infrared transmitter entity.
2. Add the Atomberg integration and select **"Infrared (IR)"** as the control method.
3. Select your fan model from the dropdown.
4. Select the infrared transmitter entity to use.
5. Position the IR emitter so it has line-of-sight to your Atomberg fan's IR receiver.

#### Entities

The IR setup creates the following entities:

| Entity | Type | Description |
|--------|------|-------------|
| Fan | `fan` | On/off and speed control (6 speeds including boost) |
| Boost | `button` | Activate boost mode (speed 6) |
| LED | `button` | Toggle the fan's LED indicator |
| Sleep Mode | `button` | Toggle sleep mode |
| Timer | `button` | Toggle timer |
| Timer 1 Hour | `button` | Set timer to 1 hour |
| Timer 2 Hours | `button` | Set timer to 2 hours |
| Timer 3 Hours | `button` | Set timer to 3 hours |
| Timer 6 Hours | `button` | Set timer to 6 hours |

#### Important Limitations

- **One-way communication** — IR is transmit-only. The integration tracks assumed state internally but cannot detect if the fan is controlled by the physical remote. If you use the physical remote, resync the entity in Home Assistant by toggling it.
- **Line of sight required** — The IR emitter must be able to "see" the fan's IR receiver. Obstructions will prevent commands from being received.
- **NEC protocol** — Atomberg fans use NEC protocol with address `0xF300`. The IR codes are based on community-decoded values and are compatible with Gorilla Efficio, Renesa, Aris, Erica, and other Atomberg models.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

- Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template
- Atomberg IoT Team


[integration_blueprint]: https://github.com/ludeeus/integration_blueprint
[commits-shield]: https://img.shields.io/github/commit-activity/y/nsathya2010/atomberg-devices.svg?style=for-the-badge
[commits]: https://github.com/nsathya2010/atomberg-devices/commits/main
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/nsathya2010/atomberg-devices.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40nsathya2010-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/nsathya2010/atomberg-devices.svg?style=for-the-badge
[releases]: https://github.com/nsathya2010/atomberg-devices/releases
