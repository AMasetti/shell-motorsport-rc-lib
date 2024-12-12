import asyncio
from shell_motorsport import ShellMotorsportCar

car_name = 'AMASETTI_F1_75_44' # Change this to the name you want to give your car

async def main():
    car = ShellMotorsportCar()

    try:
        if car_name not in car.vehicle_list:
            await car.find_and_name_car(car_name)
        else:
            await car.connect(car_name)

        # Move forwards for 1 second
        await car.move_command(car.retreive_precomputed_message(forward=1))
        await asyncio.sleep(1)
        await car.stop()

        # Move backwards for 1 second
        await car.move_command(car.retreive_precomputed_message(backward=1))
        await asyncio.sleep(1)
        await car.stop()

        # Steering test
        await car.move_command(car.retreive_precomputed_message(left=1))
        await asyncio.sleep(1)
        await car.move_command(car.retreive_precomputed_message(right=1))
        await asyncio.sleep(1)
        await car.stop()

        # Move forwards right then backwards left
        await car.move_command(car.retreive_precomputed_message(forwar=1, right=1))
        await asyncio.sleep(1)
        await car.move_command(car.retreive_precomputed_message(forwar=1, right=1))
        await asyncio.sleep(1)

    finally:
        await car.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
