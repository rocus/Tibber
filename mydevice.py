from machine import Pin


class Device:

    device_is_on = False

    def __init__(self, typ, relaispin):
        self.relais = Pin(relaispin, Pin.OUT, value=0)
        self.typ = typ
        if typ == 'AO' or typ == 'NO':
            self.relais.off()
            # print ( 'relais off')
        elif typ == 'AC' or typ == 'NC':
            self.relais.on()
            # print ( 'relais on')
        # print ('deviceinit' , self.device_is_on )

    def turn_device_on(self):
        if self.typ == 'NO':
            # print ( 'relais turned on' )
            self.relais.on()
        elif self.typ == 'NC':
            # print ( 'relais turned off' )
            self.relais.off()
        self.device_is_on = True

    def turn_device_off(self):
        if self.typ == 'NO':
            # print ( 'relais turned off' )
            self.relais.off()
        elif self.typ == 'NC':
            # print ( 'relais turned on' )
            self.relais.on()
        self.device_is_on = False

    def device_on(self):
        return self.device_is_on

    def device_off(self):
        return not self.device_is_on
