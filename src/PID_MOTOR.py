import re
import time
from src.L298N_MOTOR_SIMPLE import SimpleDCMotor

# --- PID Controller Class ---
class PID:
    def __init__(self, Kp, Ki, Kd, setpoint=0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self._prev_error = 0
        self._integral = 0
        self._last_time = time.time()

    def update(self, current_value):
        current_time = time.time()
        delta_time = current_time - self._last_time
        if delta_time == 0:
            return 0
        error = self.setpoint - current_value
        P = self.Kp * error
        self._integral += error * delta_time
        I = self.Ki * self._integral
        derivative = (error - self._prev_error) / delta_time
        D = self.Kd * derivative
        self._prev_error = error
        self._last_time = current_time
        return P + I + D

    def set_setpoint(self, setpoint):
        self.setpoint = setpoint
        self.reset()

    def reset(self):
        self._prev_error = 0
        self._integral = 0
        self._last_time = time.time()

# --- Motor Control Class ---
class PID_MOTOR:
    def __init__(self, in1, in2, enable, frequency=1000, max_displacement=10,
                 initial_mqtt_speed=35, initial_boost_speed=55):
        self.motor = SimpleDCMotor(in1, in2, enable, frequency)
        self.mqtt_speed = initial_mqtt_speed # Use the new parameter
        
        self.pid_mode = False 
        self.in_initial_boost_phase = True
        self.max_displacement = max_displacement
        self.pid = PID(Kp=0.5, Ki=0.1, Kd=0.05)
        self.current_motor_speed = 0

        # Safety speed limits
        self.min_speed = 30
        self.max_speed = 50

        # Initial boost speed (configurable from Main.py)
        self.initial_boost_speed = initial_boost_speed

    def set_setpoint(self, setpoint):
        self.pid.set_setpoint(setpoint)
        print(f"New PID RPM setpoint: {setpoint}")

    def set_normal_speed(self, speed):
        self.mqtt_speed = speed
        print(f"Normal speed set to: {self.mqtt_speed}")

    def get_motor_control_handler(self):
        def motor_control_handler(topic, payload):
            try:
                payload_str = payload.decode().strip().replace('{', '').replace('}', '')
                pattern = re.compile(r'"(\w+)"\s*:\s*(\d+)')
                matches = pattern.findall(payload_str)
                data = {key: int(value) for key, value in matches}

                control_data = {}
                if 'onoff' in data:
                    control_data['on_off'] = bool(data['onoff'])
                
                if 'velocidad' in data:
                    if self.pid_mode:
                        self.set_setpoint(data['velocidad'])
                    else:
                        self.mqtt_speed = data['velocidad']
                        print(f"New speed setpoint (MQTT): {self.mqtt_speed}")

                if 'inversion' in data:
                    control_data['inversion'] = bool(data['inversion'])

                if 'on_off' in control_data or 'inversion' in control_data:
                    self.motor.control_motor(control_data)

            except Exception as e:
                print(f"Error handling motor message from {topic}: {e}")
        return motor_control_handler

    def start(self, on_off=True, initial_speed=0, normal_speed=50, inversion=False):
        """
        Starts the motor with specified initial conditions.
        The speed set here will be overridden by update() logic if not in PID mode.
        """
        print(f"Starting motor with on_off={on_off}, initial_speed={initial_speed}, normal_speed={normal_speed}, inversion={inversion}...")
        self.motor.control_motor({'on_off': on_off, 'speed': initial_speed, 'inversion': inversion})
        self.current_motor_speed = initial_speed # Initialize current_motor_speed
        self.mqtt_speed = normal_speed # Update mqtt_speed with the normal_speed from start
        if self.pid_mode:
            self.pid.set_setpoint(normal_speed) # Set PID setpoint to normal_speed
            self.pid.reset()
            print("Motor started in PID mode.")
        else:
            print("Motor started in cyclical mode.")

    def update(self, current_rpm=None, current_displacement=None, direction='indefinida'):
        if self.pid_mode:
            if current_rpm is not None:
                pid_output = self.pid.update(current_rpm)
                self.current_motor_speed += pid_output
                
                # Clamp speed to safety limits
                if self.current_motor_speed > self.max_speed: self.current_motor_speed = self.max_speed
                if self.current_motor_speed < self.min_speed: self.current_motor_speed = self.min_speed
                
                self.motor.control_motor({'speed': self.current_motor_speed})
                print(f"[PID] RPM: {current_rpm}, Setpoint: {self.pid.setpoint}, Speed: {self.current_motor_speed:.2f}")
        else:
            if self.in_initial_boost_phase:
                # Initial boost at configurable speed, ignoring safety limits for startup
                self.motor.control_motor({'speed': self.initial_boost_speed})
                if direction == 'bajada':
                    print("Initial boost complete. Switching to normal cycle.")
                    self.in_initial_boost_phase = False
            else:
                if direction == 'bajada':
                    new_speed = self.mqtt_speed
                    # Clamp to safety limits
                    if new_speed > self.max_speed: new_speed = self.max_speed
                    if new_speed < self.min_speed: new_speed = self.min_speed
                    self.motor.control_motor({'speed': new_speed})
                elif direction == 'subida':
                    speed_subida = self.mqtt_speed
                    # Clamp to safety limits
                    if speed_subida > self.max_speed: speed_subida = self.max_speed
                    if speed_subida < self.min_speed: speed_subida = self.min_speed
                    self.motor.control_motor({'speed': speed_subida})
