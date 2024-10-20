"""Class for handling connection to API.

This class uses the SensorReader from sensor.reader to read sensor data and send read data
to API for visualization inside a web dashboard.


@Author: Fabio Rose
@Date: 03.10.2023
"""

from machine import Pin, ADC
import network
import utime as time
import socket
import os
import urequests as requests
import json
import time

sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)
sta_if.active(True)
ap_if.active(False)

from sensor.reader import SensorReader, SensorController
import sensor.access_point as AP

class WebServer:
    def __init__(self):
        self.model_type = "Toms Pico"
        with open("/wifi_config.json") as file:
            credentials = json.load(file)
        self.ssid = credentials["ssid"]
        self.pw = credentials["password"]
        self.wlan = network.WLAN(network.STA_IF)
        self.ip = self.__connect_to_wlan()
        self.reader = SensorReader()
        self.controller = SensorController(self.reader)
        self.unique_id = self.__get_board_id()
        print(f"RaspberryPi Board-ID: {self.unique_id}")
        print(f"Modelltyp: {self.model_type}")
        network.country("DE")
        
    def __get_board_id(self) -> str:
        """Retrieves unique pico board identifier."""
        id = ""
        for b in machine.unique_id():
            id += hex(b)[2:]
        return id
    
    """def __read_pi_config(self) -> dict:
        with open("identifier.json") as f:
            data = json.load(f)
        self.model_type = data["model_type"]"""

    def __check_wlan_connection(self):
        # create access point if no credentials are provided
        if self.ssid == "" or self.pw == "":
            netconfig, wap = AP.create_access_point(password="12345678")
            AP.start_webserver(netconfig[0], self.wlan, wap)
        else:
            # try if connection is possible
            self.wlan.active(True)
            self.wlan.connect(self.ssid, self.pw)
            for _ in range(5):
                # return from method if connection is established
                if self.wlan.isconnected():
                    return 
                time.sleep(1)
            # otherwise create access point
            netconfig, wap = AP.create_access_point(password="12345678")
            AP.start_webserver(netconfig[0], self.wlan, wap)

    def __connect_to_wlan(self) -> str:
        """
        Funktion stellt WLAN-Verbindung her und liefert die IP Adresse des Servers zurueck.
        """
        # this method will create an access point if no credentials are provided OR if the connection to the wifi network fails
        # the access point then will trigger a restart if credentials are provided by the user 
        self.__check_wlan_connection()
        # therefor code from here on is only executed if a connection is established
        print("Connection established")
        print(self.wlan.status())
        return self.wlan.ifconfig()[0]
    
    def __post_data(self, data_dict):
        try:
            res = requests.post(f"https://greenhouse-web.vercel.app/api/data", headers={"apiKey": f"{self.unique_id}"}, json=data_dict)
            res.close()
        except:
            return
        
    def start_measuring(self):
        while True:
            data_dict = self.reader.measure()
            data_dict['ip_address'] = self.wlan.ifconfig()[0]
            print("="*24)
            print(f"Temperatur: {self.reader.data.temperature}")
            print(f"Luftfeuchtigkeit: {self.reader.data.humidity}")
            print(f"Wasser leer: {self.reader.data.is_water_empty}")
            print(f"Bodenfeuchtigkeit 1: {self.reader.data.soil_humidity_1}")
            print(f"Bodenfeuchtigkeit 2: {self.reader.data.soil_humidity_2}")
            print(f"Bodenfeuchtigkeit 3: {self.reader.data.soil_humidity_3}")
            print(f"IP-Adresse: {self.wlan.ifconfig()[0]}")
            print(f"EMG_P1: : {self.reader.data.emg_stop_pump1}")
            print(f"EMG_P2: : {self.reader.data.emg_stop_pump2}")
            print(f"EMG_P3: : {self.reader.data.emg_stop_pump3}")
            print(data_dict)
            self.controller.activate_needed_pumps()
            self.__post_data(data_dict)
            print("="*24)
            time.sleep(30)


webserver = WebServer()
webserver.start_measuring()