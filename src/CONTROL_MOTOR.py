import re
import json
import time
from src.L298N_MOTOR_SIMPLE import Motor
global on_off, speed, inversion, initial_boost_speed,t1,t2,t3,t4,alarm_phase,alarm,last_alarm_state

# --- Estado inicial y compartido del Motor ---
t1=0
t2=0
t3=0
t4=0
alarm_phase = False
alarm = 0
on_off = True
inversion = False
speed = 50
initial_boost_speed = 70
in_initial_boost_phase = True
in_invertion_boost_phase = False
# Variables para detectar cambios de estado
last_on_off_state = True
last_inversion_state = False
alarm_phase = False
alarm_phase=False
alarm=False
last_alarm_state=False

class MotorControl:
    def __init__(self, in1, in2, enable, frequency=1000, desplazamiento=0):
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

    def actualizar(self, inclinacion=None,carga=None):
        """
        Reads module-level state and updates the motor, including boost phase logic.
        """
        global on_off, speed, inversion, initial_boost_speed, in_initial_boost_phase, last_on_off_state, last_inversion_state, direction, in_invertion_boost_phase, t1,t2,t3,t4,alarm_phase,alarm,last_alarm_state

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

        if alarm==0:
            t4=time.time()

        if carga>=100 and carga<=500:
            alarm=0
            



        # Actualizar los últimos estados para el próximo ciclo
        last_on_off_state = on_off
        last_inversion_state = inversion
        last_alarm_state = alarm



        print(inclinacion)
        if inclinacion is not None and (inclinacion > 15 or inclinacion < -15):
            self.motor.stop()
            in_initial_boost_phase = True
            self.desplazamiento.reset()
            t3=time.time()

        elif alarm==1 and (time.time()-t4>3):
            self.motor.stop()
            in_initial_boost_phase = True
            
        elif carga is not None and (carga > 500):
            self.motor.set_speed(speed+30)
            alarm=1
                
        elif carga is not None and (carga <100):
            self.motor.set_speed(speed-5)
            alarm=1


        elif on_off:
        # --- Aplicar comandos al motor según la fase ---
            if in_invertion_boost_phase:
                if time.time()-t1>3:
                    self.motor.set_speed(initial_boost_speed)
                    self.motor.backward() if inversion else self.motor.forward()     
                    if time.time()-t2>4:
                        in_invertion_boost_phase = False
                        t2=time.time()
        
            elif in_initial_boost_phase:
                if time.time()-t3>3:
                    self.motor.set_speed(initial_boost_speed)
                    self.motor.backward() if inversion else self.motor.forward()          
                    if direction == 'bajada':
                        in_initial_boost_phase = False
                        t3=time.time()


            elif not in_initial_boost_phase and not in_invertion_boost_phase:
                self.motor.set_speed(speed)
                self.motor.backward() if inversion else self.motor.forward()
                
            elif alarm_phase:
                self.motor.set_speed(initial_boost_speed)
                self.motor.backward() if inversion else self.motor.forward()          
                if direction == 'bajada':
                    in_initial_boost_phase = False


        


        print(last_inversion_state)
        print(last_on_off_state)
        print(in_initial_boost_phase)
        print(direction)

    def start(self):
        self.motor.set_speed(speed)
        

    def stop(self):
        self.motor.stop()