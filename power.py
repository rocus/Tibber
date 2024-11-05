from time import localtime

power_data = []


def init_power_data():
    global power_data
    power_data = []
    for x in range(24):
        power_data.append([0, 0.0, 0.0, 0.0])


def total_power_in_day():
    wh = 0
    for x in range(24):
        p = power_data[x]
        if p[0] > 0:
            wh += p[3] / p[0]
    return wh


def add_power_data(voltage, current, power):
    current_hour = localtime()[3]
    p = power_data[current_hour]
    p[0] += 1
    p[1] += voltage
    p[2] += current
    p[3] += power


def mean_power_data():
    d = 'Nr Hour Voltage Current Power'
    for i in range(24):
        p = power_data[i]
        n = p[0]
        if n != 0:
            mean_voltage = p[1] / n
            mean_current = p[2] / n
            mean_power   = p[3] / n
            s = f'{n:2d} {i:2d}:00 {round(mean_voltage):5d}{round(mean_current):7d}{round(mean_power):7d}'
            d = d + '\n' + s
    d = d + f'\nEnergy used this day: {round(total_power_in_day()):5d} Wattuur'
    return d
