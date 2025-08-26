import heapq
from collections import deque, Counter

class MedianFilter:
    def __init__(self, window_size):
        if window_size <= 0:
            raise ValueError("El tamaño de la ventana debe ser positivo")
        self.window_size = window_size
        self.min_heap = []  # Almacena la mitad mayor de los números
        self.max_heap = []  # Almacena la mitad menor de los números (como valores negativos)
        self.window = deque() # Almacena los elementos en la ventana para su eliminación
        self.to_remove = Counter() # Rastrea los elementos que se eliminarán de forma perezosa (lazy)

    def _trim_heaps(self):
        # Elimina elementos de la cima de los heaps si están marcados para ser eliminados
        while self.max_heap and self.to_remove[-self.max_heap[0]] > 0:
            val = -heapq.heappop(self.max_heap)
            self.to_remove[val] -= 1

        while self.min_heap and self.to_remove[self.min_heap[0]] > 0:
            val = heapq.heappop(self.min_heap)
            self.to_remove[val] -= 1

    def _rebalance_heaps(self):
        # Equilibra los heaps para mantener sus tamaños con una diferencia máxima de 1
        if len(self.max_heap) > len(self.min_heap) + 1:
            heapq.heappush(self.min_heap, -heapq.heappop(self.max_heap))
        elif len(self.min_heap) > len(self.max_heap):
            heapq.heappush(self.max_heap, -heapq.heappop(self.min_heap))

    def filter(self, value):
        # Añade el nuevo valor a la ventana
        self.window.append(value)

        # Añade el nuevo valor al heap apropiado
        if not self.max_heap or value <= -self.max_heap[0]:
            heapq.heappush(self.max_heap, -value)
        else:
            heapq.heappush(self.min_heap, value)

        # Si la ventana está llena, marca el elemento más antiguo para su eliminación
        if len(self.window) > self.window_size:
            oldest_value = self.window.popleft()
            self.to_remove[oldest_value] += 1

        # Equilibra los heaps después de añadir el nuevo elemento
        self._rebalance_heaps()

        # Elimina cualquier elemento inválido de la cima de los heaps
        self._trim_heaps()

        # Reequilibra de nuevo después de la limpieza, ya que el tamaño podría cambiar
        self._rebalance_heaps()

        # Calcula la mediana
        if len(self.max_heap) == len(self.min_heap):
            # Después de la limpieza, los heaps podrían estar vacíos si se eliminaron todos los elementos
            if not self.max_heap:
                return 0 # O manejar como un error/caso especial
            return int((-self.max_heap[0] + self.min_heap[0]) / 2)
        else:
            return int(-self.max_heap[0])

class EMAFilter:
    def __init__(self, alpha):
        self.alpha = alpha
        self.low_pass_filter = None
    def filter(self, value):
        if self.low_pass_filter is None:
            self.low_pass_filter = value
        else:
            self.low_pass_filter = self.alpha * value + (1 - self.alpha) * self.low_pass_filter
        return int(self.low_pass_filter)
