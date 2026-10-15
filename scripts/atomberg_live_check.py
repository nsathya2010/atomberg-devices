"""Minimal live API checker for Atomberg cloud endpoints."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / "atomberg.env"


def load_env(path: Path) -> dict[str, str]:
    """Load KEY=VALUE pairs from a local env file."""
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        values[key.strip()] = value.strip()
    return values


def request_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    """Run a GET request and parse the JSON response."""
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {err.code} calling {url}: {body}") from err
    except URLError as err:
        raise RuntimeError(f"Network error calling {url}: {err.reason}") from err


def main() -> int:
    """Exercise the main Atomberg cloud read endpoints."""
    if not ENV_PATH.exists():
        print(
            "Missing scripts/atomberg.env. Copy scripts/atomberg.env.example and fill in your real values.",
            file=sys.stderr,
        )
        return 1

    env = load_env(ENV_PATH)
    required_keys = [
        "ATOMBERG_BASE",
        "ATOMBERG_API_KEY",
        "ATOMBERG_REFRESH_TOKEN",
        "ATOMBERG_DEVICE_ID",
    ]
    missing = [key for key in required_keys if not env.get(key)]
    if missing:
        print(
            f"Missing values in scripts/atomberg.env: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    base = env["ATOMBERG_BASE"].rstrip("/")
    api_key = env["ATOMBERG_API_KEY"]
    refresh_token = env["ATOMBERG_REFRESH_TOKEN"]
    device_id = env["ATOMBERG_DEVICE_ID"]

    access_token_response = request_json(
        f"{base}/get_access_token",
        {
            "x-api-key": api_key,
            "Authorization": f"Bearer {refresh_token}",
        },
    )
    access_token = access_token_response["message"]["access_token"]

    auth_headers = {
        "x-api-key": api_key,
        "Authorization": f"Bearer {access_token}",
    }

    responses = {
        "get_access_token": access_token_response,
        "get_list_of_devices": request_json(f"{base}/get_list_of_devices", auth_headers),
        "get_device_state": request_json(
            f"{base}/get_device_state?device_id={device_id}", auth_headers
        ),
        "get_device_analytics": request_json(
            f"{base}/get_device_analytics?device_id={device_id}", auth_headers
        ),
    }

    print(json.dumps(responses, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())