from string import Template
import RPi.GPIO as GPIO
import time
#from flask import logging
import spidev
import RTIMU
import paho.mqtt.client as mqtt

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

# --- Configuración compacta de sensores y filtros ---
SENSORES = {
    'rpm': (Emboladas, {'pin': 13, 'emin': 0, 'emax': 20, 'muestras': 20, 'intervalo': 0.1}),
    'carga': (Carga, {'pins': {'data': 21, 'clk': 20}, 'cmin': 0, 'cmax': 5000}),
    'vibracion': (Vibracion, {'pin': 17, 'vmin': 0, 'vmax': 100}),
    'caudal': (Caudal, {'pin': 26, 'qmin': 0, 'qmax': 100}),
    #'gas': (Gas, {'channel': 0, 'gmin': 0, 'gmax': 1000, 'r0': 10000, 'rl': 10000}),
    'temperatura_ambiente': (TemperaturaAmbiente, {'tmin': -40, 'tmax': 85}),
    #'presion': (Presion, {'pin': {'data': 5}, 'pmin': 0, 'pmax': 100}),
    'desplazamiento': (Desplazamiento, {'dmin': -16, 'dmax': 16}),
    'inclinacion': (Inclinacion, {'imin': -180, 'imax': 180}),
}
WINDOW = 5
ALPHA = 0.85

sensores = {k: v[0](**v[1]) for k, v in SENSORES.items()}
filtros_median = {k: MedianFilter(WINDOW) for k in SENSORES}
filtros_ema = {k: EMAFilter(ALPHA) for k in SENSORES}

COMP_DESPL = ['ax', 'ay', 'az']
COMP_INCL = ['roll', 'pitch', 'yaw']

try:
    while True:
        payload = {}
        for sensor_name, sensor in sensores.items():
            val = sensor.get()
            if sensor_name == 'desplazamiento' and isinstance(val, dict):
                med = {k: filtros_median[sensor_name].filter(val.get(k)) for k in COMP_DESPL}
                payload[sensor_name] = {k: filtros_ema[sensor_name].filter(med[k]) for k in COMP_DESPL}
            elif sensor_name == 'inclinacion' and isinstance(val, dict):
                med = {k: filtros_median[sensor_name].filter(val.get(k)) for k in COMP_INCL}
                payload[sensor_name] = {k: filtros_ema[sensor_name].filter(med[k]) for k in COMP_INCL}
            elif isinstance(val, dict):
                med = {k: filtros_median[sensor_name].filter(val[k]) for k in val}
                payload[sensor_name] = {k: filtros_ema[sensor_name].filter(med[k]) for k in val}
            else:
                med = filtros_median[sensor_name].filter(val)
                payload[sensor_name] = filtros_ema[sensor_name].filter(med)
        print(payload)
        client.publish(TOPIC, str(payload))
        client.loop_start() # Mantener la conexión MQTT activa
        #time.sleep(1)
except KeyboardInterrupt:
    print("\nFinalizando medición y limpiando GPIO...")
    GPIO.cleanup()

