"""Shell Motorsport RC Car control library."""
from abc import ABC, abstractmethod
import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from bleak import BLEDevice

# Handle both package and direct script execution
try:
    from .ble_client import BLEClient
    from .encryption import MessageEncryptor
    from .joycon_handler import JoyConHandler
    from .config import (
        AES_KEY,
        IDLE_MESSAGE,
        CONTROL_PREFIX,
        VEHICLE_LIST_FILE,
        CAR_COMMANDS_FILE,
        DEFAULT_SPEED,
    )
except ImportError:
    # Fallback for direct script execution
    from ble_client import BLEClient
    from encryption import MessageEncryptor
    from joycon_handler import JoyConHandler
    from config import (
        AES_KEY,
        IDLE_MESSAGE,
        CONTROL_PREFIX,
        VEHICLE_LIST_FILE,
        CAR_COMMANDS_FILE,
        DEFAULT_SPEED,
    )

# Configure logging
logger = logging.getLogger(__name__)


class Controller(ABC):
    """Abstract base class for RC car controllers."""

    @abstractmethod
    async def connect(self, device_id: str) -> None:
        """Connect to the RC car."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the RC car."""
        pass

    @abstractmethod
    async def move_command(self, message: bytes) -> None:
        """Send a control message to the car."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Command the car to stop."""
        pass


