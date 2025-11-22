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
        # Track center position for offset axes (e.g., rotated JoyCon Y-axis)
        self._y_center = None
        self._y_min = float('inf')
        self._y_max = float('-inf')
        self._center_samples = []
        self._center_calibrated = False

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

    def _update_center_calibration(self, y_value: float, max_samples: int = 100):
        """
        Update center position calibration for offset axes.

        Args:
            y_value: Current Y-axis value
            max_samples: Maximum number of samples to collect before calculating center
        """
        if y_value != 0.0:
            self._y_min = min(self._y_min, y_value)
            self._y_max = max(self._y_max, y_value)
            self._center_samples.append(y_value)

            # Calculate center after collecting enough samples
            if len(self._center_samples) >= max_samples and not self._center_calibrated:
                # Use average of min/max as center, or median of samples
                if self._y_min != float('inf') and self._y_max != float('-inf'):
                    self._y_center = (self._y_min + self._y_max) / 2.0
                    self._center_calibrated = True
                    logger.info(f"[CALIBRATION] Y-axis center calibrated: {self._y_center:.3f} (range: {self._y_min:.3f} to {self._y_max:.3f})")
                else:
                    # Fallback: use median of samples
                    sorted_samples = sorted(self._center_samples)
                    self._y_center = sorted_samples[len(sorted_samples) // 2]
                    self._center_calibrated = True
                    logger.info(f"[CALIBRATION] Y-axis center calibrated (median): {self._y_center:.3f}")

    def _get_steering_from_offset_axis(self, axis_value: float, center: float, threshold: float = JOYCON_DEADZONE) -> Tuple[int, int]:
        """
        Get left/right steering commands from an offset axis (values don't cross zero).

        Args:
            axis_value: Current axis value
            center: Center/neutral position
            threshold: Threshold for detecting movement away from center

        Returns:
            Tuple of (left, right) flags
        """
        if center is None:
            # Not calibrated yet, use fixed center based on observed range
            center = 0.057  # Approximate center for 0.024-0.090 range

        # Calculate offset from center
        offset = axis_value - center

        # Apply threshold relative to center
        if abs(offset) < threshold:
            return (0, 0)  # Within deadzone

        # Determine direction
        left = 1 if offset < 0 else 0
        right = 1 if offset > 0 else 0

        return (left, right)

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
        self, status: Dict, device_type: str = "Plus", current_speed: int = DEFAULT_SPEED, rotated: bool = False
    ) -> Tuple[int, int, int, int, int]:
        """
        Parse JoyCon status and return movement commands.

        Args:
            status: JoyCon status dictionary from pyjoycon
            device_type: "Plus" or "Minus"
            current_speed: Current speed setting (used if no speed button pressed)
            rotated: Whether the JoyCon is rotated (single controller mode).
                    When True, uses y-axis as horizontal steering axis.

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

                # Analog stick for steering
                # For rotated single JoyCon: y-axis becomes horizontal (when rotated 90°)
                # For normal orientation: x-axis is horizontal

                # Try multiple possible structures for analog values
                analog_x_raw = 0.0
                analog_y_raw = 0.0

                # Try different possible structures
                if "analogs" in status and "right" in status["analogs"]:
                    analogs_right = status["analogs"]["right"]
                    analog_x_raw = analogs_right.get("x", analogs_right.get("stick_x", analogs_right.get("horizontal", 0.0)))
                    analog_y_raw = analogs_right.get("y", analogs_right.get("stick_y", analogs_right.get("vertical", 0.0)))
                elif "analog-sticks" in status and "right" in status["analog-sticks"]:
                    stick_right = status["analog-sticks"]["right"]
                    analog_x_raw = stick_right.get("x", stick_right.get("horizontal", stick_right.get("stick_x", 0.0)))
                    analog_y_raw = stick_right.get("y", stick_right.get("vertical", stick_right.get("stick_y", 0.0)))
                elif "stick" in status and "right" in status["stick"]:
                    stick_right = status["stick"]["right"]
                    analog_x_raw = stick_right.get("x", stick_right.get("horizontal", 0.0))
                    analog_y_raw = stick_right.get("y", stick_right.get("vertical", 0.0))
                elif "right_stick_x" in status or "right_stick_y" in status:
                    analog_x_raw = status.get("right_stick_x", 0.0)
                    analog_y_raw = status.get("right_stick_y", 0.0)

                # Handle raw integer values (pyjoycon might return integers that need normalization)
                if isinstance(analog_x_raw, int):
                    # Normalize from -32768 to 32767 range to -1.0 to 1.0
                    analog_x_raw = analog_x_raw / 32768.0 if analog_x_raw != 0 else 0.0
                if isinstance(analog_y_raw, int):
                    # Normalize from -32768 to 32767 range to -1.0 to 1.0
                    analog_y_raw = analog_y_raw / 32768.0 if analog_y_raw != 0 else 0.0

                # Debug: Log all available keys
                if logger.isEnabledFor(logging.INFO):
                    if "analogs" in status:
                        logger.info(f"[AXIS DEBUG] Available in status['analogs']: {list(status['analogs'].keys())}")
                    if "analog-sticks" in status:
                        logger.info(f"[AXIS DEBUG] Available in status['analog-sticks']: {list(status['analog-sticks'].keys())}")
                    if "stick" in status:
                        logger.info(f"[AXIS DEBUG] Available in status['stick']: {list(status['stick'].keys())}")

                if rotated:
                    # When rotated, Y-axis is horizontal but has offset (always positive)
                    # Update center calibration
                    self._update_center_calibration(analog_y_raw)

                    # Check if X-axis has negative values (could be better for left turns)
                    if analog_x_raw < 0:
                        # X-axis has negative values, use it for steering
                        steering_axis = analog_x_raw
                        axis_name = "X (has negative values)"
                        steering_axis_raw = steering_axis
                        steering_axis = self._apply_deadzone(steering_axis)
                        left = 1 if steering_axis < 0 else 0
                        right = 1 if steering_axis > 0 else 0
                    else:
                        # Use Y-axis with center-relative comparison
                        steering_axis = analog_y_raw
                        axis_name = "Y (rotated, offset)"
                        steering_axis_raw = steering_axis
                        # Use center-relative comparison for offset axis
                        left, right = self._get_steering_from_offset_axis(analog_y_raw, self._y_center)
                        steering_axis = analog_y_raw - (self._y_center if self._y_center else 0.057)  # For logging
                else:
                    # Normal orientation: use x-axis for horizontal steering
                    steering_axis = analog_x_raw
                    axis_name = "X (normal)"
                    steering_axis_raw = steering_axis
                    steering_axis = self._apply_deadzone(steering_axis)
                    left = 1 if steering_axis < 0 else 0
                    right = 1 if steering_axis > 0 else 0

                # Log steering info - more detailed when values pass deadzone
                if left or right:
                    # Steering command will be generated
                    center_info = f", center={self._y_center:.3f}" if self._y_center else ""
                    logger.info(
                        f"[STEERING ACTIVE] Plus JoyCon - "
                        f"X={analog_x_raw:.3f}, Y={analog_y_raw:.3f}{center_info}, "
                        f"Using {axis_name}={steering_axis_raw:.3f}, "
                        f"left={left}, right={right}, rotated={rotated}"
                    )
                elif abs(steering_axis_raw) > 0.01 or abs(analog_y_raw) > 0.01:
                    # Value detected but no steering command
                    center_info = f", center={self._y_center:.3f}" if self._y_center else ""
                    logger.debug(
                        f"[STEERING FILTERED] Plus JoyCon - "
                        f"X={analog_x_raw:.3f}, Y={analog_y_raw:.3f}{center_info}, "
                        f"Using {axis_name}={steering_axis_raw:.3f}, "
                        f"left={left}, right={right}"
                    )

            elif device_type == "Minus":
                # Left JoyCon controls
                forward = (
                    1 if status.get("buttons", {}).get("left", {}).get("sr", False) else 0
                )
                backward = (
                    1 if status.get("buttons", {}).get("left", {}).get("sl", False) else 0
                )

                # Analog stick for steering
                # For rotated single JoyCon: y-axis becomes horizontal (when rotated 90°)
                # For normal orientation: x-axis is horizontal

                # Try multiple possible structures for analog values
                analog_x_raw = 0.0
                analog_y_raw = 0.0

                # Try different possible structures
                if "analogs" in status and "left" in status["analogs"]:
                    analogs_left = status["analogs"]["left"]
                    analog_x_raw = analogs_left.get("x", analogs_left.get("stick_x", analogs_left.get("horizontal", 0.0)))
                    analog_y_raw = analogs_left.get("y", analogs_left.get("stick_y", analogs_left.get("vertical", 0.0)))
                elif "analog-sticks" in status and "left" in status["analog-sticks"]:
                    stick_left = status["analog-sticks"]["left"]
                    analog_x_raw = stick_left.get("x", stick_left.get("horizontal", stick_left.get("stick_x", 0.0)))
                    analog_y_raw = stick_left.get("y", stick_left.get("vertical", stick_left.get("stick_y", 0.0)))
                elif "stick" in status and "left" in status["stick"]:
                    stick_left = status["stick"]["left"]
                    analog_x_raw = stick_left.get("x", stick_left.get("horizontal", 0.0))
                    analog_y_raw = stick_left.get("y", stick_left.get("vertical", 0.0))
                elif "left_stick_x" in status or "left_stick_y" in status:
                    analog_x_raw = status.get("left_stick_x", 0.0)
                    analog_y_raw = status.get("left_stick_y", 0.0)

                # Handle raw integer values (pyjoycon might return integers that need normalization)
                if isinstance(analog_x_raw, int):
                    # Normalize from -32768 to 32767 range to -1.0 to 1.0
                    analog_x_raw = analog_x_raw / 32768.0 if analog_x_raw != 0 else 0.0
                if isinstance(analog_y_raw, int):
                    # Normalize from -32768 to 32767 range to -1.0 to 1.0
                    analog_y_raw = analog_y_raw / 32768.0 if analog_y_raw != 0 else 0.0

                if rotated:
                    # When rotated, Y-axis is horizontal but has offset (always positive)
                    # Update center calibration
                    self._update_center_calibration(analog_y_raw)

                    # Check if X-axis has negative values (could be better for left turns)
                    if analog_x_raw < 0:
                        # X-axis has negative values, use it for steering
                        steering_axis = analog_x_raw
                        axis_name = "X (has negative values)"
                        steering_axis_raw = steering_axis
                        steering_axis = self._apply_deadzone(steering_axis)
                        left = 1 if steering_axis < 0 else 0
                        right = 1 if steering_axis > 0 else 0
                    else:
                        # Use Y-axis with center-relative comparison
                        steering_axis = analog_y_raw
                        axis_name = "Y (rotated, offset)"
                        steering_axis_raw = steering_axis
                        # Use center-relative comparison for offset axis
                        left, right = self._get_steering_from_offset_axis(analog_y_raw, self._y_center)
                        steering_axis = analog_y_raw - (self._y_center if self._y_center else 0.057)  # For logging
                else:
                    # Normal orientation: use x-axis for horizontal steering
                    steering_axis = analog_x_raw
                    axis_name = "X (normal)"
                    steering_axis_raw = steering_axis
                    steering_axis = self._apply_deadzone(steering_axis)
                    left = 1 if steering_axis < 0 else 0
                    right = 1 if steering_axis > 0 else 0

                # Log steering info - more detailed when values pass deadzone
                if left or right:
                    # Steering command will be generated
                    center_info = f", center={self._y_center:.3f}" if self._y_center else ""
                    logger.info(
                        f"[STEERING ACTIVE] Minus JoyCon - "
                        f"X={analog_x_raw:.3f}, Y={analog_y_raw:.3f}{center_info}, "
                        f"Using {axis_name}={steering_axis_raw:.3f}, "
                        f"left={left}, right={right}, rotated={rotated}"
                    )
                elif abs(steering_axis_raw) > 0.01 or abs(analog_y_raw) > 0.01:
                    # Value detected but no steering command
                    center_info = f", center={self._y_center:.3f}" if self._y_center else ""
                    logger.debug(
                        f"[STEERING FILTERED] Minus JoyCon - "
                        f"X={analog_x_raw:.3f}, Y={analog_y_raw:.3f}{center_info}, "
                        f"Using {axis_name}={steering_axis_raw:.3f}, "
                        f"left={left}, right={right}"
                    )

        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing JoyCon status: {e}")
            return (0, 0, 0, 0, current_speed)

        return (forward, backward, left, right, speed)

