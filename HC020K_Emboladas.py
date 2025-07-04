import RPi.GPIO as GPIO
import time

class Emboladas:
    def __init__(self, pin, emin, emax, muestras, intervalo):
        self.pin = pin
        self.emin = emin
        self.emax = emax
        self.muestras = muestras
        self.intervalo = intervalo
        self.n = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.contador_callback)

    def contador_callback(self, channel):
        self.n += 1

    def get(self):
        self.n = 0
        t1 = time.time()
        time.sleep(self.intervalo)
        rpm_raw = 60 * self.n / self.muestras / (time.time() - t1)
        rpm_esc = min(max(self.emin, rpm_raw), self.emax)
        return rpm_esc
