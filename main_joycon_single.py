"""Example script for controlling a single RC car with Plus JoyCon controller."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to allow imports when running as script
sys.path.insert(0, str(Path(__file__).parent))

from shell_motorsport import ShellMotorsportCar
from pyjoycon import JoyCon, get_R_id

car_name = "AMASETTI_F1_75"

# Initialize Plus JoyCon (right controller)
joycon_plus = JoyCon(*get_R_id())


async def main() -> None:
    """Main function demonstrating single car control with Plus JoyCon."""
    car = ShellMotorsportCar()

    try:
        # Connect to car by name (will find and name if not registered)
        if car_name not in car.vehicle_list:
            await car.find_and_name_car(car_name)
        await car.connect_by_name(car_name)

        print(f"Connected to {car_name}. Use JoyCon Plus to control the car.")
        print("Controls:")
        print("  SR: Forward")
        print("  SL: Backward")
        print("  Right Stick Y: Turn left/right")
        print("  A: Low speed")
        print("  B: Medium speed")
        print("  Y: High speed")
        print("  X: Max speed")
        print("\nPress Ctrl+C to stop...")

        # Current speed (will be updated by JoyCon buttons)
        current_speed = 0x50

        async def update_status():
            """Generator that yields JoyCon status updates."""
            while True:
                status = joycon_plus.get_status()
                yield status
                await asyncio.sleep(0.005)  # 5ms for better responsiveness

        async for status in update_status():
            # Get command from JoyCon
            command = car.get_joycon_command(status, "Plus", current_speed)

            # Update speed based on button presses
            _, _, _, _, current_speed = car.joycon_handler.parse_joycon_status(
                status, "Plus", current_speed
            )

            # Send command to car
            await car.move_command(command)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await car.stop()
        await car.disconnect()
        print("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())

