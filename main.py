import uasyncio as asyncio
import gc
import micropython
from uuurequests import post
from mydevice import Device
from json import load
from mqtt import MQTTClient
from sys import print_exception
from machine import Pin, reset, soft_reset
from time import localtime, sleep, gmtime
from wifi3 import connected_to_wlan, disconnect_from_wlan, connect_to_wlan, which_wlan, which_ssid
from myntp2 import settime
from power import add_power_data, mean_power_data, init_power_data, total_power_in_day

version_history = """
    1.75  garbage collection memory
    1.76  create array and empty it
    1.77  now more than 2 wifi access points
    1.78  dummy must also work for powermeter2
    1.79  multiple homes: postal code
    1.80  test sslcontext
    1.81  seperate help.txt and versions.txt
    1.82  modifications for HMM learn files.
    1.83  definitive 15-05-2024
    1.84  traindata in proper procedure
"""


version_nr = version_history.strip().split('\n')[-1].strip().split(' ')[0]


def current_time():
    s = '%3d-%02d-%02d  %2d:%02d:%02d ' % localtime()[0:6]
    return s


def writebootlog(msg):
    f = open("bootlog.txt", "a")
    f.write(current_time() + msg + '\n')
    f.close()


def readbootlog():
    try:
        f = open("bootlog.txt", "r")
    except Exception:
        f = open("bootlog.txt", "w")
    m = f.read()
    return m


def clearbootlog():
    f = open("bootlog.txt", "w")
    f.close()


debug          = False
# status         = 'neveron'
in_window      = False

wait_for_on    = None
wait_for_off   = None

tarif_today    = None
tarif_tomorrow = None

count_in  = 0
count_out = 0
mes_in    = 0
mes_out   = 0
costs_in  = 0
count     = 0

uptime    = 0


def minute(n=1):
    return n * 60


def hour(n=1):
    return n * 3600


def day(n=1):
    return n * 86400


# normally 3 hours would be OK, you can increase or decrease this array profile.
profile = [10.0, 5.0, 1.0]
max_on_hours = len(profile)


def calc_opt_start():
    global wait_for_on, wait_for_off
    opt = 10e6
    for i in range(0, 24):
        sum = 0.0
        for j in range(0, max_on_hours):
            if (i + j - max_on_hours) < 0:
                tar = tarif_today[i + j - max_on_hours + 24]
            else:
                tar = tarif_tomorrow[i + j - max_on_hours]
            sum += profile[j] * tar
        # print ( i , sum )
        if sum < opt:
            opt = sum
            he = i
    hb = he - max_on_hours

    time_now = localtime()
    if wait_for_on is not None or wait_for_off is not None:
        pub('Start and Stop time already determined.')
    else:
        if tarif_today == tarif_tomorrow:
            pass
        wait_for_on  = hour(hb - time_now[3]) - minute(time_now[4])
        wait_for_off = hour(he - time_now[3]) - minute(time_now[4])
        if hb < time_now[3] + 1:
            wait_for_on  += hour(24)
            wait_for_off += hour(24)
        elif wait_for_on > hour(24):
            wait_for_on  -= hour(24)
            wait_for_off -= hour(24)
        pub(f'Starts at {hb:2d}:00 Stops at {he:2d}:00  ({wait_for_on:5d} {wait_for_off:5d} seconds from now)')


def fetch_tibber_price(url, auth, post_code, s):
    global tarif_today, tarif_tomorrow, dummy
    import micropython

#   headers={'User-Agent': 'Mozilla/5.0'})
    headers = {'Authorization': auth, 'Content-Type': 'application/json', }
    json_data = {'query': '{viewer {homes {address { address1 , postalCode} ,currentSubscription {priceInfo {' + s + ' {total}}}}}}', }

    try:
        gc.collect()
        r = post(url, headers=headers, json=json_data)
        p = r.json()
        r.close()
        gc.collect()
        for i in p['data']['viewer']['homes']:
            if i['address']['postalCode'] == post_code:
                prices = i['currentSubscription']['priceInfo'][s]
        o = [d['total'] for d in prices]
        if len(o) == 23:    # from wintertime to summertime
            o.insert(2, o[2])
        elif len(o) == 25:  # from summertime to wintertime
            o.remove(o[2])
        if s == 'today':
            if len(o) == 24:
                tarif_today = o
                pub('Today    '    + ' '.join(str(round(100 * x, 1)) for x in tarif_today))
                return True
            else:
                return False
        elif s == 'tomorrow':
            if len(o) == 24:
                tarif_tomorrow = o
                pub('Tomorrow ' + ' '.join(str(round(100 * x, 1)) for x in tarif_tomorrow))
                return True
            else:
                pub('Length tomorrow data ' + str(len(o)))
                pub('Tomorrow taken from today')
                tarif_tomorrow = tarif_today
                return True

    except Exception as err:
        print_exception(err)
        micropython.mem_info(1)
        print('Exception in fetch_tibber price')
        return False


