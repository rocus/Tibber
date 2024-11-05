**GENERAL**

My goal was to create a device that can autonomously take advantage of variable electrical power rates, such as those from Tibber.com (i.e., the cheapest hours!). The starting point is that the device to be controlled can easily be turned on and off, that it should be turned on for a limited time during the day, and that it doesn't matter when during the day the device is turned on. One might think of:

- a water heater
- a dishwasher
- a washing machine
- a rechargeable car
- a rechargeable (bike) battery

The second and third cases present specific problems because such devices usually cannot be easily turned on as they are set up via software. I have therefore initially focused on the first case: a water heater (for which the simple rule is that applying voltage means heating (to the desired temperature), and turning off the power means not heating). 

I built the system (I call it a "Tibber timer") into an old (mechanical) timer clock because then I can easily plug it into a socket and the controlled device into the timer. For this purpose, a Dhiel Diletta/Multimat timer is perfectly suited. The mechanical clockwork was, of course, first removed; the original dial disk is replaced by a flat disk: in the middle of that disk, a small LED will be placed to provide information about the starting and functioning of the Tibber timer. I prefer this setup over a home automation solution because I don't need lamps that turn on automatically and other "smart" actions. (if you call "if this then this else that" smart)

The whole consists, besides the housing, of the following:

- a Raspberry Pi Pico with Wi-Fi
- a relay (for by example 2000 Watt)
- a Hall current sensor
- a small 5 Volt power supply

Wifi is needed to retrieve the hourly rates for the electrical power for the  following day from the Tibber.com website. I specifically chose Tibber because it has an excellent interface to their database. (no hassle with a webscrobbler)

The "Tibber timer" further communicates with the outside world via the MQTT protocol. It reports its functioning and offers the possibility to influence its operation (remotely), for example, if you want to override the start time of the connected device. The user is free to ignore the output. A user does not need to give commands either.
There are many ways to communicate with MQTT devices, for example, using Android MQTT apps. I use the output of the Tibber timer to create a log file of the controlled device. See below.

The current sensor measures the power used and thus also the savings by using the cheaper hours. With the current sensor, I also create a power profile of the device to be controlled, i.e., how long it is usually on. That also determines the most favorable moment for it to be turned on.

The power supply provides the Raspberry Pico and the relay with power from the 230 Volt.

**LOGFILE**

Below is a part of the logfile for my boiler:


2023-04-15  10:39:14 ============================\
2023-04-15  10:39:14 Starting Tibber program 1.33\
2023-04-15  10:39:14 ============================\
2023-04-15  10:39:14 Connected on Asus-EZA4\
2023-04-15  10:39:14 IP addresses 10.0.0.247 255.255.255.0 10.0.0.138 10.0.0.138\
2023-04-15  10:39:14 MQTT Commands from   DenHaag/xxxxxxxx/Boiler/in/#\
2023-04-15  10:39:14 MQTT Publications on DenHaag/xxxxxxxx/Boiler/out/#\
2023-04-15  10:39:14 Fetching Tibber data from site (in Eurocents)\
2023-04-15  10:39:17 Today    32.4 31.0 31.3 30.5 30.1 30.0 30.2 30.1 30.3 29.7 28.9 28.8\
26.8 19.2 17.5 24.8 26.2 29.4 31.0 33.5 33.7 32.9 32.9 31.9\
2023-04-15  10:39:19 Length tomorrow data 0\
2023-04-15  10:39:19 Tomorrow taken from today\
2023-04-15  10:39:19 Starts at 13:00 Stops at 17:00  ( 8460 22860 seconds)\
2023-04-15  10:39:19 Fetching again in 10 hours\
2023-04-15  13:01:15 Turning relais on\
2023-04-15  17:01:14 Turning relais off\
2023-04-15  20:39:19 Energy (kWh) in window: 2.300 and outside window: 0.000\
2023-04-15  20:39:19 Costs in window: 0.427 otherwise: 0.674\
2023-04-15  20:39:19 Mean tarif     : 0.293 profit   : 0.246\
2023-04-15  20:39:19 Fetching Tibber data from site (in Eurocents)\
2023-04-15  20:39:23 Today    32.4 31.0 31.3 30.5 30.1 30.0 30.2 30.1 30.3 29.7 28.9 28.8 26.8 19.2 17.5 24.8 26.2 29.4 31.0 33.5 33.7 32.9 32.9 31.9\
2023-04-15  20:39:26 Tomorrow 30.9 30.0 29.8 29.6 29.8 30.0 30.0 29.9 30.8 31.3 30.9 30.5
30.0 29.3 28.9 28.8 29.0 29.6 31.4 33.5 34.4 33.8 33.1 32.6\
2023-04-15  20:39:26 Starts at 14:00 Stops at 18:00  (62460 76860 seconds)\
2023-04-15  20:39:26 Fetching again in 24 hours\
2023-04-16  14:00:57 Turning relais on\
2023-04-16  18:00:57 Turning relais off\

