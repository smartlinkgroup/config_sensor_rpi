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

def on_connect(client, userdata, flags, rc):
    print("Conectado al broker " + str(rc))

def on_publish(client, userdata, mid):
    print("Mensaje publicado con ID: " + str(mid))


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

# Inicialización de sensores con min y max configurables
emboladas = Emboladas(13, 0, 20, muestras=20, intervalo=0.1)
#presion = Presion(pin={'data': 5}, pmin=0, pmax=100)
carga = Carga(pins={'data': 21, 'clk': 20}, cmin=0, cmax=5000)
#gas = Gas(channel=0, gmin=0, gmax=1000, r0=10000, rl=10000)
vibracion = Vibracion(pin=17, vmin=0, vmax=100)
caudal = Caudal(pin=26, qmin=0, qmax=100)
desplazamiento = Desplazamiento(dmin=-16, dmax=16)
inclinacion = Inclinacion(imin=-180, imax=180)
#temperatura = Temperatura(sensor_id='28-00000xxxxxxx', tmin=-40, tmax=85)  # Cambia el ID por el de tu sensor
temperatura_ambiente = TemperaturaAmbiente(tmin=-40, tmax=85)

try:
    while True:
        rpm = emboladas.get()
        #pres = presion.get()
        carg = carga.get()
        #gases = gas.get()
        vib = vibracion.get()
        caud = caudal.get()
        val_despl = desplazamiento.get()
        despl = val_despl
        val_incl = inclinacion.get()
        incl = val_incl
        #temp = temperatura.get()
        temp_amb = temperatura_ambiente.get()

        payload = {
            'rpm': rpm,
            #'presion': pres,
            'carga': carg,
            #'gases': gases,
            'vibracion': vib,
            'caudal': caud,
            'desplazamiento': despl,
            'inclinacion': incl,
            #'temperatura': temp,
            'temperatura_ambiente': temp_amb
        }

        print(payload)
        client.publish(TOPIC, str(payload))
        client.loop_start() # Mantener la conexión MQTT activa
        #time.sleep(1)
except KeyboardInterrupt:
    print("\nFinalizando medición y limpiando GPIO...")
    GPIO.cleanup()


