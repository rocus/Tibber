import machine as machine
import urequests as requests
# import json


def setRTCntpserver():
    import ntptime
    import time
    ntptime.settime()
    print("Get time from ntp server, CET assumed.")
    print(time.localtime())
    year = time.localtime()[0]       # get current year
    HHMarch   = time.mktime((year, 3,  (31 - (int(5 * year / 4 + 4)) % 7), 1, 0, 0, 0, 0, 0))  # Time of March change to CEST
    HHOctober = time.mktime((year, 10, (31 - (int(5 * year / 4 + 1)) % 7), 1, 0, 0, 0, 0, 0))  # Time of October change to CET
    now = time.time()
    if now < HHMarch:                     # we are before last sunday of march
        cet = time.localtime(now + 3600)  # CET:  UTC+1H
    elif now < HHOctober:                 # we are before last sunday of october
        cet = time.localtime(now + 7200)  # CEST: UTC+2H
    else:                                 # we are after last sunday of october
        cet = time.localtime(now + 3600)  # CET:  UTC+1H
    tm = cet
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))


def setRTCtimeserver(m):
    url = m["api_url"] + m["location"]
    response = requests.get(url)
    a = response.json()[m["time_str"]]
    response.close()
    print("Get time from ", url)
    print(a)
    date = a.split('T')[0].split('-')
    time = a.split('T')[1].split(':')
    sec = time[2].split('.')[0]
    machine.RTC().datetime((int(date[0]), int(date[1]), int(date[2]), + 1, int(time[0]), int(time[1]), int(sec), 0))


def settime(s):
    try:
        m = s["timeserver1"]
        setRTCtimeserver(m)
    except Exception:
        try:
            m = ["timeserver2"]
            setRTCtimeserver(m)
        except Exception:
            try:
                setRTCntpserver()
            except Exception:
                pass
