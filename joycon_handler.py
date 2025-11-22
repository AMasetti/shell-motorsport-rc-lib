"""JoyCon handler module for RC car control."""
import logging
from typing import Dict, Optional, Tuple

# Handle both package and direct script execution
try:
    from .config import DEFAULT_SPEED, DEFAULT_SPEED_PROFILES, JOYCON_DEADZONE
except ImportError:
    # Fallback for direct script execution
    from config import DEFAULT_SPEED, DEFAULT_SPEED_PROFILES, JOYCON_DEADZONE

logger = logging.getLogger(__name__)


class JoyConHandler:
    """Handles JoyCon input processing for RC car control."""

    def __init__(self, default_speed: int = DEFAULT_SPEED):
        """
        Initialize the JoyCon handler.

        Args:
            default_speed: Default speed value to use
        """
        self.default_speed = default_speed

    def _apply_deadzone(self, value: float, deadzone: float = JOYCON_DEADZONE) -> float:
        """
        Apply deadzone to analog stick value.

        Args:
            value: Raw analog stick value (-1.0 to 1.0)
            deadzone: Deadzone threshold

        Returns:
            Value with deadzone applied
        """
        if abs(value) < deadzone:
            return 0.0
        return value

    def _get_speed_from_buttons(
        self, status: Dict, device_type: str
    ) -> Optional[int]:
        """
        Get speed setting from JoyCon buttons.

        Args:
            status: JoyCon status dictionary
            device_type: "Plus" or "Minus"

        Returns:
            Speed value or None if no speed button pressed
        """
        try:
            if device_type == "Plus":
                if status["buttons"]["right"]["a"]:
                    return DEFAULT_SPEED_PROFILES["low"]
                elif status["buttons"]["right"]["b"]:
                    return DEFAULT_SPEED_PROFILES["medium"]
                elif status["buttons"]["right"]["y"]:
                    return DEFAULT_SPEED_PROFILES["high"]
                elif status["buttons"]["right"]["x"]:
                    return DEFAULT_SPEED_PROFILES["max"]
            elif device_type == "Minus":
                if status["buttons"]["left"]["left"]:
                    return DEFAULT_SPEED_PROFILES["low"]
                elif status["buttons"]["left"]["down"]:
                    return DEFAULT_SPEED_PROFILES["medium"]
                elif status["buttons"]["left"]["right"]:
                    return DEFAULT_SPEED_PROFILES["high"]
                elif status["buttons"]["left"]["up"]:
                    return DEFAULT_SPEED_PROFILES["max"]
        except (KeyError, TypeError) as e:
            logger.debug(f"Error reading speed buttons: {e}")

        return None

    def parse_joycon_status(
        self, status: Dict, device_type: str = "Plus", current_speed: int = DEFAULT_SPEED
    ) -> Tuple[int, int, int, int, int]:
        """
        Parse JoyCon status and return movement commands.

        Args:
            status: JoyCon status dictionary from pyjoycon
            device_type: "Plus" or "Minus"
            current_speed: Current speed setting (used if no speed button pressed)

        Returns:
            Tuple of (forward, backward, left, right, speed)
        """
        forward = 0
        backward = 0
        left = 0
        right = 0
        speed = current_speed

        try:
            # Get speed from buttons (overrides current speed if pressed)
            speed_override = self._get_speed_from_buttons(status, device_type)
            if speed_override is not None:
                speed = speed_override

            if device_type == "Plus":
                # Right JoyCon controls
                forward = 1 if status.get("buttons", {}).get("right", {}).get("sr", False) else 0
                backward = (
                    1 if status.get("buttons", {}).get("right", {}).get("sl", False) else 0
                )

                # Analog stick for steering (with deadzone)
                analog_y = status.get("analogs", {}).get("right", {}).get("y", 0.0)
                analog_y = self._apply_deadzone(analog_y)
                left = 1 if analog_y < 0 else 0
                right = 1 if analog_y > 0 else 0

            elif device_type == "Minus":
                # Left JoyCon controls
                forward = (
                    1 if status.get("buttons", {}).get("left", {}).get("sr", False) else 0
                )
                backward = (
                    1 if status.get("buttons", {}).get("left", {}).get("sl", False) else 0
                )

                # Analog stick for steering (with deadzone)
                analog_y = status.get("analogs", {}).get("left", {}).get("y", 0.0)
                analog_y = self._apply_deadzone(analog_y)
                left = 1 if analog_y < 0 else 0
                right = 1 if analog_y > 0 else 0

        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing JoyCon status: {e}")
            return (0, 0, 0, 0, current_speed)

        return (forward, backward, left, right, speed)

