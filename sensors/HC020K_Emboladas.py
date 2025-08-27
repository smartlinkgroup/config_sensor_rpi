import RPi.GPIO as GPIO
import time

class Emboladas:
    def __init__(self, pin, emin, emax, muestras, dmax, debounce_ms=10, **kwargs):
        self.pin = pin
        self.rpm_emin = emin
        self.rpm_emax = emax
        # Total de pulsos efectivos por ciclo completo (subida y bajada)
        self.muestras_por_ciclo = muestras

        # Desplazamiento máximo en mm para una carrera (subida o bajada)
        self.desplazamiento_max_mm = dmax

        # --- Debounce --- 
        self.debounce_s = debounce_ms / 1000.0
        self.last_pulse_time = 0

        # Contador total de pulsos brutos (cada flanco detectado)
        self.n_pulsos_brutos_totales = 0

        # Variables para el cálculo de RPM
        self.last_rpm_calc_time = time.time()
        self.last_n_pulsos_brutos = 0
        self.last_rpm_value = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Detectar AMBOS flancos (subida y bajada) para contar todos los cambios de estado
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self.contador_callback)

    def contador_callback(self, channel):
        """Callback que se ejecuta con cada pulso. Incluye debounce para filtrar ruido."""
        current_time = time.time()
        # Si el tiempo desde el último pulso válido es mayor que el tiempo de debounce
        if (current_time - self.last_pulse_time) > self.debounce_s:
            self.n_pulsos_brutos_totales += 1
            self.last_pulse_time = current_time # Registrar el tiempo de este pulso válido

    def get(self):
        """Calcula y devuelve los valores de RPM y desplazamiento."""
        
        # Convertir pulsos brutos a pulsos efectivos (cada 2 pulsos brutos = 1 pulso efectivo)
        effective_n_pulsos_totales = self.n_pulsos_brutos_totales / 2.0

        # --- Cálculo de RPM ---
        current_time = time.time()
        delta_t = current_time - self.last_rpm_calc_time
        
        if delta_t > 0.2: # Actualizar el valor de RPM periódicamente
            # Calcular el cambio en pulsos brutos y luego convertir a efectivos
            delta_n_brutos = self.n_pulsos_brutos_totales - self.last_n_pulsos_brutos
            effective_delta_n = delta_n_brutos / 2.0

            rpm_raw = 0
            if delta_t > 0 and self.muestras_por_ciclo > 0:
                # Un ciclo (subida+bajada) es una "revolución" del balancín
                revoluciones = effective_delta_n / self.muestras_por_ciclo
                rpm_raw = (revoluciones / delta_t) * 60.0 # Rev por segundo a RPM
            
            self.last_rpm_value = min(max(self.rpm_emin, rpm_raw), self.rpm_emax)
            
            self.last_rpm_calc_time = current_time
            self.last_n_pulsos_brutos = self.n_pulsos_brutos_totales # Almacenar el conteo bruto

        # --- Cálculo de Desplazamiento ---
        # Este cálculo se basa únicamente en el conteo efectivo de pulsos.
        pulso_actual_en_ciclo = effective_n_pulsos_totales % self.muestras_por_ciclo
        
        pulsos_por_carrera = self.muestras_por_ciclo / 2.0
        
        mm_por_pulso = 0
        if pulsos_por_carrera > 0:
            mm_por_pulso = self.desplazamiento_max_mm / pulsos_por_carrera

        # Determinar si es carrera de subida o de bajada
        if pulso_actual_en_ciclo < pulsos_por_carrera:
            # Carrera de subida: el desplazamiento aumenta desde 0
            desplazamiento_actual = pulso_actual_en_ciclo * mm_por_pulso
        else:
            # Carrera de bajada: el desplazamiento disminuye hacia 0
            pulsos_en_bajada = pulso_actual_en_ciclo - pulsos_por_carrera
            desplazamiento_actual = self.desplazamiento_max_mm - (pulsos_en_bajada * mm_por_pulso)

        # Asegurar que el valor se mantenga en el rango [0, dmax]
        desplazamiento_actual = min(max(0, desplazamiento_actual), self.desplazamiento_max_mm)

        return {'rpm': self.last_rpm_value, 'desplazamiento': desplazamiento_actual, 'pulso_en_ciclo': pulso_actual_en_ciclo, 'pulsos_por_carrera': pulsos_por_carrera}

    def reset_desplazamiento(self):
        """Reinicia el contador de pulsos para empezar el desplazamiento desde cero."""
        self.n_pulsos_brutos_totales = 0
        self.last_n_pulsos_brutos = 0
        self.last_pulse_time = 0

    def cleanup(self):
        GPIO.remove_event_detect(self.pin)
