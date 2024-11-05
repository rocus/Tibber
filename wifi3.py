import network
from time import sleep
from machine import reset

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)
ip = ''
ssid = ''


def connect_to_wlan(w):
    global wlan, ip, ssid
    for s in w:
        wlan.connect(s["ssid"], s["password"])
        counter = 1
        while not connected_to_wlan() and counter < 4:
            print('Waiting for connection...', s["ssid"], counter)
            sleep(3)
            counter += 1
        ip = wlan.ifconfig()[0]
        ssid = s["ssid"]
        if counter == 4 or ip == '0.0.0.0' or wlan.status() != 3:
            disconnect_from_wlan()
        else:
            print(ssid, " ", wlan.ifconfig())
            print(f'Connected on {ip}')
            return
    print("No wifi connection made")
    reset()


def which_wlan():
    global wlan
    return wlan.ifconfig()


def which_ssid():
    global ssid
    return ssid


def disconnect_from_wlan():
    global wlan
    wlan.disconnect()


def connected_to_wlan():
    global wlan
    return wlan.isconnected()
