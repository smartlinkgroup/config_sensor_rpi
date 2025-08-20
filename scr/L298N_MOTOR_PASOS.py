"""
This Raspberry Pi code was developed by newbiely.com
This Raspberry Pi code is made available for public use without any restriction
For comprehensive instructions and wiring diagrams, please visit:
https://newbiely.com/tutorials/raspberry-pi/raspberry-pi-stepper-motor
"""
import RPi.GPIO as GPIO
import time

class StepperMotor:
    def __init__(self, in1, in2, in3, in4):
        self.pins = [in1, in2, in3, in4]
        GPIO.setmode(GPIO.BCM)
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)

        self.sequence = [
            [1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0],
            [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1]
        ]
        self.sequence_index = 0
        self.target_steps = 0
        self.delay = 0
        self.last_step_time = 0
        self.direction = 1

        self.deg_per_step = 0.087890625
        self.steps_per_revolution = int(360 / self.deg_per_step)

    def set_step(self, w1, w2, w3, w4):
        GPIO.output(self.pins[0], w1)
        GPIO.output(self.pins[1], w2)
        GPIO.output(self.pins[2], w3)
        GPIO.output(self.pins[3], w4)

    def set_rpm(self, rpm):
        if rpm == 0:
            self.delay = 0
        else:
            # Calculate delay based on steps per revolution and sequence length
            self.delay = 60.0 / (self.steps_per_revolution * len(self.sequence) * rpm)

    def move(self, steps):
        self.target_steps = abs(steps)
        self.direction = 1 if steps > 0 else -1

    def update(self):
        if self.target_steps == 0 or self.delay == 0:
            return False

        current_time = time.time()
        if current_time - self.last_step_time >= self.delay:
            self.sequence_index = (self.sequence_index + self.direction) % len(self.sequence)
            self.set_step(*self.sequence[self.sequence_index])
            self.last_step_time = current_time
            self.target_steps -= 1
            return True
        return False

    def is_busy(self):
        return self.target_steps > 0

    def cleanup(self):
        GPIO.cleanup()
        print('-> GPIO limpiados')

if __name__ == '__main__':
    # Define GPIO pins for L298N driver
    IN1 = 12
    IN2 = 16
    IN3 = 20
    IN4 = 21

    motor = StepperMotor(IN1, IN2, IN3, IN4)
    motor.set_rpm(700)

    try:
        print("Moving forward one revolution")
        motor.move(motor.steps_per_revolution * len(motor.sequence))
        while motor.is_busy():
            motor.update()
            # In a real non-blocking application, you would do other tasks here.
            # For this example, we'll just spin.

        time.sleep(1) # Pause between movements

        print("Moving backward one revolution")
        motor.move(-motor.steps_per_revolution * len(motor.sequence))
        while motor.is_busy():
            motor.update()
            # In a real non-blocking application, you would do other tasks here.
            # For this example, we'll just spin.

    except KeyboardInterrupt:
        print('-> Interrupcion por teclado')
    finally:
        motor.cleanup()