async def fetch_tibber_prices():
    global mes_in, mes_out, count_in, count_out, costs_in, secrets
    while True:
        pub('Fetching Tibber data from site (in Eurocents)')
        t = secrets['tibber']
        tdok = fetch_tibber_price(t['api_url'], t['auth'], t['post_code'], 'today')
        tmok = fetch_tibber_price(t['api_url'], t['auth'], t['post_code'], 'tomorrow')
        if tdok and tmok:
            calc_opt_start()
            again = (19 - localtime()[3] + 24) % 24  + 1  # every day at 19/20 o'clock
#            again =1
            pub('Fetching again in ' + str(again) + ' hours')
            await asyncio.sleep(hour(again))

            mean_tarif = 0.0
            for n in range(0, 24):
                mean_tarif += tarif_tomorrow[n]
            mean_tarif /= 24

            mes_in   /= 1000
            mes_out  /= 1000
            costs_in /= 1000

            pub(f'Energy (kWh) in window: {mes_in:.3f} and outside window: {mes_out:.3f}')
            pub(f'Costs in window: {costs_in:.3f} otherwise: {mes_in*mean_tarif:.3f}')
            pub(f'Mean tarif     : {mean_tarif:.3f} profit   : {mes_in*mean_tarif-costs_in:.3f}')
            mes_in    = 0
            mes_out   = 0
            count_in  = 0
            count_out = 0
            costs_in  = 0
        else:
            pub('Fetching Tibber data failed, trying again in 15 minutes')
            await asyncio.sleep(minute(15))

upload_in_progress = False
in_hash_sha256 = 0  # sha256()
bytes_in = 0
fout = 0


def upload(msg):
    from hashlib import sha256
    from ubinascii import hexlify
    from os import rename, remove

    global in_hash_sha256, bytes_in, upload_in_progress, fout
    if len(msg) == 200:
        msg_in = msg.decode("utf-8")
        msg_in = msg_in.split(",,")
        if msg_in[0] == "end":
            in_hash_final = hexlify(in_hash_sha256.digest())
            hash_received = bytes(msg_in[2], 'utf-8')
            # print ("bytes received ", bytes_in )
            if in_hash_final == hash_received:
                # print("File copied OK, valid hash, file name: ",msg_in[1])
                pub(f"File {msg_in[1]} copied OK, valid hash, {bytes_in} bytes.")
                fout.close()
                new_name = msg_in[1]
                try:
                    rename("temp", new_name)
                except FileExistsError:
                    pub("File already Exists; Removing existing file")
                    remove(new_name)
                    rename(old_name, new_name)
            else:
                pub("File copy failed")
                fout.close()
            upload_in_progress = False
            return True
        elif msg_in[0] == "header":
            pub("Upload starting...")
            in_hash_sha256 = sha256()
            bytes_in = 0
            fout = open("temp", "wb")
            upload_in_progress = True
            return True
        elif upload_in_progress:
            bytes_in = bytes_in + len(msg)
            in_hash_sha256.update(msg)
            fout.write(msg)
            return True
        else:
            return False
    elif upload_in_progress:
        bytes_in = bytes_in + len(msg)
        in_hash_sha256.update(msg)
        fout.write(msg)
        return True
    else:
        return False


def listdir(msg):
    filelist = (len(msg) > 8)
    s = 'Files on raspberry pico:\n'
    import os
    for filename in os.listdir():
        if (filename in msg) or not filelist:
            filedata = os.stat(filename)
            filetime = gmtime(filedata[7])
            t = '%3d-%02d-%02d  %2d:%02d:%02d ' % filetime[0:6]
            s = s + f'{filename:16} {filedata[6]:6}  {t}\n'
    pub(s)


