# SPDX-FileCopyrightText: 2017 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_max6675`
====================================================

CircuitPython driver for MAX6675 thermocouple amplifier

* Author(s): Tony DiCola, Scott Shawcroft
"""

from micropython import const

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MAX6675.git"

_MAX6675_DEFAULT_ADDRESS = const(0x67)


class MAX6675:
    """Driver for the MAX6675 thermocouple amplifier."""

    def __init__(self, spi, cs):
        self.spi_device = spi
        self.cs = cs
        # Chip select needs to be active low.
        self.cs.switch_to_output(value=True)

    @property
    def temperature(self):
        """Return the temperature of the sensor in degrees Celsius."""
        return self._read() / 4.0

    def _read(self):
        """Read 2 bytes from the sensor."""
        buf = bytearray(2)
        with self.spi_device as spi:
            self.cs.value = False
            spi.readinto(buf)
            self.cs.value = True
        if buf[1] & 0x04:
            raise RuntimeError("Thermocouple is not connected.")
        value = buf[0] << 8 | buf[1]
        return value >> 3
