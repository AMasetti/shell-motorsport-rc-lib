import asyncio
import logging
import json
from bleak import BleakClient, BleakScanner
from Crypto.Cipher import AES
from pathlib import Path

logging.basicConfig(level=logging.INFO)

class ShellMotorsportCar:
    SERVICE_UUID = "fff0"
    WRITE_CHAR_UUID = "d44bc439-abfd-45a2-b575-925416129600"
    NOTIFY_CHAR_UUID = "d44bc439-abfd-45a2-b575-925416129601"
    AES_KEY = bytes.fromhex("34522a5b7a6e492c08090a9d8d2a23f8")
    CONTROL_PREFIX = b"CTL"
    SPEED_NORMAL = b"50"

    IDLE_MESSAGE = bytes.fromhex("e1055f54d880f49c2ce547267f930bf2")

    def __init__(self):
        self.client = None
        self.device = None
        self.vehicle_list_file = Path("vehicle_list.json")
        self.load_messages_from_file()

    def load_messages_from_file(self, filename="car_commands.json"):
        """Loads precomputed messages from a JSON file."""
        with open(filename, "r") as file:
            self.command_list = json.load(file)

    def save_messages_to_file(self, filename="car_commands.json"):
        """Saves precomputed messages to a JSON file."""
        with open(filename, "w") as file:
            json.dump(self.command_list, file)

    def precompute_messages(self):
        """Precomputes messages for various control states."""
        for forward in [0, 1]:
            for backward in [0, 1]:
                for left in [0, 1]:
                    for right in [0, 1]:
                        for turbo in [False, True]:
                            key = f"{forward}{backward}{left}{right}{turbo}"
                            self.command_list[key] = self._create_message(
                                forward, backward, left, right, turbo
                            )

    def save_vehicle_list(self, car_name: str, device_id: str):
        """Save car name and device_id to a JSON file."""
        vehicle_list = {}
        if self.vehicle_list_file.exists():
            with open(self.vehicle_list_file, "r") as file:
                vehicle_list = json.load(file)
        vehicle_list[car_name] = device_id
        with open(self.vehicle_list_file, "w") as file:
            json.dump(vehicle_list, file)
        logging.info(f"Saved car info: {car_name} -> {device_id}")

    def get_device_id(self, car_name: str) -> str:
        """Retrieve device_id from the JSON file given a car name."""
        if self.vehicle_list_file.exists():
            with open(self.vehicle_list_file, "r") as file:
                vehicle_list = json.load(file)
            return vehicle_list.get(car_name, None)
        return None

    async def find_and_name_car(self, new_name: str) -> BleakClient:
        """Scan for nearby devices, connect to the RC car, and assign a new name."""
        logging.info("Discovering nearby vehicles...")
        devices = await BleakScanner.discover()
        for device in devices:
            try:
                self.device = device
                logging.info(f"Found RC Car: {device.name} ({device.address})")
                self.save_vehicle_list(new_name, device.name)
                return device
            except Exception as e:
                logging.error("Error finding RC Car: %s", e)
                logging.info("RC Car not found. Make sure it is powered on and in range.")

        await asyncio.sleep(2)
        return await self.find_and_name_car(device.name, new_name)

    async def find_car(self, device_id: str) -> BleakClient:
        """Scan for nearby devices and connect to the RC car."""
        logging.info("Discovering nearby vehicles...")
        devices = await BleakScanner.discover()
        for device in devices:
            try:
                if device_id in device.name:  # Check for car name pattern
                    self.device = device
                    logging.info(f"Found RC Car: {device.name} ({device.address})")
                    return device
            except Exception as e:
                logging.error("Error finding RC Car: %s", e)
                logging.info("RC Car not found. Make sure it is powered on and in range.")

        await asyncio.sleep(2)
        return await self.find_car(device_id)

    async def connect(self, device_id: str):
        """Connect to the RC car."""
        if not self.device:
            await self.find_car(device_id)
        self.client = BleakClient(self.device.address)
        try:
            await self.client.connect()
            logging.info("Connected to RC car.")
        except Exception as e:
            logging.error("Failed to connect to RC car: %s", e)

    async def connect_to_any(self):
        """Connect to any available RC car."""
        if not self.device:
            await self.find_and_name_car("QCAR")
        self.client = BleakClient(self.device.address)
        try:
            await self.client.connect()
            logging.info("Connected to RC car.")
        except Exception as e:
            logging.error("Failed to connect to RC car %s", e)

    async def disconnect(self):
        """Disconnect from the RC car."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            logging.info("Disconnected from RC car.")

    def _encrypt_message(self, message: bytes) -> bytes:
        """Encrypt a message using AES encryption."""
        cipher = AES.new(self.AES_KEY, AES.MODE_ECB)
        return cipher.encrypt(message)

    def _create_message(self, forward: int = 0, backward: int = 0, left: int = 0, right: int = 0, drs: int = 0x50) -> bytes:
        """Create a control message to send to the car."""
        message = bytearray(16)
        message[0] = 0  # Unknown
        message[1:4] = self.CONTROL_PREFIX  # CTL
        message[4] = forward
        message[5] = backward
        message[6] = left
        message[7] = right
        message[8] = 0
        message[9] = 0x64 if drs else 0x50
        message = bytes(message)
        return self._encrypt_message(message)

    def retreive_precomputed_message(self, forward: int = 0, backward: int = 0, left: int = 0, right: int = 0, drs: int = 0x50) -> bytes:
        """Retrieve a precomputed message from the list."""
        key = f"{forward}{backward}{left}{right}{drs}"
        return self.command_list.get(key, self.IDLE_MESSAGE)

    async def move_command(self, message: bytes):
        """Send a control message to the car."""
        if not self.client or not self.client.is_connected:
            raise Exception("Not connected to the car.")
        await self.client.write_gatt_char(self.WRITE_CHAR_UUID, message)

    async def stop(self):
        """Command the car to stop."""
        if not self.client or not self.client.is_connected:
            raise Exception("Not connected to the car.")
        await self.client.write_gatt_char(self.WRITE_CHAR_UUID, self.IDLE_MESSAGE)
        logging.info("Car stopped.")
