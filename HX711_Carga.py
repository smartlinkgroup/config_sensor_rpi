from hx711v0_5_1 import HX711
import time

class Carga:

    def __init__(self, pins, cmin, cmax, reference_unit=205):
        self.pins = pins
        self.cmin = cmin
        self.cmax = cmax
        self.dout_pin = self.pins['data']
        self.sck_pin = self.pins['clk']
        self.reference_unit = reference_unit
        self.hx = HX711(self.dout_pin, self.sck_pin)
        self.hx.setReadingFormat("MSB", "MSB")
        print("[INFO] Automatically setting the offset.")
        self.hx.autosetOffset()
        offsetValue = self.hx.getOffset()
        print(f"[INFO] Finished automatically setting the offset. The new value is '{offsetValue}'.")
        print(f"[INFO] Setting the 'referenceUnit' at {reference_unit}.")
        self.hx.setReferenceUnit(reference_unit)
        print(f"[INFO] Finished setting the 'referenceUnit' at {reference_unit}.")

    def get(self, grams=True):
        rawBytes = self.hx.getRawBytes()
        weight = self.hx.rawBytesToWeight(rawBytes)
        if not grams:
            weight = weight / 1000  # kilogramos
        weight_esc = min(max(self.cmin, weight), self.cmax)
        return weight_esc

    def debug_info(self):
        rawBytes = self.hx.getRawBytes()
        longValue = self.hx.rawBytesToLong(rawBytes)
        longWithOffsetValue = self.hx.rawBytesToLongWithOffset(rawBytes)
        weightValue = self.hx.rawBytesToWeight(rawBytes)
        print(f"[INFO] longValue: {longValue} | longWithOffsetValue: {longWithOffsetValue} | weight (grams): {weightValue}")
