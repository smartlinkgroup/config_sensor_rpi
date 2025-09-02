import RTIMU
import math
import time
import numpy as np

class DesplazamientoIMU:
    def __init__(self, settings_file="RTIMULib", imu_instance=None):
        if imu_instance:
            self.imu = imu_instance
        else:
            self.settings = RTIMU.Settings(settings_file)
            self.imu = RTIMU.RTIMU(self.settings)
            if not self.imu.IMUInit():
                raise RuntimeError("IMU no detectado")
            self.imu.setSlerpPower(0.02)
            self.imu.setGyroEnable(True)
            self.imu.setAccelEnable(True)
            self.imu.setCompassEnable(False)

        # For displacement calculation
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.position = np.array([0.0, 0.0, 0.0])
        self.last_read_time = time.time()
        self.position_hpf_alpha = 0.995 # Adjusted for smoother filter
        self.filtered_position = np.array([0.0, 0.0, 0.0])

        # MPU6050 specific scale factor for +/- 8g range
        self.accel_scale_factor = 9.81 / 65536.0

    def get(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            
            if data.get("accelValid"):
                current_time = time.time()
                dt = current_time - self.last_read_time
                self.last_read_time = current_time
                
                raw_accel = np.array(data["accel"])
                
                # Convert raw accel to m/s^2
                accel_ms2 = raw_accel * self.accel_scale_factor
                
                # Subtract gravity component
                if data.get("fusionQPoseValid"):
                    q = np.array(data["fusionQPose"]) # (w, x, y, z)
                    q /= np.linalg.norm(q)

                    w, x, y, z = q
                    R = np.array([
                        [1 - 2*y**2 - 2*z**2, 2*x*y - 2*w*z, 2*x*z + 2*w*y],
                        [2*x*y + 2*w*z, 1 - 2*x**2 - 2*z**2, 2*y*z - 2*w*x],
                        [2*x*z - 2*w*y, 2*y*z + 2*w*x, 1 - 2*x**2 - 2*y**2]
                    ])

                    # The gravity vector in the sensor's frame is the third row of the rotation matrix transposed.
                    gravity_sensor_frame = R.T[:, 2] * 9.81 # Scale by g

                    linear_accel = accel_ms2 - gravity_sensor_frame
                else:
                    # Fallback if fusionQPose is not valid.
                    # This is a simplified gravity subtraction, assuming Z is vertical.
                    linear_accel = accel_ms2
                    linear_accel[2] -= 9.81 # Subtract gravity from Z-axis

                noise_threshold = 0.005 # Adjusted noise gate for more sensitivity
                linear_accel[np.abs(linear_accel) < noise_threshold] = 0

                damping = 0.99 # Adjusted damping for more persistence
                self.velocity = (self.velocity + linear_accel * dt) * damping
                self.position += self.velocity * dt

                self.filtered_position = self.position_hpf_alpha * self.filtered_position + (1 - self.position_hpf_alpha) * self.position
                final_position = self.position - self.filtered_position

                return {
                    'dx': final_position[0] * 100,
                    'dy': final_position[1] * 100,
                    'dz': final_position[2] * 100,
                    'linear_accel_x': linear_accel[0],
                    'linear_accel_y': linear_accel[1],
                    'linear_accel_z': linear_accel[2]
                }
        return None

    def reset_displacement(self):
        self.position = np.array([0.0, 0.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.filtered_position = np.array([0.0, 0.0, 0.0])
        print("Displacement reset.")


class Inclinacion:
    def __init__(self, settings_file="RTIMULib", imu_instance=None):
        if imu_instance:
            self.imu = imu_instance
        else:
            self.settings = RTIMU.Settings(settings_file)
            self.imu = RTIMU.RTIMU(self.settings)
            if not self.imu.IMUInit():
                raise RuntimeError("IMU no detectado")
            self.imu.setSlerpPower(0.02)
            self.imu.setGyroEnable(True)
            self.imu.setAccelEnable(True)
            self.imu.setCompassEnable(False)

    def get(self):
        if self.imu.IMURead():
            data = self.imu.getIMUData()
            if data.get("fusionPoseValid"):
                _, pitch, _ = data["fusionPose"]
                return int(math.degrees(pitch))
        return None

