import re
import json
from src.L298N_MOTOR_SIMPLE import Motor

# --- Estado inicial y compartido del Motor ---
on_off = True
inversion = False
speed = 40
initial_boost_speed = 70
in_initial_boost_phase = False
# Variables para detectar cambios de estado
_last_on_off_state = False
_last_inversion_state = False

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
        global on_off, speed, inversion, initial_boost_speed

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            # Silently ignore invalid JSON payloads in production
            return

        if 'onoff' in data:
            on_off = bool(data['onoff'])
            
        if 'velocidad' in data:
            speed = data['velocidad']

        if 'inversion' in data:
            inversion = bool(data['inversion'])

        if 'initial_speed' in data:
            initial_boost_speed = data['initial_speed']


    def actualizar(self):
        """
        Reads module-level state and updates the motor, including boost phase logic.
        """
        global on_off, speed, inversion, initial_boost_speed, in_initial_boost_phase, _last_on_off_state, _last_inversion_state
        
        direction = self.desplazamiento.get_direction()

        # Lógica para apagar el motor
        if not on_off:
            self.motor.stop()
            self.desplazamiento.reset()
            in_initial_boost_phase = False
            _last_on_off_state = False
            _last_inversion_state = False
            return


        # --- Disparadores para la fase de impulso ---
        # 1. Si el motor arranca desde parado en dirección de subida
        if on_off != _last_on_off_state:
            in_initial_boost_phase = True

        # 2. Si se invierte la dirección hacia 'subida' mientras está en marcha
        if inversion != _last_inversion_state:
            in_initial_boost_phase = True

        # Actualizar los últimos estados para el próximo ciclo
        _last_on_off_state = on_off
        _last_inversion_state = inversion

        # --- Aplicar comandos al motor según la fase ---
        if in_initial_boost_phase:
            self.motor.set_speed(initial_boost_speed)
            self.motor.backward() if inversion else self.motor.forward()          
            if direction == 'bajada':
                in_initial_boost_phase = False
        else:
            # Operación normal
            self.motor.set_speed(speed)
            self.motor.backward() if inversion else self.motor.forward()
        print(speed)
   

    def stop(self):
        self.motor.stop()