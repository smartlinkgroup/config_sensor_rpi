import RPi.GPIO as GPIO
import time
import busio
import board
import digitalio
import paho.mqtt.client as mqtt

from HC020K_Emboladas import Emboladas
from HK1100C_Presion import Presion
from HX711_Carga import Carga
from MQ135_GAS import Gas
from SW520_Vibracion import Vibracion
from YFS201_Caudal import Caudal
#from IMU10_Desplazamiento_Inclinacion_Temperatura import Desplazamiento, Inclinacion, TemperaturaAmbiente
from MAX6675_Temperatura import Temperatura 
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

# Especifica la versión de la API para eliminar la advertencia de obsolescencia (DeprecationWarning)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT, 10)

client.on_connect = on_connect
client.on_publish = on_publish
client.on_message = on_message
client.on_subscribe = on_subscribe



# --- Inicialización de buses de hardware compartidos ---

# Inicializa el bus I2C una sola vez para todos los sensores que lo usen.
# Usa los objetos 'board' para una correcta inicialización con Blinka.
i2c_bus = busio.I2C(board.SCL, board.SDA)
print("[INFO] Bus I2C inicializado.")

# Inicializa el bus SPI para el sensor de temperatura MAX6675.
# Usa los pines de hardware SPI por defecto: SCK, MISO. MOSI no es necesario.
print("DEBUG: Inicializando bus SPI...")
spi_bus = busio.SPI(board.SCK, MISO=board.MISO)
print(f"DEBUG: Objeto spi_bus creado: {spi_bus}")

# Inicializa el pin Chip Select (CS) para el sensor de temperatura en GPIO25.
print("DEBUG: Inicializando pin CS...")
cs_temp = digitalio.DigitalInOut(board.D25)
print(f"DEBUG: Objeto cs_temp creado: {cs_temp}")

# --- Configuración de sensores ---
SENSORES = { 
    'rpm': (Emboladas, {'pin': 12, 'emin': 0, 'emax': 20, 'muestras': 20, 'intervalo': 0.1}),
    'carga': (Carga, {'pins': {'data': 21, 'clk': 20}, 'cmin': 0, 'cmax': 5000}),
    'vibracion': (Vibracion, {'pin': 17, 'vmin': 0, 'vmax': 100,  'measure_time': 100}),
    'caudal': (Caudal, {'pin': 26, 'qmin': 0, 'qmax': 100}),
    'gas': (Gas, {'i2c': i2c_bus, 'channel': 0, 'gmin': 0, 'gmax': 1000, 'r0': 10000, 'rl': 10000}),
    'presion': (Presion, {'i2c': 'i2c_bus', 'channel': 1, 'pmin': 0, 'pmax': 100}),
    #'temperatura_ambiente': (TemperaturaAmbiente, {}),
    #'desplazamiento': (Desplazamiento, {}),
    #'inclinacion': (Inclinacion, {}),
    'temperatura': (Temperatura, {'spi': spi_bus, 'cs': cs_temp}),
}

WINDOW = 5
ALPHA = 0.85

sensores = {k: v[0](**v[1]) for k, v in SENSORES.items()}
# Los diccionarios de filtros se inicializan vacíos. Se poblarán dinámicamente.
filtros_median = {}
filtros_ema = {}
payloadSub = None # Inicializar la variable global

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
                    filtros_median[sensor_name] = {k: MedianFilter(WINDOW) for k in val}
                    filtros_ema[sensor_name] = {k: EMAFilter(ALPHA) for k in val}

                # Aplica el filtro correcto a cada componente individualmente
                med_dict = {k: filtros_median[sensor_name][k].filter(v) for k, v in val.items()}
                payload[sensor_name] = {k: filtros_ema[sensor_name][k].filter(v) for k, v in med_dict.items()}
            else:
                # Para sensores de un solo valor
                if sensor_name not in filtros_median:
                    # Inicialización perezosa: crea una única instancia de filtro
                    print(f"INFO: Creando filtros para el sensor '{sensor_name}'")
                    filtros_median[sensor_name] = MedianFilter(WINDOW)
                    filtros_ema[sensor_name] = EMAFilter(ALPHA)

                med_val = filtros_median[sensor_name].filter(val)
                payload[sensor_name] = filtros_ema[sensor_name].filter(med_val)

        print(payload)
        client.publish(TOPIC, str(payload))  # Publica los datos filtrados
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nFinalizando medición y limpiando GPIO...")
finally:
    # Llama al método cleanup de cada sensor si existe
    for sensor in sensores.values():
        if hasattr(sensor, 'cleanup'):
            sensor.cleanup()
