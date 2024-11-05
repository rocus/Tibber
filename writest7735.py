from ST7735 import TFT
from sysfont import sysfont
from machine import SPI, PWM

tft = None  # Necessary????
# spi= None
# pwm= None


def init(p):
    global tft
    pwm = PWM(p["pwmpin"])
    pwm.freq(p["pwmfreq"])
    pwm.duty_u16(p["pwmduty"])
    spi = SPI(0, baudrate=10000000, polarity=0, phase=0, sck=p["sckpin"], mosi=p["mosipin"], miso=None)
    tft = TFT(spi, p["aDCpin"], p["aResetpin"], p["aCSpin"])
    tft.initg()
    tft.rgb(True)
    tft.fill(TFT.BLACK)
    tft.text((30, 150), "Starting", TFT.WHITE, sysfont, 1)


dot = True


def show_power(d):
    global dot

    def line(h, v, txt):
        tft.text((h, v), txt, TFT.WHITE, sysfont, 1, nowrap=True)

    dot = not dot
    if d == {}:
        line(30, 150, "Not connected")
    else:
        h = 10
        v = 30
        n = sysfont["Height"] * 2
        line(h, v,         f'Voltage {d["Voltage"] :7.1f} V ')
        line(h, v + n,     f'Current {d["Current"] :7.3f} A ')
        line(h, v + 2 * n, f'Power   {d["Power"]   :7.1f} W ')
        line(h, v + 3 * n, f'Energy  {d["Energy"]    :7d} Wh')
        line(h, v + 4 * n, f'Freq    {d["Freq"]    :7.1f} Hz')
        line(h, v + 5 * n, f'Pwr_fac {d["Pwr_fac"] :7.2f}   ')
        line(60, 140, (".", " ")[dot])
        line(30, 150, "             ")