def process_incoming_message(topic, msg):
    global tarif_today, tarif_tomorrow, profile, debug, tibber, status
    try:
        if upload(msg):
            pass
        elif b'intoday' in msg:
            tarif_today = msg.split(b',')
            tarif_today . pop(0)
            for i in range(0, 24):
                tarif_today[i] = float(tarif_today[i])
            pub('Tarif tomorrow set ' + ', '.join(str(x) for x in tarif_today))
        elif b'intomorrow' in msg:
            tarif_tomorrow = msg.split(b',')
            tarif_tomorrow . pop(0)
            for i in range(0, 24):
                tarif_tomorrow[i] = float(tarif_tomorrow[i])
            pub('Tarif today  set   ' + ', '.join(str(x) for x in tarif_tomorrow))
        elif b'inprofile' in msg:
            profil = msg.split(b',')
            profil . pop(0)
            for i in range(0, max_on_hours):
                profile[i] = float(profil[i])
            pub('Profile  set ' + ', '.join(str(x) for x in profile))
        elif msg == b'calc':
            if tarif_today is not None and tarif_tomorrow is not None:
                calc_opt_start()
        elif msg == b'stattod':
            if tarif_today is not None:
                pub('Today    ' + ' '.join(str(round(i * 100, 1)) for i in tarif_today))
        elif msg == b'stattom':
            if tarif_tomorrow is not None:
                pub('Tomorrow ' + ' '.join(str(round(i * 100, 1)) for i in tarif_tomorrow))
            else:
                pub('No tomorrow prices')
        elif msg == b'profile':
            pub('Profile ' + ', '.join(str(i) for i in profile))
        elif msg == b'uptime':
            pub(f'Uptime tibber device: {uptime:3d} days')
        elif msg == b'startstop':
            pub(f'Start Stop device: {wait_for_on} {wait_for_off}')
        elif msg == b'count':
            pub(f'Measurements device: {count_in:3d} {count_out:3d} Watthours: {round(mes_in):3d} {round(mes_out):3d}')
        elif msg == b'turndeviceon':
            tibber.turn_device_on()
            pub('Device turned on')
        elif msg == b'turndeviceoff':
            tibber.turn_device_off()
            pub('Device turned off')
        elif msg == b'isdeviceon':
            if tibber.device_on():
                pub('Device is on')
            else:
                pub('Device is off')
        elif msg == b'debug':
            debug = True
            pub('Debugging mode on')
        elif msg == b'settime':
            settime(secrets)
            pub('Internal time reset')
        elif msg == b'nodebug':
            debug = False
            pub('Debugging mode off')
        elif msg == b'reset':
            pub('Tibber device reset')
            sleep(3)
            writebootlog('Tibber device reset')
            reset()
        elif msg == b'softreset':
            pub('Tibber device softreset')
            sleep(3)
            writebootlog('Tibber device reset')
            soft_reset()
        elif msg == b'versions':
            pub('Tibber program version: ' + version_nr + version_history)
        elif msg == b'versionnr':
            pub('Tibber program version: ' + version_nr)
        elif msg == b'alwayson':
            status = 'alwayson'
            pub('Device permanently on')
            tibber.turn_device_on()
        elif msg == b'neveron':
            status = 'neveron'
            pub('Device permanently off')
            tibber.turn_device_off()
        elif msg == b'tibberon':
            status = 'tibberon'
            pub('Device controlled by Tibber device')
        elif msg == b'status':
            pub('Device controlled status: ' + status)
        elif msg == b'pulse':
            if status == 'tibberon':
                tibber.turn_device_on()
                pub('Device turned on for 7 seconds')
                sleep(7)
                tibber.turn_device_off()
                pub('Device turned off')
        elif b'meanpowerdata' in msg:
            d = mean_power_data()
            pub('Mean Power data: \n' + d)
        elif b'writebootlog' in msg:
            writebootlog(msg.decode())
        elif b'readbootlog' == msg:
            pub('Bootlog: \n' + readbootlog())
        elif b'clearbootlog' == msg:
            clearbootlog()
        elif b'whichwlan' == msg:
            pub('Wlan connected: ' + which_wlan()[0])
        elif b'whichssid' == msg:
            pub('Ssid connected: ' + which_ssid())
        elif b'comment' in msg:
            pub(msg.decode())
        elif b'listdir' in msg:
            listdir(msg.decode())
        elif msg == b'memory':
            pub(f'Memory free: {gc.mem_free()} allocated: {gc.mem_alloc()}')
            t = secrets['tibber']
            micropython.mem_info(1)
            tdok = fetch_tibber_price(t['api_url'], t['auth'], t['post_code'], 'today')
            micropython.mem_info(1)
            tmok = fetch_tibber_price(t['api_url'], t['auth'], t['post_code'], 'tomorrow')
            pub(f'Memory free: {gc.mem_free()} allocated: {gc.mem_alloc()}')
        elif msg == b'help':
            f = open("help.txt", "r")
            pub(f.read())
            f.close()
        else:
            pub('Unknown command: \"' + msg.decode() + '\"')
    except Exception as err:
        pub('Exception in command \"' + msg.decode() + '\" : ' + str(type(err)))