class ShellMotorsportCar(Controller):
    """
    Control Shell Motorsport RC cars via Bluetooth Low Energy (BLE).

    This class provides methods to connect to RC cars, send movement commands,
    and manage multiple vehicles. It supports both programmatic control and
    JoyCon controller input.

    Example:
        ```python
        import asyncio
        from shell_motorsport import ShellMotorsportCar

        async def main():
            car = ShellMotorsportCar()
            try:
                await car.connect("QCAR-0000044")
                await car.move_forward(speed=0x64)
                await asyncio.sleep(1)
                await car.stop()
            finally:
                await car.disconnect()

        asyncio.run(main())
        ```

    Example with context manager:
        ```python
        async def main():
            async with ShellMotorsportCar() as car:
                await car.connect("QCAR-0000044")
                await car.move_forward()
        ```
    """

    def __init__(
        self,
        vehicle_list_file: Optional[Path] = None,
        commands_file: Optional[Path] = None,
    ):
        """
        Initialize the ShellMotorsportCar instance.

        Args:
            vehicle_list_file: Path to vehicle list JSON file. If None, uses default.
            commands_file: Path to precomputed commands JSON file. If None, uses default.
        """
        self.ble_client = BLEClient()
        self.encryptor = MessageEncryptor(AES_KEY)
        self.joycon_handler = JoyConHandler()

        self.vehicle_list_file = vehicle_list_file or VEHICLE_LIST_FILE
        self.commands_file = commands_file or CAR_COMMANDS_FILE
        self.vehicle_list: Dict[str, str] = {}
        self.command_list: Dict[str, str] = {}

        self._load_vehicle_list()
        self._load_commands()

    def _load_vehicle_list(self) -> None:
        """Load vehicle list from JSON file."""
        try:
            if self.vehicle_list_file.exists():
                with open(self.vehicle_list_file, "r") as file:
                    self.vehicle_list = json.load(file)
                logger.debug(f"Loaded {len(self.vehicle_list)} vehicles from list")
            else:
                logger.info(
                    f"Vehicle list file not found: {self.vehicle_list_file}. "
                    "Creating empty list."
                )
                self.vehicle_list = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing vehicle list file: {e}")
            self.vehicle_list = {}
        except Exception as e:
            logger.error(f"Error loading vehicle list: {e}")
            self.vehicle_list = {}

    def _load_commands(self) -> None:
        """Load precomputed commands from JSON file."""
        try:
            if self.commands_file.exists():
                with open(self.commands_file, "r") as file:
                    self.command_list = json.load(file)
                logger.debug(f"Loaded {len(self.command_list)} precomputed commands")
            else:
                logger.warning(
                    f"Commands file not found: {self.commands_file}. "
                    "Precomputed commands will not be available."
                )
                self.command_list = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing commands file: {e}")
            self.command_list = {}
        except Exception as e:
            logger.error(f"Error loading commands: {e}")
            self.command_list = {}

    def _save_vehicle_list(self) -> None:
        """Save vehicle list to JSON file."""
        try:
            with open(self.vehicle_list_file, "w") as file:
                json.dump(self.vehicle_list, file, indent=2)
            logger.debug(f"Saved {len(self.vehicle_list)} vehicles to list")
        except Exception as e:
            logger.error(f"Error saving vehicle list: {e}")
            raise

    def _save_commands(self) -> None:
        """Save precomputed commands to JSON file."""
        try:
            with open(self.commands_file, "w") as file:
                json.dump(self.command_list, file, indent=2)
            logger.debug(f"Saved {len(self.command_list)} commands")
        except Exception as e:
            logger.error(f"Error saving commands: {e}")
            raise

    def list_vehicles(self) -> Dict[str, str]:
        """
        Get list of all registered vehicles.

        Returns:
            Dictionary mapping vehicle names to device IDs
        """
        return self.vehicle_list.copy()

    def get_device_id(self, car_name: str) -> Optional[str]:
        """
        Retrieve device ID for a given car name.

        Args:
            car_name: Name of the car

        Returns:
            Device ID if found, None otherwise
        """
        return self.vehicle_list.get(car_name)

    def is_connected(self) -> bool:
        """
        Check if currently connected to a car.

        Returns:
            True if connected, False otherwise
        """
        return self.ble_client.is_connected

    def get_connection_status(self) -> Dict[str, any]:
        """
        Get detailed connection status.

        Returns:
            Dictionary with connection status information
        """
        return {
            "connected": self.is_connected(),
            "device": self.ble_client.device.name if self.ble_client.device else None,
            "address": self.ble_client.device.address if self.ble_client.device else None,
        }

    def precompute_messages(self) -> None:
        """
        Precompute messages for all control state combinations.

        This generates encrypted messages for all combinations of forward,
        backward, left, right, and speed settings, saving them to the
        commands file for faster retrieval.
        """
        logger.info("Precomputing messages...")
        speed_values = [0x16, 0x32, 0x48, 0x64]

        for forward in [0, 1]:
            for backward in [0, 1]:
                for left in [0, 1]:
                    for right in [0, 1]:
                        for speed in speed_values:
                            key = f"{forward}{backward}{left}{right}{speed}"
                            message = self._create_message(
                                forward, backward, left, right, speed
                            )
                            self.command_list[key] = base64.b64encode(message).decode(
                                "utf-8"
                            )

        self._save_commands()
        logger.info(f"Precomputed {len(self.command_list)} messages")

    def _create_message(
        self,
        forward: int = 0,
        backward: int = 0,
        left: int = 0,
        right: int = 0,
        speed: int = DEFAULT_SPEED,
    ) -> bytes:
        """
        Create a control message for the car.

        Args:
            forward: Forward movement flag (0 or 1)
            backward: Backward movement flag (0 or 1)
            left: Left turn flag (0 or 1)
            right: Right turn flag (0 or 1)
            speed: Speed value (0x16-0x64)

        Returns:
            Encrypted message bytes (16 bytes)

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate inputs
        if forward not in [0, 1] or backward not in [0, 1]:
            raise ValueError("Forward and backward must be 0 or 1")
        if left not in [0, 1] or right not in [0, 1]:
            raise ValueError("Left and right must be 0 or 1")
        if not (0x00 <= speed <= 0xFF):
            raise ValueError("Speed must be between 0x00 and 0xFF")

        message = bytearray(16)
        message[0] = 0  # Unknown
        message[1:4] = CONTROL_PREFIX  # CTL
        message[4] = forward
        message[5] = backward
        message[6] = left
        message[7] = right
        message[8] = 0
        message[9] = speed
        # Remaining bytes are zeros

        return self.encryptor.encrypt(bytes(message))

    def retrieve_precomputed_message(
        self,
        forward: int = 0,
        backward: int = 0,
        left: int = 0,
        right: int = 0,
        speed: int = DEFAULT_SPEED,
    ) -> bytes:
        """
        Retrieve a precomputed message from the command list.

        Args:
            forward: Forward movement flag (0 or 1)
            backward: Backward movement flag (0 or 1)
            left: Left turn flag (0 or 1)
            right: Right turn flag (0 or 1)
            speed: Speed value

        Returns:
            Encrypted message bytes, or IDLE_MESSAGE if not found
        """
        key = f"{forward}{backward}{left}{right}{speed}"
        encoded_message = self.command_list.get(key)

        if encoded_message:
            try:
                message = base64.b64decode(encoded_message)
                logger.debug(f"[MESSAGE DEBUG] Retrieved precomputed message for key: {key}")
                return message
            except Exception as e:
                logger.warning(f"Error decoding precomputed message: {e}")
                return IDLE_MESSAGE

        # Fallback to creating message on the fly
        logger.debug(f"Precomputed message not found for key {key}, creating new one")
        message = self._create_message(forward, backward, left, right, speed)
        logger.debug(f"[MESSAGE DEBUG] Created new message for key: {key}")
        return message

    async def find_and_name_car(self, new_name: str) -> BLEDevice:
        """
        Scan for nearby RC cars and assign a name to the first one found.

        Args:
            new_name: Name to assign to the found car

        Returns:
            Found BLEDevice

        Raises:
            TimeoutError: If no car is found after max retries
        """
        logger.info(f"Discovering and naming car: {new_name}")
        device = await self.ble_client.scan_for_device(device_name_pattern="QCAR")

        if device:
            device_id = device.name
            self.vehicle_list[new_name] = device_id
            self._save_vehicle_list()
            logger.info(f"Saved car: {new_name} -> {device_id}")
            return device
        else:
            raise TimeoutError("Could not find any RC car")

    async def find_car(self, device_id: str) -> BLEDevice:
        """
        Scan for a specific RC car by device ID.

        Args:
            device_id: Device ID to find (e.g., "QCAR-0000044")

        Returns:
            Found BLEDevice

        Raises:
            TimeoutError: If car is not found after max retries
        """
        logger.info(f"Scanning for car: {device_id}")
        device = await self.ble_client.scan_for_device(device_id=device_id)

        if device:
            return device
        else:
            raise TimeoutError(f"Could not find car: {device_id}")

    async def connect(self, device_id: str) -> None:
        """
        Connect to an RC car by device ID.

        Args:
            device_id: Device ID to connect to (e.g., "QCAR-0000044")

        Raises:
            ConnectionError: If connection fails
            TimeoutError: If car is not found
        """
        if self.is_connected():
            logger.warning("Already connected. Disconnecting first...")
            await self.disconnect()

        device = await self.find_car(device_id)
        await self.ble_client.connect(device)
        logger.info(f"Connected to {device_id}")

    async def connect_by_name(self, car_name: str) -> None:
        """
        Connect to an RC car by registered name.

        Args:
            car_name: Registered name of the car

        Raises:
            ValueError: If car name is not registered
            ConnectionError: If connection fails
            TimeoutError: If car is not found
        """
        device_id = self.get_device_id(car_name)
        if not device_id:
            raise ValueError(
                f"Car '{car_name}' not found in vehicle list. "
                "Use find_and_name_car() first."
            )
        await self.connect(device_id)

    async def disconnect(self) -> None:
        """Disconnect from the current car."""
        await self.ble_client.disconnect()

    async def move_command(self, message: bytes) -> None:
        """
        Send a control message to the car.

        Args:
            message: Encrypted message bytes (must be 16 bytes)

        Raises:
            ConnectionError: If not connected
            ValueError: If message length is invalid
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to the car")

        if len(message) != 16:
            raise ValueError(f"Message must be exactly 16 bytes, got {len(message)}")

        await self.ble_client.write_characteristic(message)

    async def stop(self) -> None:
        """
        Command the car to stop.

        Raises:
            ConnectionError: If not connected
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to the car")

        await self.ble_client.write_characteristic(IDLE_MESSAGE)

    # Convenience methods for common movements
    async def move_forward(
        self, speed: int = DEFAULT_SPEED, duration: Optional[float] = None
    ) -> None:
        """
        Move the car forward.

        Args:
            speed: Speed value (default: 0x50)
            duration: Duration in seconds. If None, continues until stop() is called.
        """
        message = self.retrieve_precomputed_message(forward=1, speed=speed)
        if duration:
            end_time = asyncio.get_event_loop().time() + duration
            while asyncio.get_event_loop().time() < end_time:
                await self.move_command(message)
                await asyncio.sleep(0.01)
        else:
            await self.move_command(message)

    async def move_backward(
        self, speed: int = DEFAULT_SPEED, duration: Optional[float] = None
    ) -> None:
        """
        Move the car backward.

        Args:
            speed: Speed value (default: 0x50)
            duration: Duration in seconds. If None, continues until stop() is called.
        """
        message = self.retrieve_precomputed_message(backward=1, speed=speed)
        if duration:
            end_time = asyncio.get_event_loop().time() + duration
            while asyncio.get_event_loop().time() < end_time:
                await self.move_command(message)
                await asyncio.sleep(0.01)
        else:
            await self.move_command(message)

    def get_joycon_command(
        self, status: Dict, device_type: str = "Plus", current_speed: int = DEFAULT_SPEED, rotated: bool = False
    ) -> bytes:
        """
        Get a control message from JoyCon controller input.

        Args:
            status: JoyCon status dictionary from pyjoycon
            device_type: "Plus" or "Minus"
            current_speed: Current speed setting (used if no speed button pressed)
            rotated: Whether the JoyCon is rotated (single controller mode).
                    When True, uses y-axis as horizontal steering axis.

        Returns:
            Encrypted control message bytes
        """
        try:
            forward, backward, left, right, speed = self.joycon_handler.parse_joycon_status(
                status, device_type, current_speed, rotated
            )

            # Log command generation for debugging
            if forward or backward or left or right:
                logger.info(
                    f"[COMMAND DEBUG] Generating command: "
                    f"forward={forward}, backward={backward}, left={left}, right={right}, speed=0x{speed:02x}"
                )

            message = self.retrieve_precomputed_message(
                forward=forward, backward=backward, left=left, right=right, speed=speed
            )

            # Verify message was retrieved/created correctly
            if len(message) != 16:
                logger.error(f"[ERROR] Invalid message length: {len(message)} bytes (expected 16)")

            return message
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate JoyCon command: {e}", exc_info=True)
            # Return idle message on error
            return IDLE_MESSAGE

    # Async context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures disconnection."""
        await self.disconnect()
