import RTIMU
import math


class Desplazamiento:
    def __init__(self, settings_file="RTIMULib"):
        self.settings = RTIMU.Settings(settings_file)
        self.imu = RTIMU.RTIMU(self.settings)
        self.dmin = -16 # Valor por defecto, se puede ajustar
        self.dmax = 16  # Valor por defecto, se puede ajustar
        if not self.imu.IMUInit():
            raise RuntimeError("IMU no detectado")
        self.imu.setSlerpPower(0.02)
        self.imu.setGyroEnable(True)
        self.imu.setAccelEnable(True)
        self.imu.setCompassEnable(False)

    def get(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            if "accel" in data:
                ax, ay, az = data["accel"]
                return {
                    'ax': ax,
                    'ay': ay,
                    'az': az
                }
        return None

class Inclinacion:
    def __init__(self, settings_file="RTIMULib"):
        self.settings = RTIMU.Settings(settings_file)
        self.imu = RTIMU.RTIMU(self.settings)
        self.imin = -180 # Valor por defecto
        self.imax = 180  # Valor por defecto
        if not self.imu.IMUInit():
            raise RuntimeError("IMU no detectado")
        self.imu.setSlerpPower(0.02)
        self.imu.setGyroEnable(True)
        self.imu.setAccelEnable(True)
        self.imu.setCompassEnable(False)

    def get(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            if "fusionPose" in data:
                roll, pitch, yaw = data["fusionPose"]
                return {
                    'roll': int(math.degrees(roll)),
                    'pitch': int(math.degrees(pitch)),
                    'yaw': int(math.degrees(yaw))
                }
        return None

class TemperaturaAmbiente:
    def __init__(self, settings_file="RTIMULib"):
        self.settings = RTIMU.Settings(settings_file)
        self.imu = RTIMU.RTIMU(self.settings)
        if not self.imu.IMUInit():
            raise RuntimeError("IMU no detectado")

    def get(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            if "temperature" in data:
                return data["temperature"]
        return None
