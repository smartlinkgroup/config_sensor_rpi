import RPi.GPIO as GPIO
import time

class Caudal:
    def __init__(self, pin, qmin, qmax, intervalo=1):
        self.pin = pin
        self.qmin = qmin
        self.qmax = qmax
        self.intervalo = intervalo
        self.n = 0
        self.caudal = 0
        self._start_time = None
        self._last_n = 0
        self._finished = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self._incrementar, bouncetime=2)

    def _incrementar(self, channel):
        self.n += 1

    def get(self):
        # Iniciar medición si no ha comenzado o si terminó
        if self._start_time is None or self._finished:
            self._start_time = time.time()
            self._last_n = self.n
            self._finished = False
            self.caudal = 0
        elapsed = time.time() - self._start_time
        if elapsed < self.intervalo:
            # Calcular caudal parcial
            f = (self.n - self._last_n) / elapsed if elapsed > 0 else 0
            caudal_raw = f / 7.5
            caudal_esc = min(max(self.qmin, caudal_raw), self.qmax)
            self.caudal = caudal_esc
        else:
            # Calcular caudal final
            f = (self.n - self._last_n) / elapsed if elapsed > 0 else 0
            caudal_raw = f / 7.5
            caudal_esc = min(max(self.qmin, caudal_raw), self.qmax)
            self.caudal = caudal_esc
            self._finished = True
        return self.caudal

    def cleanup(self):
        GPIO.cleanup()
