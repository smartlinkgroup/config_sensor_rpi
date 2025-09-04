import re
import json
import time
from src.L298N_MOTOR_SIMPLE import Motor
global on_off, speed, inversion, initial_boost_speed, alarm,t1,t2

# --- Estado inicial y compartido del Motor ---
t1=time.time()
t2=time.time()
alarm = 0
on_off = True
inversion = False
speed = 40
initial_boost_speed = 70
in_initial_boost_phase = True
in_invertion_boost_phase = False
# Variables para detectar cambios de estado
last_on_off_state = True
last_inversion_state = False

class MotorControl:
    def __init__(self, in1, in2, enable, frequency=1000, desplazamiento=None):
        """
        Initializes the motor object and stores a reference to the displacement sensor.
        """
        self.motor = Motor(in1, in2, enable, frequency)
        self.desplazamiento = desplazamiento

    def mqtt_handler(self, topic, payload):
        """
        Handles incoming MQTT messages and updates the module-level state.
        """
        global on_off, speed, inversion, initial_boost_speed, alarm

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            # Silently ignore invalid JSON payloads in production
            return

        if 'onoff' in data:
            on_off = bool(data['onoff'])
            
        if 'velocidad' in data:
            speed = data['velocidad']
            alarm=0

        if 'inversion' in data:
            inversion = bool(data['inversion'])
            alarm=0

        if 'initial_speed' in data:
            initial_boost_speed = data['initial_speed']

    def actualizar(self):
        """
        Reads module-level state and updates the motor, including boost phase logic.
        """
        global on_off, speed, inversion, initial_boost_speed, in_initial_boost_phase, last_on_off_state, last_inversion_state, direction, in_invertion_boost_phase, t1,t2

        # Obtener la dirección del desplazamiento

        direction = self.desplazamiento.get_direction()
         
        # Lógica para apagar el motor
        if not on_off:
            self.motor.stop()
            self.desplazamiento.reset()

        # 1. Si el motor arranca desde parado en dirección de subida
        if on_off != last_on_off_state:
            in_initial_boost_phase = True

        # 2. Si se invierte la dirección hacia 'subida' mientras está en marcha
        if inversion != last_inversion_state:
            in_invertion_boost_phase = True
            self.motor.stop()
            self.desplazamiento.reset()
            t1=time.time()
            t2=time.time()
       
        
     



        # Actualizar los últimos estados para el próximo ciclo
        last_on_off_state = on_off
        last_inversion_state = inversion
        print()
        if on_off:
        # --- Aplicar comandos al motor según la fase ---
            if in_invertion_boost_phase:
                if time.time()-t1>3:
                    self.motor.set_speed(initial_boost_speed)
                    self.motor.backward() if inversion else self.motor.forward()     
                    if time.time()-t2>4:
                        in_invertion_boost_phase = False
                        t2=time.time()


            elif in_initial_boost_phase:
                self.motor.set_speed(initial_boost_speed)
                self.motor.backward() if inversion else self.motor.forward()          
                if direction == 'bajada':
                    in_initial_boost_phase = False

            elif not in_initial_boost_phase and not in_invertion_boost_phase:
            # Operación normal
                self.motor.set_speed(speed)
                self.motor.backward() if inversion else self.motor.forward()
                

        print(last_inversion_state)
        print(last_on_off_state)
        print(in_initial_boost_phase)
        print(direction)

    def start(self):
        self.motor.set_speed(speed)
        

    def stop(self):
        self.motor.stop()