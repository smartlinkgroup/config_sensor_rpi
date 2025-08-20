import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class Presion:
    def __init__(self, i2c, channel, pmin=0, pmax=100, vref=3.3):
        """
        Inicializa el sensor de presión HK1100C utilizando un ADC ADS1115.
        :param channel: Canal del ADS1115 a utilizar (0-3).
        :param pmin: Valor mínimo de presión del sensor.
        :param pmax: Valor máximo de presión del sensor.
        :param vref: Voltaje de referencia del circuito del sensor (usualmente 3.3V o 5V).
        """
        self.channel_num = channel
        self.pmin = pmin
        self.pmax = pmax
        self.vref = vref
        self.presion = 0

        try:
            # Crea el objeto ADC
            self.ads = ADS.ADS1115(i2c)
            # El gain=1 es para un rango de +/-4.096V, seguro para voltajes de 3.3V/5V
            self.ads.gain = 1
            self.chan = AnalogIn(self.ads, channel)
        except Exception as e:
            print(f"[ERROR] No se pudo inicializar el ADC ADS1115 para el sensor de Presión. ¿Está conectado y el I2C habilitado? Error: {e}")
            self.chan = None

    def get(self):
        if self.chan is None:
            return None # No se pudo inicializar, no se puede leer.
        
        try:
            volt = self.chan.voltage
            # La fórmula escala el voltaje (0-vref) al rango de presión (pmin-pmax).
            # Se corrigió la fórmula original para un mapeo lineal estándar.
            self.presion = (volt / self.vref) * (self.pmax - self.pmin) + self.pmin
            return self.presion
        except Exception as e:
            print(f"Error al leer el sensor de presión: {e}")
            return None
