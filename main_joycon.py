"""Example script for controlling RC cars with JoyCon controllers."""
import asyncio
from shell_motorsport import ShellMotorsportCar
from pyjoycon import JoyCon, get_R_id, get_L_id

car_name_plus = "AMASETTI_F1_75_44"
car_name_minus = "CES_F1_75"

joycon_plus = JoyCon(*get_R_id())
joycon_minus = JoyCon(*get_L_id())


async def main() -> None:
    """Main function demonstrating JoyCon control of RC cars."""
    car_plus = ShellMotorsportCar()
    car_minus = ShellMotorsportCar()

    try:
        # Connect to cars by name
        if car_name_plus not in car_plus.vehicle_list:
            await car_plus.find_and_name_car(car_name_plus)
        await car_plus.connect_by_name(car_name_plus)

        if car_name_minus not in car_minus.vehicle_list:
            await car_minus.find_and_name_car(car_name_minus)
        await car_minus.connect_by_name(car_name_minus)

        # Current speed for each car (will be updated by JoyCon buttons)
        speed_plus = 0x50
        speed_minus = 0x50

        async def update_status():
            """Generator that yields JoyCon status updates."""
            while True:
                status_plus = joycon_plus.get_status()
                status_minus = joycon_minus.get_status()
                yield status_plus, status_minus
                await asyncio.sleep(0.005)  # 5ms for better responsiveness

        async for status_plus, status_minus in update_status():
            # Get commands from JoyCons (speed is handled internally)
            command_plus = car_plus.get_joycon_command(
                status_plus, "Plus", speed_plus
            )
            command_minus = car_minus.get_joycon_command(
                status_minus, "Minus", speed_minus
            )

            # Update speed based on button presses
            # (Speed is returned in the command, but we track it separately)
            _, _, _, _, speed_plus = car_plus.joycon_handler.parse_joycon_status(
                status_plus, "Plus", speed_plus
            )
            _, _, _, _, speed_minus = car_minus.joycon_handler.parse_joycon_status(
                status_minus, "Minus", speed_minus
            )

            await car_plus.move_command(command_plus)
            await car_minus.move_command(command_minus)

    finally:
        await car_plus.disconnect()
        await car_minus.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
