import RPi.GPIO as GPIO
import time

class Vibracion:
    def __init__(self, pin, vmin, vmax, measure_time):
        self.pin = pin
        self.vmin = vmin
        self.vmax = vmax
        self.measure_time = measure_time
        self.vibracion = 0
        self._start_time = None
        self._c1 = 0
        self._last_state = 1
        self._finished = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def get(self):
        # Iniciar medición si no ha comenzado
        if self._start_time is None or self._finished:
            print("--- STARTING NEW VIBRATION MEASUREMENT ---")
            self._start_time = time.time()
            self._c1 = 0
            self._last_state = 1
            self._finished = False
            self.vibracion = 0

        elapsed = time.time() - self._start_time
        
        if elapsed < self.measure_time:
            state = GPIO.input(self.pin)
           
            if state == 0 and self._last_state == 1:
                self._c1 += 1
                print(f"*** VIBRATION DETECTED! New count: {self._c1} ***")
            self._last_state = state
        else:
            if not self._finished:
                print(f"--- MEASUREMENT FINISHED --- Final count: {self._c1}")
                # Measurement cycle is over.
                self._finished = True

        # The scaling factor of 40 in the original code was likely too high,
        # causing low readings. A smaller value like 10 will make the sensor
        # more sensitive. This factor represents the number of vibration events
        # detected in 'measure_time' that would correspond to a 100% reading.
        scaling_factor = 10
        vib_raw = int((self._c1 / scaling_factor) * 100)
        vib_esc = min(max(self.vmin, vib_raw), self.vmax)
        self.vibracion = vib_esc
        
        return self.vibracion

    def cleanup(self):
        GPIO.cleanup()
