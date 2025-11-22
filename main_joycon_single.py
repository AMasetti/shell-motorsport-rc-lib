"""Example script for controlling a single RC car with Plus JoyCon controller."""
import asyncio
import sys
import logging
from pathlib import Path

# Configure logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        print("Controls (single rotated JoyCon):")
        print("  SR: Forward")
        print("  SL: Backward")
        print("  Right Stick (horizontal): Turn left/right")
        print("    - Tilt stick left = Turn left")
        print("    - Tilt stick right = Turn right")
        print("  A: Low speed")
        print("  B: Medium speed")
        print("  Y: High speed")
        print("  X: Max speed")
        print("\nPress Ctrl+C to stop...")

        # Current speed (will be updated by JoyCon buttons)
        current_speed = 0x50

        async def update_status():
            """Generator that yields JoyCon status updates."""
            first_status_logged = False
            while True:
                status = joycon_plus.get_status()

                # Log the structure of the status dict once for debugging
                if not first_status_logged:
                    print(f"[DEBUG] JoyCon status structure keys: {list(status.keys())}")
                    print(f"[DEBUG] Full status structure (first 500 chars): {str(status)[:500]}")
                    if "analogs" in status:
                        print(f"[DEBUG] Analogs structure: {status['analogs']}")
                    if "analog-sticks" in status:
                        print(f"[DEBUG] Analog-sticks structure: {status['analog-sticks']}")
                    if "stick" in status:
                        print(f"[DEBUG] Stick structure: {status['stick']}")
                    if "buttons" in status:
                        print(f"[DEBUG] Buttons structure: {status['buttons']}")
                    first_status_logged = True

                yield status
                await asyncio.sleep(0.005)  # 5ms for better responsiveness

        async for status in update_status():
            # Debug: Try multiple possible structures for analog values
            analog_x = 0.0
            analog_y = 0.0

            # Try different possible structures
            if "analogs" in status and "right" in status["analogs"]:
                analogs_right = status["analogs"]["right"]
                analog_x = analogs_right.get("x", analogs_right.get("stick_x", analogs_right.get("horizontal", 0.0)))
                analog_y = analogs_right.get("y", analogs_right.get("stick_y", analogs_right.get("vertical", 0.0)))
            elif "analog-sticks" in status and "right" in status["analog-sticks"]:
                stick_right = status["analog-sticks"]["right"]
                analog_x = stick_right.get("x", stick_right.get("horizontal", stick_right.get("stick_x", 0.0)))
                analog_y = stick_right.get("y", stick_right.get("vertical", stick_right.get("stick_y", 0.0)))
            elif "stick" in status and "right" in status["stick"]:
                stick_right = status["stick"]["right"]
                analog_x = stick_right.get("x", stick_right.get("horizontal", 0.0))
                analog_y = stick_right.get("y", stick_right.get("vertical", 0.0))
            elif "right_stick_x" in status or "right_stick_y" in status:
                analog_x = status.get("right_stick_x", 0.0)
                analog_y = status.get("right_stick_y", 0.0)

            # Handle raw integer values (pyjoycon might return integers that need normalization)
            if isinstance(analog_x, int):
                # Normalize from -32768 to 32767 range to -1.0 to 1.0
                analog_x = analog_x / 32768.0 if analog_x != 0 else 0.0
            if isinstance(analog_y, int):
                # Normalize from -32768 to 32767 range to -1.0 to 1.0
                analog_y = analog_y / 32768.0 if analog_y != 0 else 0.0

            # Log analog values periodically (every 100ms to avoid spam)
            import time
            if not hasattr(update_status, "_last_log_time"):
                update_status._last_log_time = 0
                update_status._min_y = float('inf')
                update_status._max_y = float('-inf')
            current_time = time.time()
            if current_time - update_status._last_log_time > 0.1:  # Log every 100ms
                # Track Y-axis range
                if analog_y != 0.0:
                    update_status._min_y = min(update_status._min_y, analog_y)
                    update_status._max_y = max(update_status._max_y, analog_y)
                print(f"[DEBUG] Analog X: {analog_x:.3f}, Analog Y: {analog_y:.3f} (Y range: {update_status._min_y:.3f} to {update_status._max_y:.3f})")
                # Also log raw values if they're different
                raw_analogs = status.get("analogs", {}).get("right", {})
                if raw_analogs:
                    print(f"[DEBUG] Raw analogs['right']: {raw_analogs}")
                update_status._last_log_time = current_time

            # Get command from JoyCon (rotated=True for single rotated controller)
            command = car.get_joycon_command(status, "Plus", current_speed, rotated=True)

            # Update speed based on button presses
            forward, backward, left, right, current_speed = car.joycon_handler.parse_joycon_status(
                status, "Plus", current_speed, rotated=True
            )

            # Debug: Log command values - especially steering
            if left or right:
                print(f"[STEERING COMMAND] left={left}, right={right}, Y-axis={analog_y:.3f}")
            if forward or backward or left or right:
                print(f"[DEBUG] Command: forward={forward}, backward={backward}, left={left}, right={right}, speed=0x{current_speed:02x}")

            # Verify connection before sending command
            if not car.is_connected():
                print("[ERROR] Car is not connected! Attempting to reconnect...")
                try:
                    await car.connect_by_name(car_name)
                except Exception as e:
                    print(f"[ERROR] Failed to reconnect: {e}")
                    break

            # Send command to car
            try:
                await car.move_command(command)
            except Exception as e:
                print(f"[ERROR] Failed to send command: {e}")
                import traceback
                traceback.print_exc()

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await car.stop()
        await car.disconnect()
        print("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())

