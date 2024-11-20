import asyncio
from bleak import BleakClient, BleakScanner
from Crypto.Cipher import AES

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

    async def find_car(self, device_id):
        """Scan for nearby devices and connect to the RC car."""
        print("Discovering nearby vehicles...")
        devices = await BleakScanner.discover()
        for device in devices:
            try:
                if device_id in device.name:  # Check for car name pattern
                    self.device = device
                    print(f"'Found RC Car: {device.name} ({device.address})")
                    return device
            except Exception as e:
                # raise Exception("RC Car not found. Make sure it is powered on and in range.")
                print("RC Car not found. Make sure it is powered on and in range.")

        await asyncio.sleep(2)
        return self.find_car()


    async def connect(self, device_id):
        """Connect to the RC car."""
        if not self.device:
            await self.find_car(device_id)
        self.client = BleakClient(self.device.address)
        await self.client.connect()
        print("Connected to RC car.")

    async def disconnect(self):
        """Disconnect from the RC car."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("Disconnected from RC car.")

    def _encrypt_message(self, message: bytes) -> bytes:
        """Encrypt a message using AES encryption."""
        cipher = AES.new(self.AES_KEY, AES.MODE_ECB)
        return cipher.encrypt(message)

    def _create_message(self, forward=0, backward=0, left=0, right=0, speed=0x50) -> bytes:
        """Create a control message to send to the car."""
        message = bytearray(16)
        message[0] = 0  # Unknown
        message[1:4] = self.CONTROL_PREFIX  # CTL
        message[4] = forward
        message[5] = backward
        message[6] = left
        message[7] = right
        message[8] = 0
        message[9] = 0x50
        message = bytes(message)
        print("Mensaje en claro (16 bytes):")
        print(" ".join(f"{byte:02x}" for byte in message))
        return self._encrypt_message(message)


    async def move_forward(self, duration=2):
        """
        Command the car to move forward and periodically send control packets.

        Args:
            duration (int): Duration in seconds to move forward (default is 2).
        """
        if not self.client or not self.client.is_connected:
            raise Exception("Not connected to the car.")

        message = self._create_message(forward=1, right=1)
        end_time = asyncio.get_event_loop().time() + duration  # Calculate end time

        try:
            print("Car moving forward...")
            while asyncio.get_event_loop().time() < end_time:
                await self.client.write_gatt_char(self.WRITE_CHAR_UUID, message)
                # await asyncio.sleep(0.01)  # Wait 10 milliseconds
        finally:
            await self.stop()  # Ensure the car stops when the loop exits


    async def stop(self):
        """Command the car to stop."""
        if not self.client or not self.client.is_connected:
            raise Exception("Not connected to the car.")
        await self.client.write_gatt_char(self.WRITE_CHAR_UUID, self.IDLE_MESSAGE)
        print("Car stopped.")
