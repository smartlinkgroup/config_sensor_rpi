import RPi.GPIO as GPIO
import time
import busio
import board
import digitalio
import json
import re

from src.Digital_Filters import MedianFilter
from src.mqtt_client import MQTTClient
from src.CONTROL_MOTOR import MotorControl

# Import sensor classes
from sensors.HC020K_Emboladas import Encoder, Emboladas, Desplazamiento
from sensors.HK1100C_Presion import Presion
from sensors.HX711_Carga import Carga
from sensors.MQ135_GAS import Gas
from sensors.SW520_Vibracion import Vibracion
from sensors.YFS201_Caudal import Caudal
from sensors.MAX6675_Temperatura import Temperatura
from sensors.IMU10_Desplazamiento_Inclinacion_Temperatura import Inclinacion

# --- Hardware Bus Initialization ---
i2c_bus = busio.I2C(board.SCL, board.SDA)
spi_bus = busio.SPI(board.SCK, MISO=board.MISO)
cs_temp = digitalio.DigitalInOut(board.D25)
encoder = Encoder(pin=12)

# --- Sensor Definitions ---
SENSORES = {
    'rpm': (Emboladas, {'encoder': encoder, 'pulsos_por_rev': 20}),
    'desplazamiento': (Desplazamiento, {'encoder': encoder, 'dmax': 3, 'muestras': 20}),
    'carga': (Carga, {'pins': {'data': 21, 'clk': 20}, 'cmin': 0, 'cmax': 5000}),
    'vibracion': (Vibracion, {'pin': 17, 'vmin': 0, 'vmax': 100, 'measure_time': 10}),
    'caudal': (Caudal, {'pin': 26, 'qmin': 0, 'qmax': 100}),
    'gas': (Gas, {'i2c': i2c_bus, 'channel': 1, 'gmin': 0, 'gmax': 10000, 'r0': 10000, 'rl': 10000}),
    'presion': (Presion, {'i2c': i2c_bus, 'channel': 0, 'pmin': 0, 'pmax': 100}),
    'temperatura': (Temperatura, {'spi': spi_bus, 'cs': cs_temp}),
    'inclinacion': (Inclinacion, {})
}

WINDOW = 5

# Instantiate sensors
sensores = {k: v[0](**v[1]) for k, v in SENSORES.items()}
filtros_median = {}

def main():
    desplazamiento_val = 0
    inclinacion = 0

    # --- Object Initialization ---
    mqtt_client = MQTTClient()
    # Pass the displacement sensor to the motor controller
    motor_control = MotorControl(in1=24, in2=23, enable=27, frequency=1000, desplazamiento=sensores['desplazamiento'])

    # --- MQTT Setup ---
    mqtt_client.set_message_handler(motor_control.mqtt_handler)
    mqtt_client.start()

    try:
        last_values = {}
        while True:
            # 1. Update motor state

            # 2. Process all sensors
            payload = {}
            for sensor_name, sensor in sensores.items():
                val = sensor.get()
                if val is None:
                    val = last_values.get(sensor_name)
                else:
                    last_values[sensor_name] = val
                if val is None:
                    continue
                


                # Apply filter and add to payload
                if isinstance(val, dict):
                    payload[sensor_name] = {k: int(v) for k, v in val.items()}
                elif sensor_name == 'desplazamiento' or sensor_name == 'inclinacion':
                    payload[sensor_name] = int(val)
                else:
                    if sensor_name not in filtros_median:
                        filtros_median[sensor_name] = MedianFilter(WINDOW)
                    payload[sensor_name] = filtros_median[sensor_name].filter(val)

            # Get latest sensor values from payload
            desplazamiento = payload.get('desplazamiento')
            inclinacion = payload.get('inclinacion')
            carga = payload.get('carga')
            

            motor_control.actualizar(inclinacion,carga)
            
            # 3. Publish sensor data
            if payload:
                print(payload)
                mqtt_client.publish(payload)

            time.sleep(0.0001)

    except KeyboardInterrupt:
        print("\nFinalizando medición y limpiando GPIO...")
    finally:
        # --- Cleanup ---
        motor_control.stop()
        for sensor in sensores.values():
            if hasattr(sensor, 'cleanup'):
                sensor.cleanup()
        mqtt_client.stop()
        GPIO.cleanup()
        print("GPIO limpiado y programa terminado.")

if __name__ == "__main__":
    main()
