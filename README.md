# Control de Autos RC de Shell Motorsport

![Shell Motorsport RC Car](img/image.png)

Esta librería permite controlar los autos de radio control (RC) de Shell Motorsport a través de Bluetooth Low Energy (BLE). Proporciona funciones para conectarse al vehículo, enviar comandos de movimiento y administrar múltiples autos.

## Instalación

Opción 1: Via PIP

```shell
pip install git+https://github.com/AMasetti/shell-motorsport-rc-lib
```


Opción 2: Clonar el Repo

1. Clona este repositorio:
    ```shell
    git clone
    ```

2. Navega al directorio del proyecto:
    ```shell
    cd ShellMotorSport
    ```

3. Instala las dependencias requeridas:
    ```shell
    pip install -r requirements.txt
    ```

Asegúrate de tener instalados los paquetes bleak y pycryptodome para manejar las conexiones BLE y la encriptación AES.


## Uso con main.py

El archivo main.py es un ejemplo de cómo utilizar la librería para controlar tu auto RC.

```python
import asyncio
from shell_motorsport import ShellMotorsportCar

car_name = 'AMASETTI_F1_75_44' # Cambia esto al nombre que desees asignar a tu auto

async def main():
    car = ShellMotorsportCar()

    try:
        if car_name not in car.vehicle_list:
            await car.find_and_name_car(car_name)
        else:
            await car.connect(car_name)

        # Mover hacia adelante por 1 segundo
        await car.move_command(car.retreive_precomputed_message(forward=1))
        await asyncio.sleep(1)
        await car.stop()

        # Mover hacia atrás por 1 segundo
        await car.move_command(car.retreive_precomputed_message(backward=1))
        await asyncio.sleep(1)
        await car.stop()

        # Prueba de dirección
        await car.move_command(car.retreive_precomputed_message(left=1))
        await asyncio.sleep(1)
        await car.move_command(car.retreive_precomputed_message(right=1))
        await asyncio.sleep(1)
        await car.stop()

        # Mover hacia adelante a la derecha y luego hacia atrás a la izquierda
        await car.move_command(car.retreive_precomputed_message(forward=1, right=1))
        await asyncio.sleep(1)
        await car.move_command(car.retreive_precomputed_message(backward=1, left=1))
        await asyncio.sleep(1)

    finally:
        await car.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

Para ejecutar el script:
```shell
python main.py
```

Asegúrate de modificar el valor de `car_name` en `main.py` con el nombre que desees asignar a tu auto.

## Descubrir IDs y guardar tus autos
Para descubrir el `device_id` de tu auto y asignarle un nombre personalizado:

1. Enciende tu auto RC y asegúrate de que esté en modo de emparejamiento.

2. En `main.py`, asigna un nombre único a `car_name`:
    ```shell
    car_name = 'NOMBRE_DE_TU_AUTO'
    # ...existing code...
    ```

3. Ejecuta `main.py`. El programa buscará dispositivos BLE cercanos, encontrará tu auto y guardará su `device_id` en el archivo `vehicle_list.json`.

## Conectar y controlar varios vehículos
La librería permite controlar múltiples autos RC simultáneamente:

1. Asegúrate de que los nombres y `device_ids` de tus autos estén guardados en `vehicle_list.json`.

2. En tu script, crea instancias separadas de `ShellMotorsportCar` para cada auto y conéctalas utilizando sus nombres:
    ```python
    car1 = ShellMotorsportCar()
    await car1.connect('NOMBRE_AUTO_1')

    car2 = ShellMotorsportCar()
    await car2.connect('NOMBRE_AUTO_2')

    # Controlar car1
    await car1.move_forward()
    # Controlar car2
    await car2.move_backward()
    ```

3. Utiliza las funciones de movimiento para controlar cada auto de forma independiente.

## Funcionamiento del protocolo de comunicación
Los autos RC de Shell utilizan Bluetooth Low Energy (BLE) para comunicarse. La librería maneja el protocolo de comunicación que incluye:

- **Mensajes cifrados**: Los comandos se encriptan utilizando AES-128 en modo ECB.
- **Servicios y características BLE**: Se utiliza el servicio con UUID `fff0` y las características de escritura y notificación correspondientes.
- **Formato de los mensajes**: Los mensajes de control tienen una longitud de 16 bytes y contienen información sobre dirección (avance, retroceso, izquierda, derecha) y velocidad.

Para obtener más detalles técnicos, te invitamos a consultar la siguiente [documentación](https://gist.github.com/scrool/e79d6a4cb50c26499746f4fe473b3768) con toda la información de los protocolos y formato de los mensajes.

## Agradecimientos
Queremos expresar nuestro agradecimiento a [Scrool](https://github.com/scrool) por sus valiosas contribuciones en la ingeniería inversa, que han sido fundamentales para este proyecto.
