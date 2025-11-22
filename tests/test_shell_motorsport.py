"""Tests for Shell Motorsport RC Car library."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock, mock_open
from pathlib import Path
import json

from shell_motorsport import ShellMotorsportCar


@pytest.fixture
def car():
    """Create a ShellMotorsportCar instance for testing."""
    with patch("shell_motorsport.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data='{"TEST_CAR": "QCAR-0000001"}')):
            return ShellMotorsportCar()


@pytest.fixture
def mock_ble_device():
    """Create a mock BLE device."""
    device = MagicMock()
    device.name = "TEST_CAR"
    device.address = "00:11:22:33:44:55"
    return device


@pytest.mark.asyncio
@patch("shell_motorsport.BLEClient")
async def test_find_and_name_car(mock_ble_client_class, car, mock_ble_device):
    """Test finding and naming a car."""
    mock_ble_client = MagicMock()
    mock_ble_client.scan_for_device = AsyncMock(return_value=mock_ble_device)
    mock_ble_client_class.return_value = mock_ble_client
    car.ble_client = mock_ble_client

    with patch("builtins.open", mock_open()) as mock_file:
        device = await car.find_and_name_car("TEST_CAR")
        assert device is not None
        assert device.name == "TEST_CAR"
        assert "TEST_CAR" in car.vehicle_list


@pytest.mark.asyncio
@patch("shell_motorsport.BLEClient")
async def test_connect(mock_ble_client_class, car, mock_ble_device):
    """Test connecting to a car."""
    mock_ble_client = MagicMock()
    mock_ble_client.scan_for_device = AsyncMock(return_value=mock_ble_device)
    mock_ble_client.connect = AsyncMock()
    mock_ble_client.is_connected = True
    mock_ble_client.device = mock_ble_device
    mock_ble_client_class.return_value = mock_ble_client
    car.ble_client = mock_ble_client

    await car.connect("TEST_CAR")
    assert car.is_connected()


@pytest.mark.asyncio
@patch("shell_motorsport.BLEClient")
async def test_connect_by_name(mock_ble_client_class, car, mock_ble_device):
    """Test connecting to a car by name."""
    car.vehicle_list = {"TEST_CAR": "QCAR-0000001"}
    mock_ble_client = MagicMock()
    mock_ble_client.scan_for_device = AsyncMock(return_value=mock_ble_device)
    mock_ble_client.connect = AsyncMock()
    mock_ble_client.is_connected = True
    mock_ble_client.device = mock_ble_device
    mock_ble_client_class.return_value = mock_ble_client
    car.ble_client = mock_ble_client

    await car.connect_by_name("TEST_CAR")
    assert car.is_connected()


@pytest.mark.asyncio
@patch("shell_motorsport.BLEClient")
async def test_connect_by_name_not_found(car):
    """Test connecting by name when car is not registered."""
    car.vehicle_list = {}
    with pytest.raises(ValueError, match="not found in vehicle list"):
        await car.connect_by_name("NONEXISTENT_CAR")


@pytest.mark.asyncio
@patch("shell_motorsport.BLEClient")
async def test_disconnect(mock_ble_client_class, car):
    """Test disconnecting from a car."""
    mock_ble_client = MagicMock()
    mock_ble_client.disconnect = AsyncMock()
    mock_ble_client.is_connected = True
    mock_ble_client_class.return_value = mock_ble_client
    car.ble_client = mock_ble_client

    await car.disconnect()
    mock_ble_client.disconnect.assert_called_once()


def test_precompute_messages(car):
    """Test precomputing messages."""
    car.precompute_messages()
    assert len(car.command_list) > 0
    # Should have messages for all combinations
    assert len(car.command_list) == 2 * 2 * 2 * 2 * 4  # forward*backward*left*right*speeds


def test_retrieve_precomputed_message(car):
    """Test retrieving a precomputed message."""
    car.precompute_messages()
    message = car.retrieve_precomputed_message(forward=1)
    assert message is not None
    assert len(message) == 16


def test_retrieve_precomputed_message_not_found(car):
    """Test retrieving a message that doesn't exist (should create on the fly)."""
    car.command_list = {}
    message = car.retrieve_precomputed_message(forward=1)
    assert message is not None
    assert len(message) == 16


