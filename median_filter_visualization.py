class Node:
    def __init__(self, value=0):
        self.value = value
        self.next = None

class MedianFilter:
    STOPPER = 0

    def __init__(self, window_size):
        self.window_size = window_size
        self.buffer = [Node() for _ in range(window_size)]
        # Link buffer nodes circularly
        for i in range(window_size):
            self.buffer[i].next = self.buffer[(i + 1) % window_size]
        self.iterator = 0
        self.smaller = Node(self.STOPPER)
        self.bigger = Node(0)
        self.bigger.next = self.smaller

    def median_filter(self, value):
        if value == self.STOPPER:
            value += 1

        # Update the buffer with the new value
        self.buffer[self.iterator].value = value
        self.iterator = (self.iterator + 1) % self.window_size

        # Robust: collect all values, sort, and return median
        values = [node.value for node in self.buffer]
        values_sorted = sorted(values)
        mid = len(values_sorted) // 2
        if len(values_sorted) % 2 == 1:
            return values_sorted[mid]
        else:
            return (values_sorted[mid - 1] + values_sorted[mid]) / 2
