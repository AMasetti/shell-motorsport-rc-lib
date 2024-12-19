import asyncio
from shell_motorsport import ShellMotorsportCar
from pyjoycon import JoyCon, get_R_id, get_L_id

AMASETTI_F1_75 = "QCAR-0000044"
CES_F1_75 = "QCAR-0000055"

joycon_plus = JoyCon(*get_R_id())
joycon_minus = JoyCon(*get_L_id())

async def main():
    car_plus = ShellMotorsportCar()
    car_minus = ShellMotorsportCar()

    try:
        await car_plus.connect(AMASETTI_F1_75)
        await car_minus.connect(CES_F1_75)

        async def update_status():
            while True:
                status_plus = joycon_plus.get_status()
                status_minus = joycon_minus.get_status()
                yield status_plus, status_minus
                await asyncio.sleep(0.005)  # Reduce interval to 5ms for better responsiveness

        async for status_plus, status_minus in update_status():
            command_plus = car_plus.get_joycon_command(status_plus, 'Plus')
            command_minus = car_minus.get_joycon_command(status_minus, 'Minus')
            await car_plus.move_command(command_plus)
            await car_minus.move_command(command_minus)

    finally:
        await car_plus.disconnect()
        await car_minus.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
