from string import Template
import RPi.GPIO as GPIO
import time
#from flask import logging
import spidev
import RTIMU
import paho.mqtt.client as mqtt
import os

from HC020K_Emboladas import Emboladas
from HK1100C_Presion import Presion
from HX711_Carga import Carga
from MQ135_GAS import Gas
from SW520_Vibracion import Vibracion
from YFS201_Caudal import Caudal
from IMU10_Desplazamiento_Inclinacion_Temperatura import Desplazamiento, Inclinacion, TemperaturaAmbiente
from DS18B20_Temperatura import Temperatura
from median_filter_visualization import MedianFilter, EMAFilter

def on_connect(client, userdata, flags, rc):
    print("Conectado al broker " + str(rc))

def on_publish(client, userdata, mid):
    print("Mensaje publicado con ID: " + str(mid))
    print("Hola mundo")

def on_message(client, userdata, msg):
    print("Mensaje recibido en el topic " + msg.topic + ": " + str(msg.payload))
    global payloadSub
    payloadSub = str(msg.payload)

def on_subscribe(client, userdata, mid, granted_qos):
    print("Suscrito con ID: " + str(mid) + ", QoS: " + str(granted_qos))

# Configuración MQTT
BROKER = "192.168.68.10"  # Cambia por la IP de tu broker
PORT = 1883
TOPIC = "sensores"
USERNAME = "lift-adm"  # Cambia por tu usuario si es necesario
PASSWORD = "lift2025" # Cambia por tu contraseña si es necesario

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT, 10)

client.on_connect = on_connect
client.on_publish = on_publish
client.on_message = on_message
client.on_subscribe = on_subscribe



# --- Configuración compacta de sensores  ---
SENSORES = { 
    'rpm': (Emboladas, {'pin': 16, 'emin': 0, 'emax': 20, 'muestras': 20, 'intervalo': 0.1}),
    'carga': (Carga, {'pins': {'data': 21, 'clk': 20}, 'cmin': 0, 'cmax': 5000}),
    'vibracion': (Vibracion, {'pin': 17, 'vmin': 0, 'vmax': 100,  'measure_time': 100}),
    'caudal': (Caudal, {'pin': 26, 'qmin': 0, 'qmax': 100}),
    #'gas': (Gas, {'channel': 0, 'gmin': 0, 'gmax': 1000, 'r0': 10000, 'rl': 10000}),
    #'temperatura_ambiente': (TemperaturaAmbiente, {'tmin': -40, 'tmax': 85}),
    #'presion': (Presion, {'pin': {'data': 5}, 'pmin': 0, 'pmax': 100}),
    #'desplazamiento': (Desplazamiento, {'dmin': -16, 'dmax': 16}),
    #'inclinacion': (Inclinacion, {'imin': -180, 'imax': 180}),
    'temperatura_ds18b20': (Temperatura, {'sensor_id': '28-xxxxxxxxxxxx', 'tmin': -55, 'tmax': 125}),  # Reemplaza con el ID real
}

ALPHA = 0.85

sensores = {k: v[0](**v[1]) for k, v in SENSORES.items()}
# Los diccionarios de filtros se inicializan vacíos. Se poblarán dinámicamente.
filtros_median = {}
filtros_ema = {}

try:
    client.subscribe("ejemplo/sensores")
    print("Suscrito al topic: ejemplo/sensores")
    client.loop_start()  # Mantener la conexión MQTT activa



    while True:
        payload = {}
        for sensor_name, sensor in sensores.items():
            val = sensor.get()
            if val is None:
                continue  # Omite el sensor si no hay lectura válida

            if isinstance(val, dict):
                # Para sensores con múltiples valores (diccionarios)
                if sensor_name not in filtros_median:
                    # Inicialización perezosa: crea un diccionario de filtros para cada componente
                    print(f"INFO: Creando filtros para el sensor multicomponente '{sensor_name}'")
                    filtros_median[sensor_name] = {k: MedianFilter(5) for k in val}
                    filtros_ema[sensor_name] = {k: EMAFilter(0.85) for k in val}

                # Aplica el filtro correcto a cada componente individualmente
                med_dict = {k: filtros_median[sensor_name][k].filter(v) for k, v in val.items()}
                payload[sensor_name] = {k: filtros_ema[sensor_name][k].filter(v) for k, v in med_dict.items()}
            else:
                # Para sensores de un solo valor
                if sensor_name not in filtros_median:
                    # Inicialización perezosa: crea una única instancia de filtro
                    print(f"INFO: Creando filtros para el sensor '{sensor_name}'")
                    filtros_median[sensor_name] = MedianFilter(5)
                    filtros_ema[sensor_name] = EMAFilter(0.85)

                med_val = filtros_median[sensor_name].filter(val)
                payload[sensor_name] = filtros_ema[sensor_name].filter(med_val)

        print("Payload actual:", payload)  # Imprime el payload con los valores de los sensores
        client.publish(TOPIC, str(payload))  # Publica los datos filtrados
       # time.sleep(0.5)

except KeyboardInterrupt:
    print("\nFinalizando medición y limpiando GPIO...")
    GPIO.cleanup()
finally:
    GPIO.cleanup()
