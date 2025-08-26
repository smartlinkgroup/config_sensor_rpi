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
from sensors.IMU10_Desplazamiento_Inclinacion_Temperatura import Desplazamiento, Inclinacion


# --- Inicialización de buses de hardware compartidos ---
i2c_bus = busio.I2C(board.SCL, board.SDA)

spi_bus = busio.SPI(board.SCK, MISO=board.MISO)

cs_temp = digitalio.DigitalInOut(board.D25)

# --- Configuración de sensores ---
SENSORES = {
    'rpm': (Emboladas, {'pin': 12, 'emin': 0, 'emax': 20, 'muestras': 20, 'intervalo': 0.1}),
    'carga': (Carga, {'pins': {'data': 21, 'clk': 20}, 'cmin': 0, 'cmax': 5000}),
    'vibracion': (Vibracion, {'pin': 17, 'vmin': 0, 'vmax': 100,  'measure_time': 10}),
    'caudal': (Caudal, {'pin': 26, 'qmin': 0, 'qmax': 100}),
    'gas': (Gas, {'i2c': i2c_bus, 'channel': 1, 'gmin': 0, 'gmax': 1000, 'r0': 10000, 'rl': 10000}),
    'presion': (Presion, {'i2c': i2c_bus, 'channel': 0, 'pmin': 0, 'pmax': 100}),
    'temperatura': (Temperatura, {'spi': spi_bus, 'cs': cs_temp}),
    'desplazamiento': (Desplazamiento, {}),
    'inclinacion': (Inclinacion, {}),
    'motor': (SimpleDCMotor,{'in1': 24, 'in2': 23, 'enable': 27, 'frequency': 1000})
}

WINDOW = 3

sensores = {k: v[0](**v[1]) for k, v in SENSORES.items()}
filtros_median = {}

def main():

    mqtt_client = MQTTClient()

    def motor_control_handler(topic, payload):
        try:
            payload_str = payload.decode()
            # The payload is not a valid JSON, so we parse it manually
            # It looks like this: { "onoff": 1 "velocidad": 50 "inversion": 0 }
            # It is missing commas.
            
            # Clean up the string
            payload_str = payload_str.strip().replace('{', '').replace('}', '')
            
            # Use regex to find key-value pairs
            pattern = re.compile(r'"(\w+)"\s*:\s*(\d+)')
            matches = pattern.findall(payload_str)
            
            data = {key: int(value) for key, value in matches}
            
            control_data = {}
            if 'onoff' in data:
                control_data['on_off'] = bool(data['onoff'])
            if 'velocidad' in data:
                control_data['speed'] = data['velocidad']
            if 'inversion' in data:
                control_data['inversion'] = bool(data['inversion'])

            if control_data:
                sensores['motor'].control_motor(control_data)

        except Exception as e:
            print(f"Error handling motor message from {topic}: {e}")

    mqtt_client.set_message_handler(motor_control_handler)
    mqtt_client.start()

    # --- Motor Control Example ---
    print("Starting motor...")
    #sensores['motor'].control_motor({'on_off': 1, 'speed': 50, 'inversion': False})
    

    try:
        while True:
               
          
            payload = {}
            for sensor_name, sensor in sensores.items():
                if sensor_name == 'motor':
                    
                    continue

                val = sensor.get()

                if val is None:
                    continue

                if isinstance(val, dict):
                    if sensor_name not in filtros_median:
                        print(f"INFO: Creando filtros para el sensor multicomponente '{sensor_name}'")
                        filtros_median[sensor_name] = {k: MedianFilter(WINDOW) for k in val}

                    payload[sensor_name] = {k: filtros_median[sensor_name][k].filter(v) for k, v in val.items()}
                else:
                    if sensor_name not in filtros_median:
                        print(f"INFO: Creando filtros para el sensor '{sensor_name}'")
                        filtros_median[sensor_name] = MedianFilter(WINDOW)

                    payload[sensor_name] = filtros_median[sensor_name].filter(val)

            if payload:
                print(payload)
                mqtt_client.publish(payload)
            time.sleep(0.001) # Sleep time can be adjusted

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