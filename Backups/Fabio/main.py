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

from sensor.reader import SensorReader, SensorController
from sensor.access_point import create_access_point, start_webserver

class WebServer:
    def __init__(self, wlan_ssid: str, wlan_pw: str):
        self.model_type = "Toms Pico"
        self.ssid = wlan_ssid
        self.pw = wlan_pw
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

    def __connect_to_wlan(self) -> str:
        """
        Funktion stellt WLAN-Verbindung her und liefert die IP Adresse des Servers zurueck.
        """
        if not self.wlan.isconnected():
            print('WLAN-Verbindung herstellen')
            self.wlan.active(True)
            self.wlan.connect(self.ssid, self.pw)
            for i in range(10):
                if self.wlan.status() < 0 or self.wlan.status() >= 3:
                    break
                print('.')
                time.sleep(1)
        if self.wlan.isconnected():
            print('WLAN-Verbindung hergestellt')
            netConfig = self.wlan.ifconfig()
            print('IPv4-Adresse:', netConfig[0])
            print()
            return netConfig[0]
        else:
            ipv4, subnetmask = create_access_point(essid="Test", password="password")
            start_webserver(ipv4)
            print('Keine WLAN-Verbindung')
            print('WLAN-Status:', wlan.status())
            print()
            return ''
    
    def __post_data(self, data_dict):
        try:
            res = requests.post(f"https://greenhouse-web.vercel.app/api/data", headers={"apiKey": f"{self.unique_id}"}, json=data_dict)
            res.close()
        except:
            return
        
    def start_measuring(self):
        while True:
            data_dict = self.reader.measure()
            print("="*24)
            print(f"Temperatur: {self.reader.data.temperature}")
            print(f"Luftfeuchtigkeit: {self.reader.data.humidity}")
            print(f"Distanz: {self.reader.data.distance}")
            print(f"Wasser leer: {self.reader.data.is_water_empty}")
            print(f"Bodenfeuchtigkeit 1: {self.reader.data.soil_humidity_1}")
            print(f"Bodenfeuchtigkeit 2: {self.reader.data.soil_humidity_2}")
            print(f"Bodenfeuchtigkeit 3: {self.reader.data.soil_humidity_3}")
            print(data_dict)
            self.controller.activate_needed_pumps()
            self.__post_data(data_dict)
            print("="*24)
            time.sleep(30)


"""# Dateiname der JSON-Datei
dateiname = "wifi_config.json"

# Öffnen der Datei und Lesen des Inhalts
with open(dateiname, "r") as datei:
    json_string = datei.read()

# Parsen des JSON-Strings
data = json.loads(json_string)

# Zugriff auf die Daten
WLAN_name= data["ssid"]
password= data["password"]"""


webserver = WebServer(wlan_ssid= "", wlan_pw= "")
webserver.start_measuring()