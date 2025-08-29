import RPi.GPIO as GPIO
import threading
import time

# Clase 1: Hardware del Encoder
class Encoder:
   
    def __init__(self, pin, debounce_ms=30):
        self.pin = pin
        self.debounce_ms = debounce_ms
        self._count = 0
        self._lock = threading.Lock()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self._callback, bouncetime=self.debounce_ms)
        print(f"EncoderHardware inicializado en el pin {self.pin}")

    def _callback(self, channel):
        with self._lock:
            self._count += 1

    def get_count(self):
        with self._lock:
            return self._count

    def reset_count(self):
        with self._lock:
            self._count = 0


# Clase 2: Lógica de Emboladas (RPM)
class Emboladas:
 
    def __init__(self, encoder, pulsos_por_rev=1):
        self.encoder = encoder
        self.pulsos_por_rev = pulsos_por_rev
        self.last_count = 0
        self.last_time = time.time()
        self.rpm = 0

    def get(self):
        current_time = time.time()
        delta_time = current_time - self.last_time

        if delta_time >= 1.0:
            current_count = self.encoder.get_count()
            delta_count = current_count - self.last_count
            self.last_count = current_count

            revoluciones = delta_count / self.pulsos_por_rev
            self.rpm = (revoluciones / delta_time) * 60
            self.last_time = current_time
            
        return self.rpm

# Clase 3: Lógica de Desplazamiento del Encoder
class Desplazamiento:
   
    def __init__(self, encoder, dmax, muestras):
        self.encoder = encoder
        self.dmax = dmax
        self.muestras_subida = muestras
        self.pulsos_ciclo_completo = self.muestras_subida * 2
        self.distancia_por_pulso = self.dmax / self.muestras_subida

    def get(self):
        count = self.encoder.get_count()
        count_en_ciclo = count % self.pulsos_ciclo_completo

        desplazamiento_actual = 0
        direccion = ''
        if count_en_ciclo <= self.muestras_subida:
            # Primera mitad del ciclo (subida)
            desplazamiento_actual = count_en_ciclo * self.distancia_por_pulso
            direccion = 'subida'
        else:
            # Segunda mitad del ciclo (bajada)
            desplazamiento_actual = (self.pulsos_ciclo_completo - count_en_ciclo) * self.distancia_por_pulso
            direccion = 'bajada'
            
        return {'desplazamiento': desplazamiento_actual, 'direccion': direccion}

    def reset(self):
        self.encoder.reset_count()
