import RPi.GPIO as GPIO
import time

class Caudal:
    def __init__(self, pin, qmin, qmax):
        self.pin = pin
        self.qmin = qmin
        self.qmax = qmax
        self.n = 0
        self.caudal = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self._incrementar, bouncetime=2)

    def _incrementar(self, channel):
        self.n += 1

    def get(self, intervalo=1):
        self.n = 0
        t = time.time()
        time.sleep(intervalo)
        f = self.n / (time.time() - t)  # Pulsos por segundo (Hz)
        caudal_raw = f / 7.5  # Caudal en L/min (YFS201: 7.5 pulsos = 1 L/min)
        # Escalado a los límites qmin y qmax
        caudal_esc = min(max(self.qmin, caudal_raw), self.qmax)
        self.caudal = caudal_esc
        return self.caudal

    def cleanup(self):
        GPIO.cleanup()
