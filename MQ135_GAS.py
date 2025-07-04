import spidev
import time

class Gas:
    def __init__(self, channel, gmin, gmax, r0=10000, rl=10000):
        self.channel = channel
        self.gmin = gmin
        self.gmax = gmax
        self.r0 = r0
        self.rl = rl
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 1350000
        self.gases = {}

    def get(self):
        d = self.spi.xfer2([1, (8 + self.channel) << 4, 0])
        val = ((d[1] & 3) << 8) + d[2]
        v = val * 3.3 / 4096  # vref fijo a 3.3V
        rs = (3.3 - v) * self.rl / v
        ratio = rs / self.r0 / 3.6
        self.gases = {
            'CO': min(max(self.gmin, 605.18 * (ratio ** -3.937)), self.gmax),
            'Alcohol': min(max(self.gmin, 77.255 * (ratio ** -3.18)), self.gmax),
            'CO2': min(max(self.gmin, 110.47 * (ratio ** -2.862) + 400), self.gmax),
            'Toluen': min(max(self.gmin, 44.947 * (ratio ** -3.445)), self.gmax),
            'NH4': min(max(self.gmin, 102.2 * (ratio ** -2.473)), self.gmax),
            'Aceton': min(max(self.gmin, 34.668 * (ratio ** -3.369)), self.gmax)
        }
        return self.gases

    def cleanup(self):
        self.spi.close()
