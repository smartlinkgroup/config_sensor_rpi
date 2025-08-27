import RPi.GPIO as GPIO

class SimpleDCMotor:
    """
    Simplified DC motor control for L298N
    Usage: motor = SimpleDCMotor(in1_pin, in2_pin, enable_pin, frequency=1000)
    """
    
    def __init__(self, in1, in2, enable, frequency=1000):
        """Initialize motor with pin numbers"""
        self.in1 = in1
        self.in2 = in2
        self.enable = enable
        self.direction = 0  # 0 = stop, 1 = forward, -1 = backward
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.in1, self.in2, self.enable], GPIO.OUT)
        
        # Initialize PWM
        self.pwm = GPIO.PWM(self.enable, frequency)
        self.pwm.start(0)
        
        # Stop motor initially
        self.stop()
    
    def forward(self, speed=100):
        """Move forward with speed 0-100"""
        speed = max(0, min(100, speed))
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(speed)
        self.direction = 1
    
    def backward(self, speed=100):
        """Move backward with speed 0-100"""
        speed = max(0, min(100, speed))
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
        self.pwm.ChangeDutyCycle(speed)
        self.direction = -1
    
    def stop(self):
        """Stop the motor"""
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0)
        self.direction = 0
    
    def set_speed(self, speed):
        """Set speed 0-100 without changing direction"""
        speed = max(0, min(100, speed))
        self.pwm.ChangeDutyCycle(speed)

    def control_motor(self, data):
        """Control motor from a dictionary"""
        if 'on_off' in data and not data['on_off']:
            self.stop()
            return

        if 'inversion' in data:
            if data['inversion']:
                self.backward(data.get('speed', 100))
            else:
                self.forward(data.get('speed', 100))
        elif 'speed' in data:
            self.set_speed(data['speed'])
