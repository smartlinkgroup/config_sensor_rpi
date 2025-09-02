import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class Gas:
    def __init__(self, i2c, channel, gmin, gmax, r0=10000, rl=10000, vref=3.3):
        """
        Inicializa el sensor de gas MQ135 utilizando un ADC ADS1115.
        :param i2c: El objeto bus I2C inicializado.
        :param channel: Canal del ADS1115 a utilizar (0-3).
        :param gmin: Valor mínimo para el escalado de la salida.
        :param gmax: Valor máximo para el escalado de la salida.
        :param r0: Resistencia del sensor en aire limpio.
        :param rl: Resistencia de carga en el circuito.
        :param vref: Voltaje de referencia del circuito del sensor (usualmente 3.3V o 5V).
        """
        self.channel_num = channel
        self.gmin = gmin
        self.gmax = gmax
        self.r0 = r0
        self.rl = rl
        self.vref = vref

        try:
            # Crea el objeto ADC
            self.ads = ADS.ADS1115(i2c)
            # El gain=1 es para un rango de +/-4.096V, seguro para voltajes de 3.3V/5V
            self.ads.gain = 1
            self.chan = AnalogIn(self.ads, channel)
        except Exception as e:
            print(f"[ERROR] No se pudo inicializar el ADC ADS1115 para el sensor de Gas. ¿Está conectado y el I2C habilitado? Error: {e}")
            self.chan = None
        self.gases = {}
            
    def get(self):
        if self.chan is None:
            return None # No se pudo inicializar, no se puede leer.

        try:
            v = self.chan.voltage
            if v < 1e-6: # Evitar división por cero si el voltaje es nulo
                return None

            rs = (self.vref - v) * self.rl / v
            ratio = rs / self.r0 / 3.6 # Factor de calibración del código original
            self.gases = {
                'CO': min(max(self.gmin, 605.18 * (ratio ** -3.937)), self.gmax),
                'Alcohol': min(max(self.gmin, 77.255 * (ratio ** -3.18)), self.gmax),
                'CO2': min(max(self.gmin, 110.47 * (ratio ** -2.862) + 400), self.gmax),
                'Toluen': min(max(self.gmin, 44.947 * (ratio ** -3.445)), self.gmax),
                'NH4': min(max(self.gmin, 102.2 * (ratio ** -2.473)), self.gmax),
                'Aceton': min(max(self.gmin, 34.668 * (ratio ** -3.369)), self.gmax)
            }
            return  ratio 
        except Exception as e:
            print(f"Error al leer el sensor de gas: {e}")
            return None
