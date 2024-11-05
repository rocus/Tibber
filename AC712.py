from machine import ADC
from time    import sleep

maxint = 1 << 16


class AC712:
    def __init__(self, adc):
        self.adc   = adc
        self.imean = maxint / 2
        self.corr  = 3300 / 100 / maxint

    def ReadAllData(self):
        from math import sqrt

        nrsamples = 100

        isum = 0.0
        isqr = 0.0

        for j in range(0, nrsamples):
            i = self.adc.read_u16()
            isum += i
            isqr += ((i - self.imean) * (i - self.imean))
            sleep(0.001)
        self.imean = (self.imean + isum / nrsamples) / 2
        isqrt = sqrt(isqr / nrsamples)
        current = isqrt * self.corr
        return current

    def close(self):
        pass
