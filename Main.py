import RPi.GPIO as GPIO
import time
import busio
import board
import digitalio
import json
import re

from src.Digital_Filters import MedianFilter
from src.mqtt_client import MQTTClient
from src.L298N_MOTOR_SIMPLE import SimpleDCMotor

from sensors.HC020K_Emboladas import Emboladas
from sensors.HK1100C_Presion import Presion
from sensors.HX711_Carga import Carga
from sensors.MQ135_GAS import Gas
from sensors.SW520_Vibracion import Vibracion
from sensors.YFS201_Caudal import Caudal
from sensors.MAX6675_Temperatura import Temperatura
from sensors.IMU10_Desplazamiento_Inclinacion_Temperatura import Inclinacion # Removed Desplazamiento
import RTIMU # Import RTIMU here to initialize it once


# --- Inicialización de buses de hardware compartidos ---
i2c_bus = busio.I2C(board.SCL, board.SDA)

spi_bus = busio.SPI(board.SCK, MISO=board.MISO)

cs_temp = digitalio.DigitalInOut(board.D25)

# --- Configuración de sensores ---
# Initialize RTIMU once
imu_settings = RTIMU.Settings("RTIMULib")
imu_instance = RTIMU.RTIMU(imu_settings)
if not imu_instance.IMUInit():
    # This will fail if the IMU is not connected, but we still want to proceed for other sensors.
    print("Advertencia: IMU no detectado. La medición de inclinación no estará disponible.")
    imu_instance = None # Set to None to avoid errors later
else:
    imu_instance.setSlerpPower(0.02) # Original value
    imu_instance.setGyroEnable(True)
    imu_instance.setAccelEnable(True)
    imu_instance.setCompassEnable(False)


SENSORES = {
    'encoder': (Emboladas, {'pin': 12, 'emin': 0, 'emax': 200, 'muestras': 20, 'dmax': 10, 'debounce_ms': 10}),
    'carga': (Carga, {'pins': {'data': 21, 'clk': 20}, 'cmin': 0, 'cmax': 5000}),
    'vibracion': (Vibracion, {'pin': 17, 'vmin': 0, 'vmax': 100,  'measure_time': 10}),
    'caudal': (Caudal, {'pin': 26, 'qmin': 0, 'qmax': 100}),
    'gas': (Gas, {'i2c': i2c_bus, 'channel': 1, 'gmin': 0, 'gmax': 1000, 'r0': 10000, 'rl': 10000}),
    'presion': (Presion, {'i2c': i2c_bus, 'channel': 0, 'pmin': 0, 'pmax': 100}),
    'temperatura': (Temperatura, {'spi': spi_bus, 'cs': cs_temp}),
    # 'desplazamiento' is now handled by 'encoder'
    'motor': (SimpleDCMotor,{'in1': 24, 'in2': 23, 'enable': 27, 'frequency': 1000})
}

# Only add inclinacion if IMU was initialized successfully
if imu_instance:
    SENSORES['inclinacion'] = (Inclinacion, {'imu_instance': imu_instance})


WINDOW = 3

sensores = {k: v[0](**v[1]) for k, v in SENSORES.items()}
filtros_median = {}

def main():
    mqtt_client = MQTTClient()
    mqtt_speed = 40  # Default speed
    previous_displacement = 0

    def motor_control_handler(topic, payload):
        nonlocal mqtt_speed
        try:
            payload_str = payload.decode()
            payload_str = payload_str.strip().replace('{', '').replace('}', '')
            pattern = re.compile(r'"(\w+)"\s*:\s*(\d+)')
            matches = pattern.findall(payload_str)
            data = {key: int(value) for key, value in matches}

            control_data = {}
            if 'onoff' in data:
                control_data['on_off'] = bool(data['onoff'])
            if 'velocidad' in data:
                mqtt_speed = data['velocidad']
                control_data['speed'] = mqtt_speed
            if 'inversion' in data:
                control_data['inversion'] = bool(data['inversion'])

            if control_data:
                sensores['motor'].control_motor(control_data)
        except Exception as e:
            print(f"Error handling motor message from {topic}: {e}")

    mqtt_client.set_message_handler(motor_control_handler)
    mqtt_client.start()

    # Check if motor exists before trying to control it
    if 'motor' in sensores:
        print("Starting motor...")
        sensores['motor'].control_motor({'on_off': 1, 'speed': mqtt_speed, 'inversion': False})

    try:
        last_known_values = {}
        while True:
            # --- Read all sensors and update last_known_values ---
            for sensor_name, sensor in sensores.items():
                if sensor_name == 'motor':
                    continue
                val = sensor.get()
                if val is not None:
                    if sensor_name == 'encoder':
                        last_known_values['rpm'] = val.get('rpm')
                        last_known_values['desplazamiento'] = val.get('desplazamiento')
                    else:
                        last_known_values[sensor_name] = val
            
            # --- Motor speed logic based on displacement ---
            current_displacement = last_known_values.get('desplazamiento')
            if current_displacement is not None and 'motor' in sensores:
                new_speed = mqtt_speed
                if current_displacement < previous_displacement: # Descending
                    new_speed = mqtt_speed
                
                sensores['motor'].control_motor({'speed': new_speed})
                previous_displacement = current_displacement


            # --- Build payload and filter from last_known_values ---
            payload = {}
            for sensor_name, current_val in last_known_values.items():
                if current_val is None:
                    continue

                # inclinacion and gas return dictionaries
                if sensor_name in ['inclinacion', 'gas']:
                    if sensor_name not in filtros_median:
                        filtros_median[sensor_name] = {k: MedianFilter(WINDOW) for k in current_val}
                    payload[sensor_name] = {k: filtros_median[sensor_name][k].filter(v) for k, v in current_val.items()}
                else: # rpm, desplazamiento, carga, etc. are single values
                    if sensor_name not in filtros_median:
                        filtros_median[sensor_name] = MedianFilter(WINDOW)
                    payload[sensor_name] = filtros_median[sensor_name].filter(current_val)

            # No need to convert numpy floats anymore for desplazamiento

            if payload:
                print(payload)
                mqtt_client.publish(payload)
            time.sleep(0.1) # Adjusted sleep time for more reasonable polling

    except KeyboardInterrupt:
        print("\nFinalizando medición y limpiando GPIO...")
    finally:
        for sensor in sensores.values():
            if hasattr(sensor, 'cleanup'):
                sensor.cleanup()
        mqtt_client.stop()
        GPIO.cleanup()
        print("GPIO limpiado y programa terminado.")

if __name__ == "__main__":
    main()
