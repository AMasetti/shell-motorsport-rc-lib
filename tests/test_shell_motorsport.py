import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from shell_motorsport import ShellMotorsportCar

@pytest.fixture
def car():
    return ShellMotorsportCar()

@pytest.mark.asyncio
@patch('shell_motorsport.BleakClient')
@patch('shell_motorsport.BleakScanner.discover')
async def test_find_and_name_car(mock_discover, mock_bleak_client, car):
    mock_device = MagicMock()
    mock_device.name = "TEST_CAR"
    mock_discover.return_value = [mock_device]
    mock_bleak_client.return_value.connect = AsyncMock()
    mock_bleak_client.return_value.is_connected = True
    device = await car.find_and_name_car("TEST_CAR")
    assert device is not None
    assert "TEST_CAR" in car.get_device_id("TEST_CAR")

@pytest.mark.asyncio
@patch('shell_motorsport.BleakClient')
@patch('shell_motorsport.BleakScanner.discover')
async def test_connect(mock_discover, mock_bleak_client, car):
    mock_device = MagicMock()
    mock_device.name = "TEST_CAR"
    mock_discover.return_value = [mock_device]
    mock_bleak_client.return_value.connect = AsyncMock()
    mock_bleak_client.return_value.is_connected = True
    await car.find_and_name_car("TEST_CAR")
    await car.connect("TEST_CAR")
    assert car.client.is_connected

@pytest.mark.asyncio
@patch('shell_motorsport.BleakClient')
@patch('shell_motorsport.BleakScanner.discover')
async def test_disconnect(mock_discover, mock_bleak_client, car):
    mock_device = MagicMock()
    mock_device.name = "TEST_CAR"
    mock_discover.return_value = [mock_device]
    mock_bleak_client.return_value.connect = AsyncMock()
    mock_bleak_client.return_value.is_connected = True
    mock_bleak_client.return_value.disconnect = AsyncMock()
    await car.find_and_name_car("TEST_CAR")
    await car.connect("TEST_CAR")
    mock_bleak_client.return_value.is_connected = False
    await car.disconnect()
    assert not car.client.is_connected

def test_precompute_messages(car):
    car.precompute_messages()
    assert len(car.command_list) > 0

def test_retrieve_precomputed_message(car):
    car.precompute_messages()
    message = car.retreive_precomputed_message(forward=1)
    assert message is not None

@pytest.mark.asyncio
@patch('shell_motorsport.BleakClient')
@patch('shell_motorsport.BleakScanner.discover')
async def test_move_command(mock_discover, mock_bleak_client, car):
    mock_device = MagicMock()
    mock_device.name = "TEST_CAR"
    mock_discover.return_value = [mock_device]
    mock_bleak_client.return_value.connect = AsyncMock()
    mock_bleak_client.return_value.is_connected = True
    mock_bleak_client.return_value.write_gatt_char = AsyncMock()
    mock_bleak_client.return_value.disconnect = AsyncMock()
    await car.find_and_name_car("TEST_CAR")
    await car.connect("TEST_CAR")
    message = car.retreive_precomputed_message(forward=1)
    await car.move_command(message)
    await car.stop()
    await car.disconnect()
