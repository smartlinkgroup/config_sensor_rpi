import RTIMU
import time

class IMU:
    def __init__(self, settings_file="RTIMULib"):
        self.settings = RTIMU.Settings(settings_file)
        self.imu = RTIMU.RTIMU(self.settings)
        if not self.imu.IMUInit():
            raise RuntimeError("IMU no detectado")
        self.imu.setSlerpPower(0.02)
        self.imu.setGyroEnable(True)
        self.imu.setAccelEnable(True)
        self.imu.setCompassEnable(False)

    def read(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            return data
        return None

class Desplazamiento:
    def __init__(self, dmin, dmax, settings_file="RTIMULib"):
        self.settings = RTIMU.Settings(settings_file)
        self.imu = RTIMU.RTIMU(self.settings)
        self.dmin = dmin
        self.dmax = dmax
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
    def __init__(self, imin, imax, settings_file="RTIMULib"):
        self.settings = RTIMU.Settings(settings_file)
        self.imu = RTIMU.RTIMU(self.settings)
        self.imin = imin
        self.imax = imax
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
                    'roll': int(roll * 180 / 3.14159),
                    'pitch': int(pitch * 180 / 3.14159),
                    'yaw': int(yaw * 180 / 3.14159)
                }
        return None

class TemperaturaAmbiente:
    def __init__(self, tmin, tmax, settings_file="RTIMULib"):
        self.settings = RTIMU.Settings(settings_file)
        self.imu = RTIMU.RTIMU(self.settings)
        self.tmin = tmin
        self.tmax = tmax
        if not self.imu.IMUInit():
            raise RuntimeError("IMU no detectado")
        self.imu.setSlerpPower(0.02)
        self.imu.setGyroEnable(True)
        self.imu.setAccelEnable(True)
        self.imu.setCompassEnable(False)

    def get(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            if "temperature" in data:
                temp = data["temperature"]
                return temp
        return None