**INSTALLATION**

The software of this project consists of some python files. some text files and a json file. You must upload the files to the raspberry pico. This can easily be done by THONNY (on your PC) and a usb cable to your raspberry pico. The json file is very important because it determines how the Tibber timer is configured and will work. 

The Json file consists of:

- wifi data
- mqtt data
- tibber data
- timeserver data
- devices data

Most data is obvious; the "devices data" needs some explanation:

- tibbertype:  can be NO, NC, AO, AC deteremines how the relais works
- initmode: can be tibberon. Anything else and the device will not automatically work
- relaispin: the pin that the relais is connected to
- ledpin: the pin of the pico on which the led is connected
- ledvalue: controls the blinking of the led
- ac712: data concerning this current measuring device
   - adcpin: the pico pin to which the analog out of the ac712 is connected
   - powercorr: a correction factor for the ac712
   - treshold: ignore power usage below this treshold


**CONNECTION**

The Tibber timer needs an usb port to connect the pico to your PC (running for example Thonny)

A small power supply is needed for the pico and the relais that turns your controlled device on and of. 

A small relais must be connected to the pico. The switched output of this relais must be used to switch on/off your device. A hall current sensor is connected in series with this relais. The relais must offcourse be up to the task to turn your device on and off. The used current sensor is not really necessary but can give you an idea of how much money is saved (don't expect to get rich). The sensor also measures how long your device is "normally" on: this is important to calculate the optimum time interval. The current sensor is not very accurate, therefore a correction factor and a treshold value in the json file.


**USAGE**

When you connect your Tibber timer to your power socket the first thing the program (main.py) does is reading your json file. About 8 steps are taken: after every step the led blinks once. If everything is OK the led will blink thereafter once every 15 seconds. If the device is turned on (in the following hours) the led will blink twice every 15 seconds. It is problably best to test the json file with the timer connected to your PC (and the Tibber timer not in a power socket). The MQTT output may also be helpfull in debugging the json file.


**OUTPUT**

The device gives status information about its functioning to the MQTT broker as defined in the json file. You can ignore this information but it may be helpfull. 

**INPUT**

You can give input commands to the device by means of MQTT commands. You can give these commands on your PC for example whith mqtt-explorer or in a linux shell with an appropriate command. The list of commands is in the help.txt file on your pico. This file shown with the command "help" given in for example in mqtt-explorer.

**BOOTLOG FILE**

The Tibber timer is supposed to run permanently: it does not need reboots. If it reboots (for whatever reason) this is written to the bootlog.txt file. When going on holiday you can turn off your device with the command: neveron. If your device reboots during a holiday wherein you don't want your device (for example a boiler) to work you can use the initmode : neveron line in the json file. After return from your holiday you can check the possible reboots and then turn your device on with the command: tibberon. you can see the status with the status command.

**OVERRULING THE TIBBER TIMER**

This all works a bit tricky. Two commands turndeviceon and turndeviceoff work in combination with the already set timer points (start and stop time). More easy is using the commands: alwayson and neveron. After using neveron you must issue the command tibberon.

**DIFFICULT DEVICES**

A boiler can often simply be turned on and off. Unfortunately many manifacturers think the world is waiting for there "smart" devices. At best you can turn such device simply on or off by means of a local offered website of the device. At worst they need your phone that doubles as a glorified remote control. Sometimes you can program your device at your convenience  and then , later , push a button. You could try to make the connection of this button yourself and connect this to the relais of your Tibber timer. Otherwise you can use a mechanical device to push this button (for example a fingerbot). If the manufacturer thinks he is really smart this button must be pushed shortly after the programming of the device (or the device goes to an error situation with a nice impressive error code). An other possibility is to use a doorlock for starting the device. That is by making or braking a wire in the doorlock (use the relais settings NO and NC). I use this method with my dishwasher. My washingmachine has no means to start it remotely but when the power is cut shortly after starting the machine it will later continue at that point.

**DAYLIGHT SAVING TIME**

The transition from summertime to wintertime does not go automatically (I found that unnecessary). If you give the settime command the time is corrected but at that day the turn on/off times will be an hour off. The next day everything should be OK.

**SPECIAL VERSIONS OF THE TIBBER TIMER**

I made two special versions of this device: one with a small TFT screen and one that will log the power usage of the attached device for one day to make a usage profile of the device. The one with the TFT screen has a better current measurement device and shows every minute the real and apparent power, phase angle and voltage/current. Because of space limitations there is no relais and the Tibber functionality is not present. 