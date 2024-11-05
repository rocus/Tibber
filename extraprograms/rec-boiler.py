#!/usr/bin/python3
import paho.mqtt.client as paho

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)
    client.subscribe("DenHaag/xxxxxxxxxxx/Boiler/out/#" , qos=1)

def on_publish(client, userdata, mid, properties=None):
    print("Publish mid: " + str(mid) )

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

f= open('log-boiler.txt', 'a')
def on_message(client, userdata, msg):
    line=msg.payload.decode()
    f.write(line+'\n')
    f.flush()

client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.username_pw_set("rjvoosten", "xxxxxxxxxx")
client.on_connect   = on_connect
client.on_subscribe = on_subscribe
client.on_message   = on_message
client.on_publish   = on_publish
client.connect("10.0.0.120", 1883)
client.loop_forever()