async def check_for_wifi():
    global secrets, client
    while True:
        print(current_time())
        if not connected_to_wlan():
            pub('Disconnected from wifi')
            disconnect_from_wlan()
            asyncio.sleep(10)
            connect_to_wlan(secrets["wifi"])
            pub('Reconnecting with wifi')
        await asyncio.sleep(minute(10))


async def check_for_incoming_messages():
    global client
    while True:
        try:
            client.check_msg()
#            p = client.check_msg()
#            client.ping()
            if client.msg != b'':
                process_incoming_message(client.tpc, client.msg)
                client.msg = b''
        except Exception as err:
            client.msg = b''
            print(f'Exception incoming messages {err=}, {type(err)=}')
            no_connection = True
            while no_connection:
                try:
                    await asyncio.sleep(minute(3))
                    print('Trying to subscribe to mqtt again')
                    pub('Trying to subscribe to mqtt again')
                    client = None
                    client = init_mqtt(m)
                    no_connection = False
                    pub('Client subscribed again')
                    print('Client subscribed again')
                except Exception:
                    print('Failed to subscribe')
        await asyncio.sleep(1)  # seconds


async def turn_device_on():
    global wait_for_on, count, tibber, in_window
    while True:
        if wait_for_on is None:
            await asyncio.sleep(minute(1))
        elif wait_for_on >= 0:
            await asyncio.sleep(wait_for_on)
            in_window = True
            wait_for_on = None
            count = 0
            if status != 'neveron':
                tibber.turn_device_on()
                pub('Turning device on ', )
        else:
            wait_for_on = None
            await asyncio.sleep(minute(1))


async def turn_device_off():
    global wait_for_off, status, tibber, in_window
    while True:
        if wait_for_off is None:
            await asyncio.sleep(minute(1))
        elif wait_for_off >= 0:
            await asyncio.sleep(wait_for_off)
            in_window = False
            wait_for_off = None
            if status != 'alwayson':
                tibber.turn_device_off()
                pub('Turning device off')
        else:
            wait_for_off = None
            await asyncio.sleep(minute(1))


