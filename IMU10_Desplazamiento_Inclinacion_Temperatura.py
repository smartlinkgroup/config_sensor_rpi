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
        self.imu.setCompassEnable(True)

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
        self.imu.setCompassEnable(True)

    def get(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            if "accel" in data:
                ax, ay, az = data["accel"]
                return {
                    'ax': min(max(self.dmin, ax), self.dmax),
                    'ay': min(max(self.dmin, ay), self.dmax),
                    'az': min(max(self.dmin, az), self.dmax)
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
        self.imu.setCompassEnable(True)

    def get(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            if "fusionPose" in data:
                roll, pitch, yaw = data["fusionPose"]
                return {
                    'roll': min(max(self.imin, roll), self.imax),
                    'pitch': min(max(self.imin, pitch), self.imax),
                    'yaw': min(max(self.imin, yaw), self.imax)
                }
        return None

class Temperatura:
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
        self.imu.setCompassEnable(True)

    def get(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            if "temperature" in data:
                temp = data["temperature"]
                return min(max(self.tmin, temp), self.tmax)
        return None
