"""Constants for the Atomberg integration."""

from enum import StrEnum

DOMAIN = "atomberg"

UDP_LISTENER = "udp_listener"
ENTRIES = "entries"

CONF_REFRESH_TOKEN = "refresh_token"
CONF_USE_CLOUD_CONTROL = "use_cloud_control"
CONF_CONTROL_METHOD = "control_method"
CONF_IR_EMITTER_ENTITY = "ir_emitter_entity"
CONF_FAN_MODEL = "fan_model"
CONF_POLL_INTERVAL = "purifier_poll_interval"
MANUFACTURER = "Atomberg"

# How often (in minutes) the cloud is polled for state that has no local
# push update (water purifiers, locks, and fan analytics). The Atomberg
# cloud API allows 100 calls/day; the default of 30 minutes uses 48 of them
# (2 endpoint calls per poll).
DEFAULT_POLL_INTERVAL_MINUTES = 30
MIN_POLL_INTERVAL_MINUTES = 20
MAX_POLL_INTERVAL_MINUTES = 60


class ControlMethod(StrEnum):
    """Control method for Atomberg devices."""

    CLOUD = "cloud"
    IR = "ir"


class FanModel(StrEnum):
    """Supported Atomberg fan models for IR control."""

    RENESA_PLUS = "renesa_plus"
    ARIS = "aris"
    ERICA = "erica"
    GORILLA_EFFICIO = "gorilla_efficio"
    EFFICIO_PLUS_400MM_PEDESTAL = "efficio_plus_400mm_pedestal"
    GENERIC = "generic"


FAN_MODEL_NAMES = {
    FanModel.RENESA_PLUS: "Renesa+",
    FanModel.ARIS: "Aris",
    FanModel.ERICA: "Erica",
    FanModel.GORILLA_EFFICIO: "Gorilla Efficio",
    FanModel.EFFICIO_PLUS_400MM_PEDESTAL: "Efficio+ 400mm Pedestal",
    FanModel.GENERIC: "Generic",
}
