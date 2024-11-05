from AC712 import AC712
from machine import ADC

voltage = 230
powercorr = 1.0
powertresh = 1

current = None


def init(p):
    global powercorr, powertresh, current
    adc = ADC(p["adcpin"])
    current = AC712(adc)
    powercorr = p["powercorr"]
    powertresh = p["powertres"]


def measure_power():
    curr = current.ReadAllData()
    power = curr * voltage * powercorr
    if power < powertresh:
        power = 0
    d = {"Voltage": voltage, "Current": curr, "Power": power, "Energy": 0, "Freq": 50, "Pwr_fac": 1, "Alarm": 0, "CRC": 0}
    return d
