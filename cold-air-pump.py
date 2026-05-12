"""
cold-air-pump.py: Original work Copyright (C) 2026 by Blewett

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Softxware, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

The system pumps cold outdoor air indoors.  The system uses two
temperature sensors, a wifi controlled power switch, a fan, and python
code running on most any computer that supports general purpose input
and output (GPIO) devices.  An old laptop with a USB GPIO card or a
Raspberry PI computer from the last decade both work well.

and other words like that.

"""

#
# Tasmota commands for Fauf device
#
# comands seem to be backwards Off turns on, On turns off
#
# http://TASMOTA_IP_DEF/cm?cmnd=Power%20Off
# http://TASMOTA_IP_DEF/cm?cmnd=Power%20On
#
#

import tkinter as tk
from tkinter import ttk
import random
import threading
import os
import time
import glob
import requests

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')
devices = []

# only two
i = 0
for dev in device_folder:
    devices.append(dev + "/w1_slave")
    i += 1
    if i > 1:
        break

def is_decimal_string(s):
    periods = False
    ret = False

    for c in s:
        if c == '.':
            if periods:
                return False
            periods = True
            continue

        if ord(c) < ord("0") or ord(c) > ord("9"):
            return False

        ret = True

    return ret

def read_temp_sensor(dev):
    while True:
        time.sleep(0.2)
        f = open(dev, 'r')
        lines = f.readlines()
        f.close()

        if len(lines) > 1:
            line = lines[0].strip()
        else:
            continue

        if line[-3:] != 'YES':
            continue
        else:
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                return float(temp_string) / 1000.0
            else:
                continue

