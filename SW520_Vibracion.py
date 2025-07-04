import RPi.GPIO as GPIO
import time

class Vibracion:
    def __init__(self, pin, vmin, vmax, measure_time=2):
        self.pin = pin
        self.vmin = vmin
        self.vmax = vmax
        self.measure_time = measure_time
        self.vibracion = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def get(self):
        c1 = 0
        t = time.time()
        while time.time() - t < self.measure_time:
            if not GPIO.input(self.pin):
                c1 += 1
                time.sleep(0.05)
        vib_raw = int(c1 / 40 * 100)
        vib_esc = min(max(self.vmin, vib_raw), self.vmax)
        self.vibracion = vib_esc
        return self.vibracion

    def cleanup(self):
        GPIO.cleanup()
