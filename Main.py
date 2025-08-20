import RPi.GPIO as GPIO
import time
import busio
import board
import digitalio
import json

from scr.Digital_Filters import MedianFilter, EMAFilter
from scr.mqtt_client import MQTTClient
from scr.L298N_MOTOR_PASOS import StepperMotor

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
    'vibracion': (Vibracion, {'pin': 17, 'vmin': 0, 'vmax': 100,  'measure_time': 100}),
    'caudal': (Caudal, {'pin': 26, 'qmin': 0, 'qmax': 100}),
    'gas': (Gas, {'i2c': i2c_bus, 'channel': 0, 'gmin': 0, 'gmax': 1000, 'r0': 10000, 'rl': 10000}),
    'presion': (Presion, {'i2c': i2c_bus, 'channel': 1, 'pmin': 0, 'pmax': 100}),
    'temperatura': (Temperatura, {'spi': spi_bus, 'cs': cs_temp}),
    'desplazamiento': (Desplazamiento, {}),
    'inclinacion': (Inclinacion, {}),
    'motor': (StepperMotor, {'in1': 12, 'in2': 16, 'in3': 20, 'in4': 21}),
}

WINDOW = 5
ALPHA = 0.85

sensores = {k: v[0](**v[1]) for k, v in SENSORES.items()}
filtros_median = {}
filtros_ema = {}

def main():
    mqtt_client = MQTTClient()

    def motor_message_handler(topic, payload):
        try:
            data = json.loads(payload.decode())
            if 'rpm' in data:
                sensores['motor'].set_rpm(data['rpm'])
            if 'steps' in data:
                sensores['motor'].move(data['steps'])
        except json.JSONDecodeError:
            print(f"Error decoding JSON: {payload.decode()}")
        except Exception as e:
            print(f"Error handling motor message: {e}")

    mqtt_client.set_message_handler(motor_message_handler)
    mqtt_client.start()

    try:
        while True:
            payload = {}
            for sensor_name, sensor in sensores.items():
                if sensor_name == 'motor':
                    sensor.update()
                    continue

                val = sensor.get()

                if val is None:
                    continue

                if isinstance(val, dict):
                    if sensor_name not in filtros_median:
                        print(f"INFO: Creando filtros para el sensor multicomponente '{sensor_name}'")
                        filtros_median[sensor_name] = {k: MedianFilter(WINDOW) for k in val}
                        filtros_ema[sensor_name] = {k: EMAFilter(ALPHA) for k in val}

                    med_dict = {k: filtros_median[sensor_name][k].filter(v) for k, v in val.items()}
                    payload[sensor_name] = {k: filtros_ema[sensor_name][k].filter(v) for k, v in med_dict.items()}
                else:
                    if sensor_name not in filtros_median:
                        print(f"INFO: Creando filtros para el sensor '{sensor_name}'")
                        filtros_median[sensor_name] = MedianFilter(WINDOW)
                        filtros_ema[sensor_name] = EMAFilter(ALPHA)

                    med_val = filtros_median[sensor_name].filter(val)
                    payload[sensor_name] = filtros_ema[sensor_name].filter(med_val)

            if payload:
                print(payload)
                mqtt_client.publish(payload)
            time.sleep(0.01) # Reduced sleep time for better motor responsiveness

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
