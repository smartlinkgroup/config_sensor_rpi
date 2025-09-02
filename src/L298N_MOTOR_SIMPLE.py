import RPi.GPIO as GPIO
import re



class Motor:


    def __init__(self, in1, in2, enable, frequency=1000):
        """Initialize motor with pin numbers"""
        self.in1 = in1
        self.in2 = in2
        self.enable = enable
        self.direction = 0  # 0 = stop, 1 = forward, -1 = backward
        self.current_speed = 0 # Variable para guardar la velocidad actual
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.in1, self.in2, self.enable], GPIO.OUT)
        # Initialize PWM
        self.pwm = GPIO.PWM(self.enable, frequency)
        self.pwm.start(0)
        # Stop motor initially
        self.stop()
        self.inicio=0

    def forward(self, speed):
        """Move forward with speed 0-100"""
        speed = max(0, min(100, speed))
        self.current_speed = speed
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(speed)
        self.direction = 1
    
    def backward(self, speed):
        """Move backward with speed 0-100"""
        speed = max(0, min(100, speed))
        self.current_speed = speed
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
        self.pwm.ChangeDutyCycle(speed)
        self.direction = -1
    
    def stop(self):
        """Stop the motor"""
        self.current_speed = 0
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0)
        self.direction = 0
    
    def set_speed(self, speed):
        speed = max(0, min(100, speed))
        self.current_speed = speed
        self.pwm.ChangeDutyCycle(speed)






    def control_motor(self, data, inicio):
        
        print (data)
        print (inicio)
        
        if data['on_off'] is False:
            self.stop()

        
        if inicio==0  or inicio==2 or inicio==3:
               
               speed_val = data['initial_speed']
               print(speed_val)

        if inicio == 1:
            speed_val = data['speed']

        if data['on_off'] is True:
                (self.backward(speed_val) if data['inversion'] else self.forward(speed_val))

        if speed_val is not None:
            self.set_speed(speed_val)
        print(speed_val)






   
