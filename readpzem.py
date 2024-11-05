from PZEM004 import PZEM
from machine import UART

pzem = None


def init(p):
    global pzem, powercorr, powertresh
    uart = UART(0, baudrate=9600, bits=8, parity=None, stop=1, tx=p["txpin"], rx=p["rxpin"], timeout=1)
    pzem = PZEM(uart)


def measure_power():
    d = pzem.ReadAllData()
    return d