class ProcessTempSensors:
    def __init__(self, root, ip_address):

        self.ip_address = ip_address

        self.root = root
        self.root.resizable(False, False)
        
        # Variables to hold the values
        self.indoor_display_var = tk.StringVar(value="")
        self.target_indoor_var = tk.StringVar(value="60")
        self.indoor_max_var = tk.StringVar(value="0")
        self.outdoor_display_var = tk.StringVar(value="")
        self.outdoor_min_var = tk.StringVar(value="50")
        self.outdoor_max_var = tk.StringVar(value="80")
        
        # Control flag for the monitoring thread
        self.running = False
        self.monitoring = False
        self.manual = False
        self.temp_running = True
        self.f_indoor = "0.0"
        self.f_outdoor = "0.0"
        self.state = False
        self.state_message = "The state is off"

        #
        self.create_widgets()

        # Start the thread for reading temp sensors
        self.temp_update_thread = threading.Thread(target=self.temp_read_values, daemon=True)
        self.temp_update_thread.start()

    def create_widgets(self):
        self.root = root
        self.root.title("Cold Air Pump: Fan Controler")

        # controler frame
        controler_frame = ttk.Frame(self.root)
        controler_frame.grid(row=0, column=0, padx=20, pady=20)
        
        # controler status frame
        controler_status_frame = ttk.LabelFrame(controler_frame, text="Controler status")
        controler_status_frame.grid(row=0, column=2, padx=5, pady=5)

        # Indoor Input Field
        indoor_frame = ttk.Frame(controler_status_frame)
        indoor_frame.grid(row=0, column=2, padx=5, pady=5)
        
        indoor_label = ttk.Label(indoor_frame, text="Indoor temp:")
        indoor_label.grid(row=0, column=1)

        self.indoor_entry = ttk.Entry(indoor_frame, textvariable=self.indoor_display_var)
        self.indoor_entry.grid(row=0, column=2)
        
        # Outdoor Input Field
        outdoor_frame = ttk.Frame(controler_status_frame)
        outdoor_frame.grid(row=1, column=2, padx=5, pady=5)
        
        outdoor_label = ttk.Label(outdoor_frame, text="Outdoor temp:")
        outdoor_label.grid(row=1, column=1)

        self.outdoor_entry = ttk.Entry(outdoor_frame, textvariable=self.outdoor_display_var)
        self.outdoor_entry.grid(row=1, column=2)
        
        # Start Monitoring Button
        self.monitoring_start_button = ttk.Button(controler_status_frame, text="Start monitoring", 
                                       command=self.toggle_monitoring)
        self.monitoring_start_button.grid(row=2, column=2)
        
        # Status label
        self.status_label = ttk.Label(controler_status_frame,
                                      text="Click start to monitoring", 
                                      foreground="gray")
        self.status_label.grid(row=3, column=2)
    
        # state label
        self.state_label = ttk.Label(controler_status_frame,
                                     text=self.state_message, 
                                     foreground="gray")
        self.state_label.grid(row=4, column=2, pady=5)
    

        min_max_frame = ttk.LabelFrame(controler_frame, text="Target indoor temp and outdoor range")
        min_max_frame.grid(row=1, column=2, padx=5, pady=15)
        
        # Target indoor input Field2
        target_indoor_frame = ttk.Frame(min_max_frame)
        target_indoor_frame.grid(row=1, column=2, padx=5, pady=5)
        
        target_indoor_label = ttk.Label(target_indoor_frame, text="Target Indoor:")
        target_indoor_label.grid(row=0, column=1)

        self.target_indoor_entry = ttk.Entry(target_indoor_frame, textvariable=self.target_indoor_var)
        self.target_indoor_entry.grid(row=0, column=2)
        
        # Outdoor min Input Field2
        outdoor_min_frame = ttk.Frame(min_max_frame)
        outdoor_min_frame.grid(row=2, column=2, padx=5, pady=5)
        
        outdoor_min_label = ttk.Label(outdoor_min_frame, text="Outdoor min:")
        outdoor_min_label.grid(row=1, column=1)

        self.outdoor_min_entry = ttk.Entry(outdoor_min_frame, textvariable=self.outdoor_min_var)
        self.outdoor_min_entry.grid(row=1, column=2)
        
        # OUTDOOR max Input Field2
        outdoor_max_frame = ttk.Frame(min_max_frame)
        outdoor_max_frame.grid(row=3, column=2, padx=5, pady=5)
        
        outdoor_max_label = ttk.Label(outdoor_max_frame, text="Outdoor max:")
        outdoor_max_label.grid(row=1, column=1)

        self.outdoor_max_entry = ttk.Entry(outdoor_max_frame, textvariable=self.outdoor_max_var)
        self.outdoor_max_entry.grid(row=1, column=2)
        
        # Manual start Button
        self.manual_start_button = ttk.Button(controler_frame,
                                              text="Start manual mode", 
                                              command=self.toggle_manual)
        self.manual_start_button.grid(row=6, column=2)
        

    def set_tasmota_power(self, state):
        # Basic command (most common)
        # url = f"http://{self.ip_address}/cm?cmnd=Power%20Off"
        # user=admin&password=yourpassword&cmnd=Power%20On
        # url = f"http://{self.ip_address}/cm?cmnd=Status%200"
        url = f"http://{self.ip_address}/cm?cmnd=Status"

        # BACKWARDS
        if state == False:
            url = f"http://{self.ip_address}/cm?cmnd=Power%20On"
        else:
            url = f"http://{self.ip_address}/cm?cmnd=Power%20Off"

        try:
            response = requests.get(url, timeout=5)
            """
            if response.status_code == 200:
                print("✅ Power ON command sent successfully!")
                print("Response:", response.text)
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(response.text)
            """
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")


    def set_state(self, value):
        if value == self.state:
            return

        self.state = value

        color = "grey"
        if value:
            self_state_message = "The state is on"
            color = "green"
        else:
            self_state_message = "The state is off"

        self.state_label.config(text=self_state_message, foreground=color)
        self.set_tasmota_power(value)

    def temp_read_values(self):
        while self.temp_running:
            i = 0
            for dev in devices:
                # check if there are more than two devices
                if i >= 2:
                    break
                c = read_temp_sensor(dev)
                f = (c * 9.0/5.0) + 32.0
                f = round(f, 2)
                # c = round(c, 2)
                if i == 0:
                    self.f_indoor = f
                else:
                    self.f_outdoor = f
                i += 1

            if self.monitoring == True:
                self.monitor_values()

            self.indoor_display_var.set(str(self.f_indoor))
            self.outdoor_display_var.set(str(self.f_outdoor))

            # Wait 0.5 seconds
            time.sleep(0.5)
    
    def toggle_monitoring(self):
        if self.monitoring == False:
            # Start monitoring
            if self.manual == True:
                self.toggle_manual()
            self.monitoring = True
            self.monitoring_start_button.config(text="Stop monitoring")
            self.status_label.config(text="Monitoring every 0.5 seconds...", foreground="green")
        else:
            # Stop monitoring
            if self.state:
                self.set_state(False)
            self.monitoring = False
            self.monitoring_start_button.config(text="Start monitoring")
            self.status_label.config(text="Click start to monitoring", foreground="gray")

    def toggle_manual(self):
        if self.monitoring == True:
            self.toggle_monitoring()

        if self.manual:
            self.manual = False
            self.manual_start_button.config(text="Start manual mode")
        else:
            self.manual = True
            self.manual_start_button.config(text="Stop manual mode")

        self.set_state(self.manual)
    
    def monitor_values(self):
        if self.monitoring == False:
            return

        target_indoor = self.target_indoor_var.get()
        outdoor_min = self.outdoor_min_var.get()
        outdoor_max = self.outdoor_max_var.get()

        if is_decimal_string(target_indoor) == False:
            self.status_label.config(text=f"The Indoor temp is not a temperature", foreground="red")
            return

        if is_decimal_string(outdoor_min) == False:
            self.status_label.config(text=f"The Outdoor min is not a temperature", foreground="red")
            self.set_state(False)
            return

        if is_decimal_string(outdoor_max) == False:
            self.status_label.config(text=f"The Outdoor max is not a temperature", foreground="red")
            self.set_state(False)
            return

        if self.f_indoor < float(target_indoor):
            self.status_label.config(text=f"{self.f_indoor} is below the the target indoor temp", foreground="red")
            self.set_state(False)
            return

        if self.f_outdoor < float(outdoor_min):
            self.status_label.config(text=f"{self.f_outdoor} is below the outdoor min.", foreground="red")
            self.set_state(False)
            return

        if self.f_outdoor > float(outdoor_max):
            self.status_label.config(text=f"{self.f_outdoor} is above the outdoor max.", foreground="red")
            self.set_state(False)
            return

        status = self.f_indoor > self.f_outdoor
        if status == True:
            self.status_label.config(text="Monitoring: indoor > outdoor", foreground="green")
        else:
            self.status_label.config(text="Monitoring: indoor < outdoor", foreground="green")

        self.set_state(status)
    
    def on_closing(self):
        self.running = False  # Stop the thread gracefully
        self.root.destroy()


if __name__ == "__main__":
    TASMOTA_IP_DEF = your tasmota ip address here
    root = tk.Tk()
    app = ProcessTempSensors(root, TASMOTA_IP_DEF)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
