# python-cold-air-pump
The python and sensor based system pumps cold outdoor air indoors for low energy cooling.

<img width="375" height="478" alt="cold-air-pump" src="https://github.com/user-attachments/assets/068981c3-e06c-4b3b-af77-d687b50a6908" />


I live in northern California where the weather is mild year around.  In the summer time, we have some days where the temperature reaches into the 80's and sometimes low 90's F.  It most always cools down to the high 50's or low 60's at night.  If one cools their dwelling at night, that is often enough to avoid having to resort of compressor based air conditioning the next day.  Cooling at night also is good for sleeping - my opinion - as is all of the rest.

In order to cool a dwelling with night air one needs to pump the cool air at night into the dwelling - hence our somewhat silly notion of a "cool pump".  This is a fan that blows cool outdoor air indoors.  The device and code look for a range of outdoor temperatures and pump air into the dwelling when those temperatures are lower than the indoor temperature.

The system uses two temperature sensors, a wifi controlled power switch, a fan, and python code running on most any computer that supports general purpose input and output (GPIO) devices.  An old laptop with a USB GPIO card or a Raspberry PI computer from the last decade both work well.  The python code spec:

  1. check indoor temperature > than some lower limit
     (we do not want to freeze things)
  2. check outdoor temperature in within a range
  3. check indoor temperature > outdoor temperature
  4. when 1 2 and 3 conditions are met turn on the window fan

The DS18B20 water resistent/waterproof temperature sensors are about $2 US each.  Variants of the SONOFF S31 WiFi controled power switches are in the $10 US range.  Window fans and computers are market rate as we all know.  The python code is free.

It is common to load a copy of the Tasmota operating system onto the WiFi based power switch.  Some power switches ship with a version of Tasmota or are configured to allow an over the air (OTA) download of it.  The python code here assumes one has a Tasmota configured power switch.  All of this produces a cloud and subscription free system.

The DS18B20 temperature sensors are connected to 3.3 volt power, ground, and GPIO data - I use GPIO pin 4.  There is a 4.7K resistor placed between power and data.  There is a third wire from the DS18B20 that of course goes to ground.  DS18B20 wiring for each device can be stacked next to each other.

For Raspberry PI's one has to add the one wire support.  Do this by adding:

  [all]
  dtoverlay=w1-gpio

to the bottom of /boot/firmware/config.txt and reboot.  After rebooting one can run the following and then check for 28* devices in /sys/bus/w1/devices.  The 28* devices are the temperature sensors:

  sudo modprobe w1-gpio
  sudo modprobe w1-therm

This python code loads the following libraries:

  import tkinter as tk
  from tkinter import ttk
  import threading
  import os
  import time
  import glob
  import requests

Run using:
  python cold-air-pump.py
<img width="375" height="478" alt="cold-air-pump" src="https://github.com/user-attachments/assets/e1773aa2-6850-45ed-b0b2-8ec0e311178e" />