@pytest.mark.asyncio
@patch("shell_motorsport.BLEClient")
async def test_move_command(mock_ble_client_class, car):
    """Test sending a move command."""
    mock_ble_client = MagicMock()
    mock_ble_client.write_characteristic = AsyncMock()
    mock_ble_client.is_connected = True
    mock_ble_client_class.return_value = mock_ble_client
    car.ble_client = mock_ble_client

    message = car.retrieve_precomputed_message(forward=1)
    await car.move_command(message)
    mock_ble_client.write_characteristic.assert_called_once_with(message)


@pytest.mark.asyncio
@patch("shell_motorsport.BLEClient")
async def test_move_command_not_connected(car):
    """Test move command when not connected."""
    mock_ble_client = MagicMock()
    mock_ble_client.is_connected = False
    car.ble_client = mock_ble_client

    message = car.retrieve_precomputed_message(forward=1)
    with pytest.raises(ConnectionError, match="Not connected"):
        await car.move_command(message)


@pytest.mark.asyncio
@patch("shell_motorsport.BLEClient")
async def test_stop(mock_ble_client_class, car):
    """Test stopping the car."""
    mock_ble_client = MagicMock()
    mock_ble_client.write_characteristic = AsyncMock()
    mock_ble_client.is_connected = True
    mock_ble_client_class.return_value = mock_ble_client
    car.ble_client = mock_ble_client

    await car.stop()
    from shell_motorsport.config import IDLE_MESSAGE
    mock_ble_client.write_characteristic.assert_called_once_with(IDLE_MESSAGE)


def test_list_vehicles(car):
    """Test listing vehicles."""
    car.vehicle_list = {"CAR1": "QCAR-0000001", "CAR2": "QCAR-0000002"}
    vehicles = car.list_vehicles()
    assert vehicles == {"CAR1": "QCAR-0000001", "CAR2": "QCAR-0000002"}


def test_get_device_id(car):
    """Test getting device ID by name."""
    car.vehicle_list = {"TEST_CAR": "QCAR-0000001"}
    device_id = car.get_device_id("TEST_CAR")
    assert device_id == "QCAR-0000001"


def test_get_device_id_not_found(car):
    """Test getting device ID when car is not found."""
    car.vehicle_list = {}
    device_id = car.get_device_id("NONEXISTENT")
    assert device_id is None


def test_is_connected(car):
    """Test checking connection status."""
    mock_ble_client = MagicMock()
    mock_ble_client.is_connected = True
    car.ble_client = mock_ble_client
    assert car.is_connected() is True

    mock_ble_client.is_connected = False
    assert car.is_connected() is False


def test_get_connection_status(car):
    """Test getting connection status."""
    mock_ble_device = MagicMock()
    mock_ble_device.name = "TEST_CAR"
    mock_ble_device.address = "00:11:22:33:44:55"

    mock_ble_client = MagicMock()
    mock_ble_client.is_connected = True
    mock_ble_client.device = mock_ble_device
    car.ble_client = mock_ble_client

    status = car.get_connection_status()
    assert status["connected"] is True
    assert status["device"] == "TEST_CAR"
    assert status["address"] == "00:11:22:33:44:55"


def test_get_joycon_command(car):
    """Test getting JoyCon command."""
    status = {
        "buttons": {
            "right": {"sr": True, "sl": False, "a": False, "b": False, "y": False, "x": False}
        },
        "analogs": {"right": {"y": 0.5}},
    }
    message = car.get_joycon_command(status, "Plus")
    assert message is not None
    assert len(message) == 16


def test_create_message_validation(car):
    """Test message creation with invalid parameters."""
    with pytest.raises(ValueError):
        car._create_message(forward=2)  # Invalid value

    with pytest.raises(ValueError):
        car._create_message(speed=0x100)  # Invalid speed


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager."""
    with patch("shell_motorsport.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data='{}')):
            async with ShellMotorsportCar() as car:
                assert car is not None
                # Disconnect should be called automatically


def test_move_forward_sync(car):
    """Test move_forward convenience method."""
    # This tests the method exists and can be called
    # Actual async execution would require more complex mocking
    assert hasattr(car, "move_forward")
    assert hasattr(car, "move_backward")
