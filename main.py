import asyncio
from shell_motorsport import ShellMotorsportCar

car_name = 'AMASETTI_F1_75' # Change this to the name you want to give your car

async def execute_continuous_move(car, message, duration=1, interval=0.01):
    end_time = asyncio.get_event_loop().time() + duration
    while asyncio.get_event_loop().time() < end_time:
        await car.move_command(message)
        await asyncio.sleep(interval)

async def main():
    car = ShellMotorsportCar()

    try:
        if car_name not in car.vehicle_list:
            await car.find_and_name_car(car_name)
            await car.connect(car.vehicle_list[car_name])
        else:
            await car.connect(car.vehicle_list[car_name])

        # Move forwards for 1 second
        await execute_continuous_move(car, car.retreive_precomputed_message(forward=1))
        await asyncio.sleep(1)

        # Move backwards for 1 second
        await execute_continuous_move(car, car.retreive_precomputed_message(backward=1))
        await asyncio.sleep(1)

        # Steering test
        await execute_continuous_move(car, car.retreive_precomputed_message(left=1))
        await execute_continuous_move(car, car.retreive_precomputed_message(right=1))
        await asyncio.sleep(1)

        # Move forwards right then backwards left
        await execute_continuous_move(car, car.retreive_precomputed_message(forward=1, right=1))
        await execute_continuous_move(car, car.retreive_precomputed_message(backward=1, left=1))
        await asyncio.sleep(1)

    finally:
        await car.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
