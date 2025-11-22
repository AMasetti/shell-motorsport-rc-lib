"""BLE client module for RC car communication."""
import asyncio
import logging
from typing import Optional
from bleak import BleakClient, BleakScanner, BLEDevice

# Handle both package and direct script execution
try:
    from .config import (
        SERVICE_UUID,
        WRITE_CHAR_UUID,
        SCAN_TIMEOUT,
        CONNECTION_TIMEOUT,
        MAX_SCAN_RETRIES,
        SCAN_RETRY_DELAY,
    )
except ImportError:
    # Fallback for direct script execution
    from config import (
        SERVICE_UUID,
        WRITE_CHAR_UUID,
        SCAN_TIMEOUT,
        CONNECTION_TIMEOUT,
        MAX_SCAN_RETRIES,
        SCAN_RETRY_DELAY,
    )

logger = logging.getLogger(__name__)


class BLEClient:
    """Handles BLE communication with RC cars."""

    def __init__(self):
        """Initialize the BLE client."""
        self.client: Optional[BleakClient] = None
        self.device: Optional[BLEDevice] = None
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to a device."""
        return self._is_connected and self.client is not None and self.client.is_connected

    async def scan_for_device(
        self, device_id: Optional[str] = None, device_name_pattern: str = "QCAR"
    ) -> Optional[BLEDevice]:
        """
        Scan for BLE devices matching the criteria.

        Args:
            device_id: Specific device ID to find (e.g., "QCAR-0000044")
            device_name_pattern: Pattern to match in device name (default: "QCAR")

        Returns:
            Found BLEDevice or None if not found

        Raises:
            TimeoutError: If scan times out after max retries
        """
        for attempt in range(MAX_SCAN_RETRIES):
            try:
                logger.info(f"Scanning for devices (attempt {attempt + 1}/{MAX_SCAN_RETRIES})...")
                devices = await asyncio.wait_for(
                    BleakScanner.discover(), timeout=SCAN_TIMEOUT
                )

                for device in devices:
                    try:
                        device_name = device.name or ""
                        if device_id:
                            if device_id in device_name:
                                logger.info(
                                    f"Found target device: {device_name} ({device.address})"
                                )
                                return device
                        elif device_name_pattern in device_name:
                            logger.info(
                                f"Found matching device: {device_name} ({device.address})"
                            )
                            return device
                    except Exception as e:
                        logger.debug(f"Error checking device {device}: {e}")
                        continue

                if attempt < MAX_SCAN_RETRIES - 1:
                    logger.warning(
                        f"Device not found. Retrying in {SCAN_RETRY_DELAY} seconds..."
                    )
                    await asyncio.sleep(SCAN_RETRY_DELAY)
                else:
                    logger.error(
                        f"Device not found after {MAX_SCAN_RETRIES} attempts. "
                        "Make sure the car is powered on and in range."
                    )
                    raise TimeoutError(
                        f"Could not find device after {MAX_SCAN_RETRIES} scan attempts"
                    )

            except asyncio.TimeoutError:
                logger.warning(f"Scan timeout (attempt {attempt + 1}/{MAX_SCAN_RETRIES})")
                if attempt < MAX_SCAN_RETRIES - 1:
                    await asyncio.sleep(SCAN_RETRY_DELAY)
                else:
                    raise TimeoutError("BLE scan timed out")

        return None

    async def connect(self, device: BLEDevice) -> None:
        """
        Connect to a BLE device.

        Args:
            device: BLEDevice to connect to

        Raises:
            ConnectionError: If connection fails
        """
        if self.is_connected:
            logger.warning("Already connected. Disconnecting first...")
            await self.disconnect()

        self.device = device
        self.client = BleakClient(device.address)

        try:
            logger.info(f"Connecting to {device.name} ({device.address})...")
            await asyncio.wait_for(
                self.client.connect(), timeout=CONNECTION_TIMEOUT
            )
            self._is_connected = True
            logger.info("Successfully connected to RC car.")
        except asyncio.TimeoutError:
            self._is_connected = False
            logger.error("Connection timeout")
            raise ConnectionError("Failed to connect: timeout")
        except Exception as e:
            self._is_connected = False
            logger.error(f"Failed to connect: {e}")
            raise ConnectionError(f"Failed to connect: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the current device."""
        if self.client and self.is_connected:
            try:
                await self.client.disconnect()
                logger.info("Disconnected from RC car.")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._is_connected = False
                self.client = None
                self.device = None

    async def write_characteristic(self, data: bytes) -> None:
        """
        Write data to the write characteristic.

        Args:
            data: Data bytes to write (must be 16 bytes)

        Raises:
            ConnectionError: If not connected
            ValueError: If data length is invalid
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to the car")

        if len(data) != 16:
            raise ValueError(f"Data must be exactly 16 bytes, got {len(data)}")

        try:
            await self.client.write_gatt_char(WRITE_CHAR_UUID, data)
        except Exception as e:
            logger.error(f"Failed to write characteristic: {e}")
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures disconnection."""
        await self.disconnect()

