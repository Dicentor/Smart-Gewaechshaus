from machine import Pin, ADC
import network
import utime as time
import json
import urequests as requests

from sensor.reader import SensorReader, SensorController
import sensor.access_point as AP

class FirestoreClient:
    def __init__(self, project_id, api_key):
        self.project_id = project_id
        self.api_key = api_key
        self.firestore_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/sensorData"

    def send_data(self, collection, document_id, data):
        """Sendet Daten an Firestore."""
        url = f"{self.firestore_url}/{document_id}?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        document = {
            "fields": {
                "temperature": {"doubleValue": data["temperature"]},
                "humidity": {"doubleValue": data["humidity"]},
                "is_water_empty": {"booleanValue": data["is_water_empty"]},
                "soil_humidity_1": {"doubleValue": data["soil_humidity_1"]},
                "soil_humidity_2": {"doubleValue": data["soil_humidity_2"]},
                "soil_humidity_3": {"doubleValue": data["soil_humidity_3"]},
                "ip_address": {"stringValue": data["ip_address"]}
            }
        }
        try:
            response = requests.put(url, headers=headers, json=document)
            response.close()
            if response.status_code == 200:
                print("Daten erfolgreich an Firestore gesendet.")
            else:
                print(f"Fehler: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Fehler beim Senden der Daten an Firestore: {e}")

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
        self.firestore = FirestoreClient("smart-ge", "AIzaSyCKIVEfYPhQC7VTECZ8r4dbIXS9JbOIdIA")
        print(f"RaspberryPi Board-ID: {self.unique_id}")
        print(f"Modelltyp: {self.model_type}")
        network.country("DE")
        
    def __get_board_id(self) -> str:
        """Retrieves unique pico board identifier."""
        return ''.join(hex(b)[2:] for b in machine.unique_id())

    def __check_wlan_connection(self):
        if self.ssid == "" or self.pw == "":
            netconfig, wap = AP.create_access_point(password="12345678")
            AP.start_webserver(netconfig[0], self.wlan, wap)
        else:
            self.wlan.active(True)
            self.wlan.connect(self.ssid, self.pw)
            for _ in range(5):
                if self.wlan.isconnected():
                    return 
                time.sleep(1)
            netconfig, wap = AP.create_access_point(password="12345678")
            AP.start_webserver(netconfig[0], self.wlan, wap)

    def __connect_to_wlan(self) -> str:
        """Funktion stellt WLAN-Verbindung her und liefert die IP Adresse des Servers zurück."""
        self.__check_wlan_connection()
        print("Connection established")
        print(self.wlan.status())
        return self.wlan.ifconfig()[0]
    
    def __send_data_to_firestore(self, data_dict):
        """Sendet die Sensordaten an Firestore."""
        document_id = f"sensor-{self.unique_id}"
        self.firestore.send_data("sensorData", document_id, data_dict)
        
    def start_measuring(self):
        while True:
            data_dict = self.reader.measure()
            data_dict["ip_address"] = self.wlan.ifconfig()[0]
            print("="*24)
            print(f"Temperatur: {self.reader.data.temperature}")
            print(f"Luftfeuchtigkeit: {self.reader.data.humidity}")
            print(f"Wasser leer: {self.reader.data.is_water_empty}")
            print(f"Bodenfeuchtigkeit 1: {self.reader.data.soil_humidity_1}")
            print(f"Bodenfeuchtigkeit 2: {self.reader.data.soil_humidity_2}")
            print(f"Bodenfeuchtigkeit 3: {self.reader.data.soil_humidity_3}")
            print(f"IP-Adresse: {self.wlan.ifconfig()[0]}")
            self.controller.activate_needed_pumps()
            self.__send_data_to_firestore(data_dict)
            print("="*24)
            time.sleep(30)

webserver = WebServer()
webserver.start_measuring()
