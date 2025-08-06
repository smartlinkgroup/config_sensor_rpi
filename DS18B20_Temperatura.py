import os

class Temperatura:
    def __init__(self, sensor_id, tmin=-55, tmax=125):
        self.sensor_id = sensor_id  # Ejemplo: '28-00000xxxxxxx'
        self.tmin = tmin
        self.tmax = tmax
        self.temp = None
        self.device_file = f"/sys/bus/w1/devices/{self.sensor_id}/w1_slave"

    def get(self):
            with open(self.device_file, 'r') as f:
                lines = f.readlines()
            if lines[0].strip()[-3:] != 'YES':
                return None  # Error de lectura
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0
                temp_esc = min(max(self.tmin, temp_c), self.tmax)
                self.temp = temp_esc
                return self.temp
            else:
                return None
            
