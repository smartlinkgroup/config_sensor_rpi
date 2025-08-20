import time

class Temperatura:
    def __init__(self, spi, cs, tmin=0, tmax=1024):
        """
        Inicializa y controla el sensor de temperatura MAX6675.
        Esta clase contiene el driver y no depende de librerías externas para el sensor.
        :param spi: Objeto bus SPI (de busio).
        :param cs: Objeto Chip Select (de digitalio).
        :param tmin: Valor mínimo de temperatura.
        :param tmax: Valor máximo de temperatura.
        """
        if not spi or not cs:
            raise ValueError("Los objetos spi y cs no pueden ser None.")

        self.spi_device = spi
        self.cs_pin = cs
        self.tmin = tmin
        self.tmax = tmax
        self._buf = bytearray(2)

        try:
            # Configura el pin CS como salida y lo pone en alto (inactivo)
            self.cs_pin.switch_to_output(value=True)
        except Exception as e:
            # Relanzar la excepción para que el programa principal se detenga y muestre el error de inicialización.
            # Esto es mejor que fallar silenciosamente más tarde.
            raise RuntimeError(f"No se pudo inicializar el pin CS para MAX6675. ¿El pin D25 es correcto? Error: {e}") from e

    def _read_temp_raw(self):
        """Lee 2 bytes del sensor y devuelve el valor crudo."""
        # El constructor ya garantiza que self.spi_device es válido.
        if self.spi_device is None:
            # Si el objeto se ha vuelto None después de la inicialización, este error lo capturará.
            raise RuntimeError("El objeto SPI (self.spi_device) se ha vuelto None.")

        # Se reemplaza el 'with' por un bloqueo manual para evitar un posible
        # problema en la librería Blinka que corrompe el objeto SPI después del primer uso.
        while not self.spi_device.try_lock():
            time.sleep(0)
        try:
            self.cs_pin.value = False
            time.sleep(0.01) # Pequeña pausa para que el sensor se estabilice
            self.spi_device.readinto(self._buf)
            # --- Diagnóstico ---
            # Imprime los bytes crudos para ver qué estamos recibiendo del sensor.
            print(f"DEBUG: Bytes crudos recibidos: {list(self._buf)}")
            self.cs_pin.value = True
        finally:
            self.spi_device.unlock()
            
        # Comprueba el bit de error (termopar desconectado)
        if self._buf[1] & 0x04:
            raise RuntimeError("Termopar no conectado o circuito abierto.")

        value = self._buf[0] << 8 | self._buf[1]
        # Descarta los 3 bits menos significativos (estado y dummy)
        return value >> 3

    def get(self):
        """
        Obtiene la temperatura en grados Celsius.
        Retorna None si hay un error de lectura.
        """
        # El constructor ya garantiza que el sensor se inicializó correctamente.
        try:
            raw_temp = self._read_temp_raw()
            if raw_temp is None:
                return None
            # La resolución es 0.25 grados por bit.
            temp = raw_temp * 0.25
            temp_esc = min(max(self.tmin, temp), self.tmax)
            return temp_esc

        except RuntimeError as e:
            # Captura el error que lanzamos arriba o el del termopar desconectado.
            print(f"[ERROR] Falla de lectura del MAX6675: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Error inesperado con MAX6675: {e}")
            return None