async def measure_consumption():
    global count_in, count_out, mes_in, mes_out, profile, count, costs_in
    while True:
        try:
            d = measure_power()  # (voltage, current, power) / 60  # Watthour
            gc.collect()
            show_power(d)
            voltage = d["Voltage"]
            current = d["Current"]
            power   = d["Power"]
            add_power_data(voltage, current, power)
            mes = power / 60
            if debug:
                pub(f"Voltage {voltage} current {current} power {power}")
            if in_window:
                profile[count // 60] += mes   # below must be 1 minute
                count     += 1
                count_in  += 1
                mes_in    += mes
                costs_in  += mes * tarif_tomorrow[localtime()[3]]
            else:
                count_out += 1
                mes_out   += mes
        except Exception as err:
            pub(f'Exception in measure consumption {err=}, {type(err)=}')
            print_exception(err)
        await asyncio.sleep(minute(1))  # this must be 1 minute


def pub(s):
    global client, secrets
    try:
        client.publish(secrets['mqtt']['topic_out'], current_time() + s)
    except Exception as err:
        print_exception(err)
        print('Exception in pub ')


async def report_measurements():
    while True:
        i = 0 if count_in  == 0 else round(mes_in)
        o = 0 if count_out == 0 else round(mes_out)
        if debug:  # see version 1.36 and 1.52
            pub(f'Measurements counts {count_in:4d} {count_out:4d} . Watthours {i:4d} {o:4d}')
            pub('Profile ' + ', '.join(str(i) for i in profile))
        await asyncio.sleep(minute(10))


def init_mqtt(m):
    import random
    uid = str(random.getrandbits(32)) if len(m['uid']) == 0 else m['uid']
    client = MQTTClient(uid, m['url'], port=m['port'], keepalive=0)
    client.user = m['user']
    client.pswd = m['pswd']

    def cb(topic, msg):
        pass  # print ( topic , msg )
    client.set_callback(cb)
    client.connect(True)
    client.subscribe(m['topic_in'] + '/#', qos=1)
    return client


def traindata(nr):
    nm = '%2d:%02d:%02d ' % localtime()[3:6]
    fl = open(nm + ".txt", "w")
    fl.write(current_time())
    for i in range(nr):
        m = measure_power()
        show_power(m)
        fl.write(str(m['Power']) + '\n')
        if (i % 3600) == 0:
            fl.flush()
    fl.write(current_time())
    fl.close()


def blink_led(n=1):
    tm = 1 / (n + 1)
    for i in range(0, n):
        # print ("LED")
        statusled.toggle()
        sleep(tm)
        statusled.toggle()
        sleep(tm)


tasks = None


async def report_status():
    while True:
        j = 0
        for i in tasks:
            j += 1
            if i.done():
                print('Unexpected end of task ', j)
                writebootlog('Unexpected end of task ' + str(j))
                reset()
        if not connected_to_wlan():
            blink_led(4)
        elif tibber.device_on():
            blink_led(2)
        else:
            blink_led(1)
        await asyncio.sleep(10)


async def end_day_things():
    current_time = localtime()
    start_wait = day() - hour(current_time[3]) - minute(current_time[4]) - current_time[5] - 5
#    print ( current_time , start_wait)
    await asyncio.sleep(start_wait)
    while True:
        pub(f'Total power this day: {round(total_power_in_day()):5}')
        init_power_data()
        await asyncio.sleep(day())


async def main():
    global uptime, tasks
    tasks = [asyncio.create_task(check_for_wifi()),
             asyncio.create_task(check_for_incoming_messages()),
             asyncio.create_task(turn_device_on()),
             asyncio.create_task(turn_device_off()),
             asyncio.create_task(fetch_tibber_prices()),
             asyncio.create_task(measure_consumption()),
             asyncio.create_task(report_measurements()),
             asyncio.create_task(end_day_things()),
             asyncio.create_task(report_status())]
    while True:
        await asyncio.sleep(day())
        uptime += 1


try:
    f = open('secrets.json')
    secrets = load(f)

    d = secrets['devices']
    statusled = Pin(d['ledpin'], Pin.OUT, value=d['ledvalue'])
    blink_led(1)

    tibber    = Device(d['tibbertype'], d['relaispin'])  # tibberype can be NO, NC, AO, AC
    status    = 'tibberon' if d['initmode'] == 'tibberon' else 'neveron'
    blink_led(1)

    def dummy_measurement(*args):
        return {"Voltage": 0, "Current": 0, "Power": 0, "Energy": 0, "Freq": 0, "Pwr_fac": 0, "CRC": 0, "Alarm": 0}

    if "pzem004" in d:
        import readpzem
        measure_power = readpzem.measure_power
        readpzem.init(d["pzem004"])
    elif "ac712" in d:
        import readac712
        measure_power = readac712.measure_power
        readac712.init(d['ac712'])
    else:
        measure_power = dummy_measurement
    blink_led(1)

    if "st7735" in d:
        import writest7735
        show_power = writest7735.show_power
        writest7735.init(d["st7735"])
    else:
        show_power = dummy_measurement
    init_power_data()
    blink_led(1)

    if "wifi" not in secrets:
        while True:
            show_power(measure_power())

    connect_to_wlan(secrets["wifi"])
    blink_led(1)

    settime(secrets)
    blink_led(1)

    m = secrets['mqtt']
    client = init_mqtt(m)
    blink_led(1)

    s = 'Starting Tibber program ' + version_nr
    writebootlog(s)
    print(s)
    pub(' ')
    pub('=' * len(s))
    pub(s)
    pub('=' * len(s))
    pub('Connected on SSID ' + which_ssid())
    pub('IP address  is    ' + which_wlan()[0])
    pub('Gateway is        ' + which_wlan()[2])
    pub('MQTT server is    ' + m['url'])
    pub('MQTT Commands     ' + m['topic_in'] + '/#')
    pub('MQTT Publications ' + m['topic_out'] + '/#')
    blink_led(1)

    if "traindata" in secrets:
        traindata(secrets["traindata"])

    asyncio.run(main())

except Exception as err:
    print_exception(err)
    sleep(20)
    blink_led(6)
    disconnect_from_wlan()
    tibber.turn_device_off()
    writebootlog(f'Exception in initialization {err=}, {type(err)=}')
    soft_reset()

except KeyboardInterrupt:
    disconnect_from_wlan()
    tibber.turn_device_off()
