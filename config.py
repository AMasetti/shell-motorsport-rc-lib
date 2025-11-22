"""Configuration management for Shell Motorsport RC Car library."""
import os
from pathlib import Path
from typing import Dict, List

# Default speed profiles
DEFAULT_SPEED_PROFILES: Dict[str, int] = {
    "low": 0x16,
    "medium": 0x32,
    "high": 0x48,
    "max": 0x64,
}

# Default speed
DEFAULT_SPEED: int = 0x50

# BLE Configuration
SERVICE_UUID: str = "fff0"
WRITE_CHAR_UUID: str = "d44bc439-abfd-45a2-b575-925416129600"
NOTIFY_CHAR_UUID: str = "d44bc439-abfd-45a2-b575-925416129601"

# AES Encryption Key
AES_KEY: bytes = bytes.fromhex("34522a5b7a6e492c08090a9d8d2a23f8")
IDLE_MESSAGE: bytes = bytes.fromhex("e1055f54d880f49c2ce547267f930bf2")
CONTROL_PREFIX: bytes = b"CTL"

# File paths (configurable via environment variables)
VEHICLE_LIST_FILE: Path = Path(
    os.getenv("SHELL_MOTORSPORT_VEHICLE_LIST", "vehicle_list.json")
)
CAR_COMMANDS_FILE: Path = Path(
    os.getenv("SHELL_MOTORSPORT_COMMANDS_FILE", "car_commands.json")
)

# Connection settings
SCAN_TIMEOUT: float = 10.0  # seconds
CONNECTION_TIMEOUT: float = 10.0  # seconds
MAX_SCAN_RETRIES: int = 5
SCAN_RETRY_DELAY: float = 2.0  # seconds

# JoyCon settings
JOYCON_DEADZONE: float = 0.1  # Analog stick deadzone threshold

