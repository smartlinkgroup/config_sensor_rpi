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
from median_filter_visualization import MedianFilter

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

# Inicialización de senssudo ores con min y max configurables
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

WINDOW = 11
filtros = {
    'rpm': MedianFilter(WINDOW),
    'carga': MedianFilter(WINDOW),
    'vibracion': MedianFilter(WINDOW),
    'caudal': MedianFilter(WINDOW),
    #'temperatura': MedianFilter(WINDOW),
    'temperatura_ambiente': MedianFilter(WINDOW),
    # 'presion': MedianFilter(WINDOW),
    # 'gas': MedianFilter(WINDOW)
}
# Filtros de mediana individuales para cada componente de desplazamiento e inclinacion
filtros_desplazamiento = {k: MedianFilter(WINDOW) for k in ['ax', 'ay', 'az']}
filtros_inclinacion = {k: MedianFilter(WINDOW) for k in ['roll', 'pitch', 'yaw']}

def safe_update(filtro, valor):
    if valor is not None:
        return filtro.median_filter(valor)
    else:
        # Si el filtro está vacío o el nodo es None, devuelve None
        if not filtro.buffer:
            return None
        idx = (filtro.iterator - 1) % filtro.window_size
        last_node = filtro.buffer[idx]
        if last_node is not None and hasattr(last_node, 'value'):
            return filtro.median_filter(last_node.value)
        else:
            return None

try:
    while True:
        rpm = safe_update(filtros['rpm'], emboladas.get())
        #pres = safe_update(filtros['presion'], presion.get()) if 'presion' in filtros else None
        carg = safe_update(filtros['carga'], carga.get())
        #gases = safe_update(filtros['gas'], gas.get()) if 'gas' in filtros else None
        vib = safe_update(filtros['vibracion'], vibracion.get())
        caud = safe_update(filtros['caudal'], caudal.get())
        # Filtrado por componente para desplazamiento
        val_despl = desplazamiento.get()
        if isinstance(val_despl, dict):
            despl = {k: safe_update(filtros_desplazamiento[k], val_despl.get(k)) for k in filtros_desplazamiento}
        else:
            despl = safe_update(filtros['desplazamiento'], val_despl)
        # Filtrado por componente para inclinacion
        val_incl = inclinacion.get()
        if isinstance(val_incl, dict):
            incl = {k: safe_update(filtros_inclinacion[k], val_incl.get(k)) for k in filtros_inclinacion}
        else:
            incl = safe_update(filtros['inclinacion'], val_incl)
        #temp = safe_update(filtros['temperatura'], temperatura.get())
        temp_amb = safe_update(filtros['temperatura_ambiente'], temperatura_ambiente.get())

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


