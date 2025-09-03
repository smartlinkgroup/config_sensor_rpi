import RPi.GPIO as GPIO
import re



class Motor:


    def __init__(self, in1, in2, enable, frequency=1000):
        self.in1 = in1
        self.in2 = in2
        self.enable = enable
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.in1, self.in2, self.enable], GPIO.OUT)
        # Initialize PWM
        self.pwm = GPIO.PWM(self.enable, frequency)
        self.pwm.start(0)
        # Stop motor initially
        self.stop()
        self.inicio=0

    def forward(self):
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
    
    def backward(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
    
    def stop(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0)
    
    def set_speed(self, velocidad):
        velocidad = max(0, min(100, velocidad))
        self.pwm.ChangeDutyCycle(velocidad)






   
