"""Class for reading sensor data

This class allows reading data of all available sensors and provides access to them via an additional class.


@Author: Fabio Rose
@Date: 13.09.2023
"""
import socket
from random import random
import network

from utime import sleep, sleep_us, ticks_us
from dht import DHT22
from machine import Pin, ADC, Timer
import time


class SensorData:
    """Class for keeping track of measured sensor data."""
    def __init__(self):
        self.temperature: float = None
        self.humidity: float = None
        self.distance: float = None
        self.is_water_empty: bool = None
        self.soil_humidity_1: float = None
        self.soil_humidity_2: float = None
        self.soil_humidity_3: float = None
    
class SensorReader:
    def __init__(self):
        self._led_onboard = Pin('LED', Pin.OUT, value=0)
        self._dht22_sensor = DHT22(Pin(14, Pin.IN, Pin.PULL_UP))
        self._plant_dist = Pin(6, Pin.OUT)
        self._CMS1      = ADC(Pin(26, Pin.IN))
        self._CMS2      = ADC(Pin(27, Pin.IN))
        self._CMS3      = ADC(Pin(28, Pin.IN))
        self._WLsens    = Pin(1, Pin.IN)
        self._trigger   = Pin(9, Pin.OUT)
        self._echo      = Pin(10, Pin.IN)
        self.data = SensorData()
    
    def _measure_temperature(self) -> None:
        """Measures temperature and stores it in data.temperature."""
        self._dht22_sensor.measure()
        self.data.temperature = self._dht22_sensor.temperature()
        
    def _measure_humidity(self) -> None:
        """Measures humidity and stores it in data.temperature."""
        self._dht22_sensor.measure()
        self.data.humidity = self._dht22_sensor.humidity()

    def _measure_is_water_empty(self) -> None:
        """Measures height of residual water in irrigation tank and stores it in data.water_level."""
        self.data.is_water_empty = bool(self._WLsens.value())
        
    def _measure_plant_dist(self) -> None:
        """Measures distance between top of plant and roof of tent and stores it in data.distance."""
        self.data.distance = 33.5
        
    def _measure_soil_humidity(self) -> None:
        """Measures soil humidity of three available sensors and stores them in
        data.soil_humidity_X where X denotes the index of the sensor.
        19000 = 100% humidity
        50000 =   0% humidity
        formel: 100 * (1 - (self._CMS3.read_u16() - 18500) / (50500 - 18500))
        """ 
        self.data.soil_humidity_1 = round(100 * (1 - (self._CMS1.read_u16() - 18500) / (50000 - 18500)),0)
        self.data.soil_humidity_2 = round(100 * (1 - (self._CMS2.read_u16() - 18500) / (50000 - 18500)),0)
        self.data.soil_humidity_3 = round(100 * (1 - (self._CMS3.read_u16() - 18500) / (50000 - 18500)),0)

    def measure(self, sensors = None) -> dict:
        """Collects measurements for every sensor and stores the collected values in data.
        Will additionally return a dictionary with sensor as key and measured values as value.
        """ 
        default_sensors = ["temperature",
                           "humidity",
                           "is_water_empty",
                           "distance",
                           "soil_humidity_1",
                           "soil_humidity_2",
                           "soil_humidity_3"]
        ret_dict = {sensor:-1 for sensor in default_sensors}
        if sensors is not None:
            if type(sensors) == str:
                sensors = [sensors]
        else:
            sensors = default_sensors
            
        for sensor in sensors:
            if sensor.lower() == "temperature":
                self._measure_temperature()
                ret_dict["temperature"] = self.data.temperature
            elif sensor.lower() == "humidity":
                self._measure_humidity()
                ret_dict["humidity"] = self.data.humidity
            elif sensor.lower() == "is_water_empty":
                self._measure_is_water_empty()
                ret_dict["is_water_empty"] = self.data.is_water_empty
            elif sensor.lower() == "distance":
                self._measure_plant_dist()
                ret_dict["distance"] = self.data.distance
            elif sensor.lower() == "soil_humidity_1":
                self._measure_soil_humidity()
                ret_dict["soil_humidity_1"] = self.data.soil_humidity_1
            elif sensor.lower() == "soil_humidity_2":
                ret_dict["soil_humidity_2"] = self.data.soil_humidity_2
            elif sensor.lower() == "soil_humidity_3":
                ret_dict["soil_humidity_3"] = self.data.soil_humidity_3
        return ret_dict

            
class SensorController():
    def __init__(self,reader):
        self._sensor_reader = reader
        self._pump1 = Pin(21, Pin.OUT, value=0)
        self._pump2 = Pin(20, Pin.OUT, value=0)
        self._pump3 = Pin(19, Pin.OUT, value=0)
        self._lamp = Pin(4, Pin.OUT)
        self._fan = Pin(5, Pin.OUT)
        self._emg_stop_pump1 = False
        self._emg_stop_pump2 = False
        self._emg_stop_pump3 = False
  
    def activate_pump(self, pump_pin):
        pump_pin.off()
      

    
    def activate_needed_pumps(self) -> None:
        """Aktiviert Pumpen, falls zugehörige Bodenfeuchtigkeit einen festegelegten Wert unterschreitet
           soilhumidity Werte: sehr nass ca. <20000; mäßig nass/optimal ca. 28000 - 32000; sehr trocken >50000 """

            
        # Überprüfen, ob der Wert von soilhumidity1 > 37000 und entsprechende Pumpe einschalten
        if self._sensor_reader.data.soil_humidity_1 < 50 and not self._emg_stop_pump1:
            self.activate_pump(self._pump1)
        else:
            self._pump1.on()

        # Überprüfen, ob der Wert von soilhumidity2 > 37000 und entsprechende Pumpe einschalten
        if self._sensor_reader.data.soil_humidity_2 < 50 and not self._emg_stop_pump2:
            self.activate_pump(self._pump2)
        else:
            self._pump2.on()

        # Überprüfen, ob der Wert von soilhumidity3 > 37000 und entsprechende Pumpe einschalten
        if self._sensor_reader.data.soil_humidity_3 < 50 and not self._emg_stop_pump3:
            self.activate_pump(self._pump3)
        else:
            self._pump3.on()
        
        time.sleep(10)
        
        self._pump1.on()
        self._pump2.on()
        self._pump3.on()
        
        self._sensor_reader.measure()
        
        if self._sensor_reader.data.soil_humidity_1 < 50:
            self._emg_stop_pump1 = True
            self._pump1.on()
            print("Bodenfeuchte-Sensor 1 defekt! Neustart des Geräts erforderlich!")
        if self._sensor_reader.data.soil_humidity_2 < 50:
            self._emg_stop_pump2 = True
            self._pump2.on()
            print("Bodenfeuchte-Sensor 2 defekt! Neustart des Geräts erforderlich!")
        if self._sensor_reader.data.soil_humidity_3 < 50:
            self._emg_stop_pump3 = True
            self._pump3.on()
            print("Bodenfeuchte-Sensor 3 defekt! Neustart des Geräts erforderlich!")
        
        
        