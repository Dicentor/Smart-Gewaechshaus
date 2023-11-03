# Bibliotheken laden
from machine import Pin, ADC, Timer
import network
import utime as time
from utime import sleep, sleep_us, ticks_us
import socket
from dht import DHT22

class SensorData:
    def __init__(self):
        self.temperature = None
        self.humidity = None
        self.distance = None
        self.waterlevel = None
        self.soilhumidity1 = None
        self.soilhumidity2 = None
        self.soilhumidity3 = None
    
    def is_lamp_too_low(self) -> bool:
        """Liefert True, falls die gemessene Distanz zu den Pflanzen kleiner als 15cm ist"""
        return self.distance < 15
    
    def is_water_empty(self) -> bool:
        """Liefert True, falls die gemessene Distanz zum Wasser kleiner als 15cm ist"""
        return self.waterempty < 15


class SensorController:
    def __init__(self):
        self.led_onboard = Pin('LED', Pin.OUT, value=0)
        self.dht22_sensor = DHT22(Pin(15, Pin.IN, Pin.PULL_UP))
        self.pump1     = Pin(1, Pin.OUT)
        self.pump2     = Pin(2, Pin.OUT)
        self.pump3     = Pin(3, Pin.OUT)
        self.lamp      = Pin(4, Pin.OUT)
        self.fan       = Pin(5, Pin.OUT)
        self.plantdist = Pin(6, Pin.OUT)
        self.CMS1      = ADC(Pin(26, Pin.IN))
        self.CMS2      = ADC(Pin(27, Pin.IN))
        self.CMS3      = ADC(Pin(28, Pin.IN))
        self.CMS4      = ADC(Pin(29, Pin.IN))
        self.trigger   = Pin(9, Pin.OUT)
        self.echo      = Pin(10, Pin.IN)
        self.pump1_timer = Timer()
        self.pump2_timer = Timer()
        self.pump3_timer = Timer()
        self.max_pump_runtime = 6  # Maximale Laufzeit der Pumpe in Sekunden (hier: 10 Minuten)
        # Objekt zum speichern der ausgelesenen Werte
        self.data = SensorData()
    
    def measure_dht22(self) -> None:
        # Messung durchführen
        self.dht22_sensor.measure()
        # Werte lesen und in Datenobjekt ablegen
        self.data.temperature = self.dht22_sensor.temperature()
        self.data.humidity = self.dht22_sensor.humidity()

    
    def measure_waterlevel(self) -> None:
        self.data.waterlevel = CMS4.read_u16()
        
    
    def measure_plantdist(self) -> None:
       
        # Abstand messen
        self.trigger.low()
        sleep_us(2)
        self.trigger.high()
        sleep_us(5)
        self.trigger.low()
        # Zeitmessungen
        while self.echo.value() == 0:
           signaloff = ticks_us()
        while self.echo.value() == 1:         
           signalon = ticks_us()
        # Vergangene Zeit ermitteln
        timepassed = signalon - signaloff
        # Abstand/Entfernung ermitteln
        # Entfernung über die Schallgeschwindigkeit (34320 cm/s bei 20 °C) berechnen
       # Durch 2 teilen, wegen Hin- und Rückweg
        abstand = timepassed * 0.03432 / 2
        self.data.distance = abstand
        
  
    
    
    def measure_soilhumidity(self) -> None:
        """Misst die Bodenfeuchtigkeit. Gemessenen Wert wird in Datenobjekt hinterlegt"""
        self.data.soilhumidity1 = self.CMS1.read_u16()
        self.data.soilhumidity2 = self.CMS2.read_u16()
        self.data.soilhumidity3 = self.CMS3.read_u16()
    
    def activate_pump(self, pump_pin, timer):
        pump_pin.on()
        timer.init(mode=Timer.ONE_SHOT, period=self.max_pump_runtime * 1000, callback=self.stop_pump)

    def stop_pump(self, timer):
        pump_pins = [self.pump1, self.pump2, self.pump3]
        for index, pump_pin in enumerate(pump_pins):
            if timer is pump_pin:
                pump_pin.off()
                if timer is self.pump1_timer:
                    print("Warnung: Pumpe 1 hat die maximale Laufzeit überschritten!")
                    # Hier kannst du eine spezifische Warnungsaktion ausführen
    
    def activate_needed_pumps(self) -> None:
        """Aktiviert Pumpen, falls zugehörige Bodenfeuchtigkeit einen festegelegten Wert unterschreitet
           soilhumidity Werte: sehr nass ca. <20000; mäßig nass/optimal ca. 28000 - 32000; sehr trocken >50000 """

            
        # Überprüfen, ob der Wert von soilhumidity1 > 37000 und entsprechende Pumpe einschalten
        if self.data.soilhumidity1 < 50:
            self.activate_pump(self.pump1, self.pump1_timer)
        else:
            self.pump1.off()

        # Überprüfen, ob der Wert von soilhumidity2 > 37000 und entsprechende Pumpe einschalten
        if self.data.soilhumidity2 < 50:
            self.activate_pump(self.pump2, self.pump2_timer)
        else:
            self.pump2.off()

        # Überprüfen, ob der Wert von soilhumidity3 > 37000 und entsprechende Pumpe einschalten
        if self.data.soilhumidity3 < 50:
            self.activate_pump(self.pump3, self.pump3_timer)
        else:
            self.pump3.off()
    
    
    def print_sensor_data(self) -> None:
        print("Soil Humidity 1:", self.data.soilhumidity1)
        print("Soil Humidity 2:", self.data.soilhumidity2)
        print("Soil Humidity 3:", self.data.soilhumidity3)
        print("Distanz", self.data.distance)
        print("Lufttemperatur", self.data.temperature)
        print("Luftfeuchte", self.data.humidity)
  
    def start_printing_data(self) -> None:
        while True:
            self.measure_dht22()
            self.measure_soilhumidity()
            self.measure_plantdist()
            self.activate_needed_pumps()
            self.activate_light()
            self.print_sensor_data()  # Wert von CMS1 drucken
            sleep(10)  # 4 Sekunden warten
instance = SensorController()
instance.start_printing_data()
  

        