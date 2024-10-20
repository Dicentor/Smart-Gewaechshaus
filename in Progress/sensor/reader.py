      
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
        self.is_water_empty: bool = None
        self.soil_humidity_1: float = None
        self.soil_humidity_2: float = None
        self.soil_humidity_3: float = None
        self.emg_stop_pump1: bool = False
        self.emg_stop_pump2: bool = False
        self.emg_stop_pump3: bool = False


class SensorReader:
    def __init__(self):
        self._led_onboard = Pin('LED', Pin.OUT, value=0)
        self._dht22_sensor = DHT22(Pin(14, Pin.IN, Pin.PULL_UP))
        self._plant_dist = Pin(6, Pin.OUT)
        self._CMS1 = ADC(Pin(26, Pin.IN))
        self._CMS2 = ADC(Pin(27, Pin.IN))
        self._CMS3 = ADC(Pin(28, Pin.IN))
        self._WLsens = Pin(1, Pin.IN)
        self._trigger = Pin(9, Pin.OUT)
        self._echo = Pin(10, Pin.IN)
        self.data = SensorData()

    def _measure_temperature(self) -> None:
        """Measures temperature and stores it in data.temperature."""
        self._dht22_sensor.measure()
        self.data.temperature = self._dht22_sensor.temperature()

    def _measure_humidity(self) -> None:
        """Measures humidity and stores it in data.humidity."""
        self._dht22_sensor.measure()
        self.data.humidity = self._dht22_sensor.humidity()

    def _measure_is_water_empty(self) -> None:
        """Measures height of water in irrigation tank and stores it in data.is_water_empty."""
        self.data.is_water_empty = bool(self._WLsens.value())


    def _measure_soil_humidity(self) -> None:
        """Measures soil humidity and stores it in data.soil_humidity_1, soil_humidity_2, and soil_humidity_3."""
        def clamp(value, min_value, max_value):
            return max(min_value, min(value, max_value))

        humidity_1 = round(100 * (1 - (self._CMS1.read_u16() - 18500) / (50000 - 18500)), 0)
        self.data.soil_humidity_1 = clamp(humidity_1, 0, 100)

        humidity_2 = round(100 * (1 - (self._CMS2.read_u16() - 18500) / (50000 - 18500)), 0)
        self.data.soil_humidity_2 = clamp(humidity_2, 0, 100)

        humidity_3 = round(100 * (1 - (self._CMS3.read_u16() - 18500) / (50000 - 18500)), 0)
        self.data.soil_humidity_3 = clamp(humidity_3, 0, 100)

    def measure(self, sensors=None) -> dict:
        """Collects measurements for every sensor and stores the collected values in data.
        Will additionally return a dictionary with sensor as key and measured values as value.
        """ 
        default_sensors = ["temperature",
                           "humidity",
                           "is_water_empty",
                           "soil_humidity_1",
                           "soil_humidity_2",
                           "soil_humidity_3",
                           "emg_stop_pump1",
                           "emg_stop_pump2",
                           "emg_stop_pump3"]
        ret_dict = {sensor: -1 for sensor in default_sensors}
            # Standardwerte für Not-Aus-Sensoren explizit setzen
        ret_dict["emg_stop_pump1"] = self.data.emg_stop_pump1
        ret_dict["emg_stop_pump2"] = self.data.emg_stop_pump2
        ret_dict["emg_stop_pump3"] = self.data.emg_stop_pump3
        
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
            elif sensor.lower() == "soil_humidity_1":
                self._measure_soil_humidity()
                ret_dict["soil_humidity_1"] = self.data.soil_humidity_1
            elif sensor.lower() == "soil_humidity_2":
                self._measure_soil_humidity()
                ret_dict["soil_humidity_2"] = self.data.soil_humidity_2
            elif sensor.lower() == "soil_humidity_3":
                self._measure_soil_humidity()
                ret_dict["soil_humidity_3"] = self.data.soil_humidity_3
        
        return ret_dict

class SensorController:
    def __init__(self, reader):
        self._sensor_reader = reader
        self._pump1 = Pin(21, Pin.OUT, value=0)
        self._pump2 = Pin(20, Pin.OUT, value=0)
        self._pump3 = Pin(19, Pin.OUT, value=0)
        self._lamp = Pin(4, Pin.OUT)
        self._fan = Pin(5, Pin.OUT)

    def get_emergency_stop_status(self):
        """Returns the emergency stop status of each pump as a dictionary."""
        return {
            "emg_stop_pump1": self._sensor_reader.data.emg_stop_pump1,
            "emg_stop_pump2": self._sensor_reader.data.emg_stop_pump2,
            "emg_stop_pump3": self._sensor_reader.data.emg_stop_pump3
        }

    def activate_pump(self, pump_pin):
        pump_pin.off()

    def activate_needed_pumps(self) -> None:
        """Aktiviert Pumpen, falls zugehörige Bodenfeuchtigkeit einen festgelegten Wert unterschreitet."""
        
        # Pumpe 1
        if not self._sensor_reader.data.emg_stop_pump1:
            if self._sensor_reader.data.soil_humidity_1 < 50:
                self.activate_pump(self._pump1)
            else:
                self._pump1.on()

        # Pumpe 2
        if not self._sensor_reader.data.emg_stop_pump2:
            if self._sensor_reader.data.soil_humidity_2 < 50:
                self.activate_pump(self._pump2)
            else:
                self._pump2.on()

        # Pumpe 3
        if not self._sensor_reader.data.emg_stop_pump3:
            if self._sensor_reader.data.soil_humidity_3 < 50:
                self.activate_pump(self._pump3)
            else:
                self._pump3.on()

        time.sleep(30)

        # Turn off pumps after sleep
        self._pump1.on()
        self._pump2.on()
        self._pump3.on()

        # Perform sensor measurement
        self._sensor_reader.measure()

        # Check for emergency stop conditions and set them permanently to True if triggered
        if self._sensor_reader.data.soil_humidity_1 < 50:
            self._sensor_reader.data.emg_stop_pump1 = True  # Once set to True, it will stay True
            self._pump1.on()
            print("Bodenfeuchte-Sensor 1 defekt! Neustart des Geräts erforderlich!")

        if self._sensor_reader.data.soil_humidity_2 < 50:
            self._sensor_reader.data.emg_stop_pump2 = True  # Once set to True, it will stay True
            self._pump2.on()
            print("Bodenfeuchte-Sensor 2 defekt! Neustart des Geräts erforderlich!")

        if self._sensor_reader.data.soil_humidity_3 < 50:
            self._sensor_reader.data.emg_stop_pump3 = True  # Once set to True, it will stay True
            self._pump3.on()
            print("Bodenfeuchte-Sensor 3 defekt! Neustart des Geräts erforderlich!")
