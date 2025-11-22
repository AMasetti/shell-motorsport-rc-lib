"""Tests for JoyCon handler module."""
import pytest
from shell_motorsport.joycon_handler import JoyConHandler
from shell_motorsport.config import DEFAULT_SPEED, DEFAULT_SPEED_PROFILES


def test_joycon_handler_init():
    """Test JoyCon handler initialization."""
    handler = JoyConHandler()
    assert handler.default_speed == DEFAULT_SPEED


def test_apply_deadzone():
    """Test deadzone application."""
    handler = JoyConHandler()
    assert handler._apply_deadzone(0.05) == 0.0  # Below deadzone
    assert handler._apply_deadzone(0.2) == 0.2  # Above deadzone
    assert handler._apply_deadzone(-0.05) == 0.0  # Below deadzone (negative)
    assert handler._apply_deadzone(-0.2) == -0.2  # Above deadzone (negative)


def test_get_speed_from_buttons_plus():
    """Test speed button detection for Plus JoyCon."""
    handler = JoyConHandler()
    status = {
        "buttons": {
            "right": {
                "a": True,
                "b": False,
                "y": False,
                "x": False,
            }
        }
    }
    speed = handler._get_speed_from_buttons(status, "Plus")
    assert speed == DEFAULT_SPEED_PROFILES["low"]

    status["buttons"]["right"]["a"] = False
    status["buttons"]["right"]["b"] = True
    speed = handler._get_speed_from_buttons(status, "Plus")
    assert speed == DEFAULT_SPEED_PROFILES["medium"]

    status["buttons"]["right"]["b"] = False
    status["buttons"]["right"]["y"] = True
    speed = handler._get_speed_from_buttons(status, "Plus")
    assert speed == DEFAULT_SPEED_PROFILES["high"]

    status["buttons"]["right"]["y"] = False
    status["buttons"]["right"]["x"] = True
    speed = handler._get_speed_from_buttons(status, "Plus")
    assert speed == DEFAULT_SPEED_PROFILES["max"]


def test_get_speed_from_buttons_minus():
    """Test speed button detection for Minus JoyCon."""
    handler = JoyConHandler()
    status = {
        "buttons": {
            "left": {
                "left": True,
                "down": False,
                "right": False,
                "up": False,
            }
        }
    }
    speed = handler._get_speed_from_buttons(status, "Minus")
    assert speed == DEFAULT_SPEED_PROFILES["low"]

    status["buttons"]["left"]["left"] = False
    status["buttons"]["left"]["down"] = True
    speed = handler._get_speed_from_buttons(status, "Minus")
    assert speed == DEFAULT_SPEED_PROFILES["medium"]

    status["buttons"]["left"]["down"] = False
    status["buttons"]["left"]["right"] = True
    speed = handler._get_speed_from_buttons(status, "Minus")
    assert speed == DEFAULT_SPEED_PROFILES["high"]

    status["buttons"]["left"]["right"] = False
    status["buttons"]["left"]["up"] = True
    speed = handler._get_speed_from_buttons(status, "Minus")
    assert speed == DEFAULT_SPEED_PROFILES["max"]


def test_parse_joycon_status_plus():
    """Test parsing Plus JoyCon status."""
    handler = JoyConHandler()
    status = {
        "buttons": {
            "right": {
                "sr": True,
                "sl": False,
                "a": False,
                "b": False,
                "y": False,
                "x": False,
            }
        },
        "analogs": {"right": {"y": 0.5}},
    }
    forward, backward, left, right, speed = handler.parse_joycon_status(status, "Plus")
    assert forward == 1
    assert backward == 0
    assert right == 1  # analog_y > 0
    assert left == 0


def test_parse_joycon_status_minus():
    """Test parsing Minus JoyCon status."""
    handler = JoyConHandler()
    status = {
        "buttons": {
            "left": {
                "sr": True,
                "sl": False,
                "left": False,
                "down": False,
                "right": False,
                "up": False,
            }
        },
        "analogs": {"left": {"y": -0.5}},
    }
    forward, backward, left, right, speed = handler.parse_joycon_status(status, "Minus")
    assert forward == 1
    assert backward == 0
    assert left == 1  # analog_y < 0
    assert right == 0


def test_parse_joycon_status_deadzone():
    """Test deadzone handling in JoyCon parsing."""
    handler = JoyConHandler()
    status = {
        "buttons": {"right": {"sr": False, "sl": False}},
        "analogs": {"right": {"y": 0.05}},  # Below deadzone
    }
    forward, backward, left, right, speed = handler.parse_joycon_status(status, "Plus")
    assert left == 0
    assert right == 0


def test_parse_joycon_status_error_handling():
    """Test error handling in JoyCon parsing."""
    handler = JoyConHandler()
    # Missing keys should not crash
    status = {}
    forward, backward, left, right, speed = handler.parse_joycon_status(status, "Plus")
    assert forward == 0
    assert backward == 0
    assert left == 0
    assert right == 0

