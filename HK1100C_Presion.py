import spidev
import time

class Presion:
    def __init__(self, pin, pmin=0, pmax=100):
        self.pin = pin
        self.pmin = pmin
        self.pmax = pmax
        self.spi_bus = 0
        self.spi_device = 0
        self.speed_hz = 1350000
        self.spi = spidev.SpiDev()
        self.spi.open(self.spi_bus, self.spi_device)
        self.spi.max_speed_hz = self.speed_hz
        self.presion = 0

    def get(self):
        d = self.spi.xfer2([1, (8 + self.pin['data']) << 4, 0])
        val = ((d[1] & 3) << 8) + d[2]
        volt = val * 3.3 / 4096
        self.presion = volt/3.3*(self.pmax - self.pmin)-self.pmin # Adjusted formula for pressure calculation
        return self.presion

    def cleanup(self):
        self.spi.close()
