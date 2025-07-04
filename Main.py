import RPi.GPIO as GPIO
import time
import spidev
import RTIMU
import paho.mqtt.client as mqtt

from HC020K_Emboladas import Emboladas
from HK1100C_Presion import Presion
from HX711_Carga import Carga
from MQ135_GAS import Gas
from SW520_Vibracion import Vibracion
from YFS201_Caudal import Caudal
from IMU10_Desplazamiento_Inclinacion_Temperatura import Desplazamiento, Inclinacion, Temperatura

# Configuración MQTT
BROKER = "localhost"  # Cambia por la IP de tu broker
PORT = 1883
TOPIC = "sensores"
USERNAME = None  # Cambia por tu usuario si es necesario
PASSWORD = None  # Cambia por tu contraseña si es necesario

client = mqtt.Client()
if USERNAME and PASSWORD:
    client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT, 60)


# Inicialización de sensores con min y max configurables
emboladas = Emboladas(17, 0, 20, muestras=20, intervalo=0.1)
presion = Presion(pin={'data': 5}, pmin=0, pmax=100)
carga = Carga(pins={'data': 21, 'clk': 20}, cmin=0, cmax=5000)
gas = Gas(channel=0, gmin=0, gmax=1000, r0=10000, rl=10000)
vibracion = Vibracion(pin=13, vmin=0, vmax=100)
caudal = Caudal(pin=26, qmin=0, qmax=100)
desplazamiento = Desplazamiento(dmin=-16, dmax=16)
inclinacion = Inclinacion(imin=-180, imax=180)
temperatura = Temperatura(tmin=-40, tmax=85)  # pines 2 y 3 para I2C

try:
    while True:
        rpm = emboladas.get()
        pres = presion.get()
        carg = carga.get()
        gases = gas.get()
        vib = vibracion.get()
        caud = caudal.get()
        despl = desplazamiento.get()
        incl = inclinacion.get()
        temp = temperatura.get()
        print(f"RPM: {rpm:.2f}")
        print(f"Presión: {pres:.2f} bar")
        print(f"Carga: {carg:.2f} g")
        print(f"Gases: {gases}")
        print(f"Vibración: {vib} %")
        print(f"Caudal: {caud:.2f} L/min")
        print(f"Desplazamiento: {despl}")
        print(f"Inclinación: {incl}")
        print(f"Temperatura: {temp}")
        # Publicar en MQTT
        payload = {
            'rpm': rpm,
            'presion': pres,
            'carga': carg,
            'gases': gases,
            'vibracion': vib,
            'caudal': caud,
            'desplazamiento': despl,
            'inclinacion': incl,
            'temperatura': temp
        }
        client.publish(TOPIC, str(payload))
        time.sleep(1)
except KeyboardInterrupt:
    print("\nFinalizando medición y limpiando GPIO...")
    GPIO.cleanup()

