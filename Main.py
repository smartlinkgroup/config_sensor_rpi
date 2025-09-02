import RPi.GPIO as GPIO
import time
import busio
import board
import digitalio
import json
import re

from src.Digital_Filters import MedianFilter
from src.mqtt_client import MQTTClient
from src.L298N_MOTOR_SIMPLE import Motor

# --- Motor Control Parameters ---
MOTOR_ON_OFF = True
MOTOR_NORMAL_SPEED = 35 # This will be the initial_mqtt_speed
MOTOR_INITIAL_SPEED= 70 # New parameter for initial boost speed
MOTOR_INVERTION= 0 # New parameter for initial boost speed

# Importar las tres clases desde el archivo modificado
from sensors.HC020K_Emboladas import Encoder, Emboladas, Desplazamiento
from sensors.HK1100C_Presion import Presion
from sensors.HX711_Carga import Carga
from sensors.MQ135_GAS import Gas
from sensors.SW520_Vibracion import Vibracion
from sensors.YFS201_Caudal import Caudal
from sensors.MAX6675_Temperatura import Temperatura
from sensors.IMU10_Desplazamiento_Inclinacion_Temperatura import Inclinacion

# --- Inicialización de buses de hardware compartidos ---
i2c_bus = busio.I2C(board.SCL, board.SDA)
spi_bus = busio.SPI(board.SCK, MISO=board.MISO)
cs_temp = digitalio.DigitalInOut(board.D25)
encoder= Encoder(pin=12)


SENSORES = {
    'rpm': (Emboladas, {'encoder': encoder, 'pulsos_por_rev': 20}),
    'desplazamiento': (Desplazamiento, {'encoder': encoder, 'dmax': 5, 'muestras': 20}),
    'carga': (Carga, {'pins': {'data': 21, 'clk': 20}, 'cmin': 0, 'cmax': 5000}),
    'vibracion': (Vibracion, {'pin': 17, 'vmin': 0, 'vmax': 100, 'measure_time': 10}),
    'caudal': (Caudal, {'pin': 26, 'qmin': 0, 'qmax': 100}),
    'gas': (Gas, {'i2c': i2c_bus, 'channel': 1, 'gmin': 0, 'gmax': 1000, 'r0': 10000, 'rl': 10000}),
    'presion': (Presion, {'i2c': i2c_bus, 'channel': 0, 'pmin': 0, 'pmax': 100}),
    'temperatura': (Temperatura, {'spi': spi_bus, 'cs': cs_temp}),
    'inclinacion': (Inclinacion, {}),
    'motor': (Motor, {'in1': 24, 'in2': 23, 'enable': 27, 'frequency': 1000})
}

WINDOW = 3

sensores = {k: v[0](**v[1]) for k, v in SENSORES.items()}
filtros_median = {}

def main():
    mqtt_client = MQTTClient()

    motor = sensores.get('motor')
    mqtt_client.start()
    inicio=0
    motor.control_motor({'on_off': MOTOR_ON_OFF, 'initial_speed': MOTOR_INITIAL_SPEED, 'speed': MOTOR_NORMAL_SPEED, 'inversion': MOTOR_INVERTION},inicio)

    try:
        # Llama a control_motor una vez para la configuración inicial

        while True:
            payload = {}
            desplazamiento_val = None

            # Procesa los sensores en un solo bucle
            for sensor_name, sensor in sensores.items():
                if sensor_name == 'motor':
                    continue
                
                val = sensor.get()
                if val is None:
                    continue

                # Guarda el valor de desplazamiento para la lógica del motor
                if sensor_name == 'desplazamiento':
                    desplazamiento_val = val

                # Aplica filtro, convierte a entero y añade al payload
                if isinstance(val, dict):
                    # Para el sensor de gas, convierte cada valor del diccionario a entero
                    payload[sensor_name] = {k: int(v) for k, v in val.items()}
                elif sensor_name == 'desplazamiento':
                    # Para el desplazamiento, convierte el valor a entero
                    payload[sensor_name] = int(val)
                else:
                    # Para los demás, el filtro ya devuelve un entero
                    if sensor_name not in filtros_median:
                        filtros_median[sensor_name] = MedianFilter(WINDOW)
                    payload[sensor_name] = filtros_median[sensor_name].filter(val)

            # --- Lógica de control del motor ---
            if inicio == 0 and desplazamiento_val >= 4 and desplazamiento_val is not None:
                inicio = 1
                motor.control_motor({'on_off': MOTOR_ON_OFF, 'initial_speed': MOTOR_INITIAL_SPEED, 'speed': MOTOR_NORMAL_SPEED, 'inversion': MOTOR_INVERTION},inicio)
                
            if inicio == 2:
                sensores.get('desplazamiento').reset()
                
            if inicio == 3 :
                inicio=1
            
            
                


            def motor_control_handler(topic, payload):

                payload_str = payload.decode()
                payload_str = payload_str.strip().replace('{', '').replace('}', '')
                pattern = re.compile(r'"(\w+)"\s*:\s*(\d+)')
                matches = pattern.findall(payload_str)
                data = {key: int(value) for key, value in matches}

                control_data = {}
                nonlocal inicio
                if 'onoff' in data:
                    control_data['on_off'] = bool(data['onoff'])

                if control_data['on_off'] is True and inicio==2:
                    inicio=3

                if control_data['on_off'] is False:
                    inicio=2
                    
                if 'velocidad' in data:
                    control_data['speed'] = data['velocidad']
              
                if 'inversion' in data:
                    control_data['inversion'] = bool(data['inversion'])
                if 'initial_speed' in data:
                    control_data['initial_speed'] = data['initial_speed']

                if control_data:
                    sensores['motor'].control_motor(control_data,inicio)
                print(f"Control data processed: {control_data}")

            mqtt_client.set_message_handler(motor_control_handler)
            # Publica el payload si contiene datos
            if payload:
                print(payload)
                mqtt_client.publish(payload)

            time.sleep(0.0001)

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
