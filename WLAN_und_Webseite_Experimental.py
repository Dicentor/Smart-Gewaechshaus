# Bibliotheken laden
from machine import Pin, ADC
import network
import utime as time
from utime import sleep, sleep_us, ticks_us
import socket
from dht import DHT22


class WebServer:
    def __init__(self, wlan_ssid: str, wlan_pw: str):
        # WLAN-Konfig hinterlegen
        self.ssid = wlan_ssid
        self.pw = wlan_pw
        self.wlan = network.WLAN(network.STA_IF)
        self.ip = self.__connect_to_wlan()
        self.controller = SensorController()
        self.html = """<!doctype html>
            <html lang="en">

            <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="shortcut icon" href="data:">
            <title>Raspberry Pi Pico</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Oswald&display=swap');
                
                *{
                    padding:0;
                    margin:0;
                    min-height:100%;
                    min-width:100%;
                }

                body {
                    background: linear-gradient(to bottom, black, green);
                    background-size: 100% 200%;
                    animation: gradientAnimation 5s linear infinite;
                    color: #fff;
                    font-family: 'Oswald', Arial, sans-serif;
                    position: relative;
                }

                @keyframes gradientAnimation {
                    0% {
                        background-position: 0% 100%;
                    }
                    50% {
                        background-position: 100% 0%;
                    }
                    100% {
                        background-position: 0% 100%;
                    }
                }

                h1 {
                text-align: center;
                color: #00ff00;
                font-size: 36px;
                }

                hr {
                border: none;
                border-top: 2px solid #00ff00;
                margin: 20px 0;
                }

                p {
                text-align: center;
                font-size: 24px;
                }

                b {
                color: #00ff00;
                }
            </style>
            </head>

            <body>
            <h1>Smart Gewächshaus</h1>
            <hr>
            <p><b>Temperatur:</b> <span id="temperature">TEMPERATURE</span> °C</p>
            <p><b>Luftfeuchtigkeit:</b> <span id="humidity">HUMIDITY</span> % RH</p>
            <hr>
            <p>Deine Mama riecht nach Maggi</p>

            <script type="text/javascript">
        setInterval(function() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/temperature", true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    document.getElementById('temperature').textContent = xhr.responseText;
                }
            };
            xhr.send();

            var xhr2 = new XMLHttpRequest();
            xhr2.open("GET", "/humidity", true);
            xhr2.onreadystatechange = function() {
                if (xhr2.readyState === 4 && xhr2.status === 200) {
                    document.getElementById('humidity').textContent = xhr2.responseText;
                }
            };
            xhr2.send();
        }, 24000);
    </script>
            </body>

            </html>
         """
        network.country("DE")
    
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
            print('Keine WLAN-Verbindung')
            print('WLAN-Status:', wlan.status())
            print()
            return ''
    
    def start_server(self) -> None:
        """
        Startet den HTTP-Server und verarbeitete einkommende Anfragen
        """
        if self.ip == '':
            raise ValueError("Server wurde keine IP-Adresse zugeordnet")
        print('Server starten')
        addr = socket.getaddrinfo(self.ip, 80)[0][-1]
        server = socket.socket()
        server.bind(addr)
        server.listen(1)
        print('Server hört auf', addr)
        print()
        print('Beenden mit STRG + C')
        print()
        while True:
            print(self.controller.data.soilhumidity1)
            try:
                conn, addr = server.accept()
                print('HTTP-Request von Client', addr)
                request = conn.recv(1024)
                #print('Request:', request)
                request = str(request)
                request = request.split()
                print('URL:', request[1])
                # Sensor abfragen
                self.controller.measure_soilhumidity()
                self.controller.measure_dht22()
                self.controller.test_method()
                # URL auswerten
                if request[1] == '/temperature':
                    response = str(self.controller.data.temperature)
                elif request[1] == '/humidity':
                    response = str(self.controller.data.humidity)
                else:
                    # Daten formatieren: Nachkommastellen kürzen und Punkt gegen Komma tauschen
                    temperature = '{:.2f}'.format(self.controller.data.temperature).replace('.',',')
                    humidity = str(self.controller.data.humidity).replace('.',',')
                    # Daten für Response aufbereiten
                    response = self.html
                # HTTP-Response senden
                conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                conn.send(response)
                conn.close()
                print('HTTP-Response gesendet')
                print()
            except OSError as e:
                print(e)
                break
            except (KeyboardInterrupt):
                break
        try: 
            conn.close()
        except NameError: pass
        try:
            server.close()
            print('Server beendet')
        except NameError as e:
            print(e)

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
        self.CMS1      = ADC(Pin(26, Pin.IN))
        self.CMS2      = ADC(Pin(27, Pin.IN))
        self.CMS3      = ADC(Pin(28, Pin.IN))
        self.trigger_P = Pin(9, Pin.OUT)
        self.echo_P    = Pin(10, Pin.IN)
        self.trigger_W = Pin(11, Pin.OUT)
        self.echo_W    = Pin(12, Pin.IN)
        self.test      = Pin(13, Pin.OUT)
        # Objekt zum speichern der ausgelesenen Werte
        self.data = SensorData()
    
    def test_method(self) -> None:
        self.test.on()
       
    
    def measure_dht22(self) -> None:
        # Messung durchführen
        self.dht22_sensor.measure()
        # Werte lesen und in Datenobjekt ablegen
        self.data.temperature = self.dht22_sensor.temperature()
        self.data.humidity = self.dht22_sensor.humidity()

    def measure_distance(self) -> None:
        """Misst die Distanz der Pflanzen zu den Lampen. Gemessenen Wert wird in Datenobjekt hinterlegt"""
        timepassed, signalon, signaloff = self.__measure_time(self.trigger_P, self.echo_P)
        # Abstand/Entfernung ermitteln
        # Entfernung über die Schallgeschwindigkeit (34320 cm/s bei 20 °C) berechnen
        # Durch 2 teilen, wegen Hin- und Rückweg
        self.data.distance = timepassed * 0.03432 / 2
        self.__print_stats(signalon, signaloff, timepassed, self.data.distance)
    
    def measure_waterlevel() -> None:
        """Misst die Distanz zum Wasserspiegel. Gemessenen Wert wird in Datenobjekt hinterlegt"""
        timepassed, signalon, signaloff = self.__measure_time(self.trigger_W, self.echo_W)
        # Abstand/Entfernung ermitteln
        # Entfernung über die Schallgeschwindigkeit (34320 cm/s bei 20 °C) berechnen
        # Durch 2 teilen, wegen Hin- und Rückweg
        self.data.waterlevel = timepassed * 0.03432 / 2
        self.__print_stats(signalon, signaloff, timepassed, self.data.waterlevel)
    
    def __measure_time(self, trigger: Pin, echo: Pin) -> float:
        """Misst Zeit zwischen Signalen und liefert die gemessene Zeit zurück"""
        trigger.low()
        sleep_us(2)
        trigger.high()
        sleep_us(5)
        trigger.low()
        # Zeit messen
        while echo.value() == 0:
            signaloff = ticks_us()
        while echo.value() == 1:         
            signalon = ticks_us()
        return signalon - signaloff, signalon, signaloff
    
    def __print_stats(signalon, signaloff, timepassed, value) -> None:
        """Gibt Ergebnisse als print in Konsole aus"""
        print(
            f"Off    : {signaloff}\n",
            f"On     : {signalon}\n",
            f"Zeit   : {timepassed}\n",
            f"Abstand: {value:.2f}cm\n"
        )
    
    def measure_soilhumidity(self) -> None:
        """Misst die Bodenfeuchtigkeit. Gemessenen Wert wird in Datenobjekt hinterlegt"""
        self.data.soilhumidity1 = self.CMS1.read_u16()
        self.data.soilhumidity2 = self.CMS2.read_u16()
        self.data.soilhumidity3 = self.CMS3.read_u16()
    
    def activate_needed_pumps(self) -> None:
        """Aktiviert Pumpen, falls zugehörige Bodenfeuchtigkeit einen festegelegten Wert unterschreitet"""
        # Überprüfen, ob der Wert von soilhumidity1 kleiner als 20000 ist und entsprechende Pumpe einschalten
        if self.data.soilhumidity1 < 20000:
            self.pump1.on()
        else:
            self.pump1.off()

        # Überprüfen, ob der Wert von soilhumidity2 kleiner als 20000 ist und entsprechende Pumpe einschalten
        if self.data.soilhumidity2 < 20000:
            self.pump2.on()
        else:
            self.pump2.off()

        # Überprüfen, ob der Wert von soilhumidity3 kleiner als 20000 ist und entsprechende Pumpe einschalten
        if self.data.soilhumidity3 < 20000:
            self.pump3.on()
        else:
            self.pump3.off()
    def measure_distance_loop(self) -> None:
        while True:
            self.measure_distance()
            sleep(1)

    def measure_waterlevel_loop(self) -> None:
        while True:
            self.measure_waterlevel()
            sleep(1)

    def measure_soilhumidity_loop(self) -> None:
        while True:
            self.measure_soilhumidity()
            sleep(1)

    def activate_needed_pumps_loop(self) -> None:
        while True:
            self.activate_needed_pumps()
            sleep(1)

    def start_sensor_loops(self) -> None:
        # Starte die Sensor-Loops in separaten Threads
        import _thread
        _thread.start_new_thread(self.measure_distance_loop, ())
        _thread.start_new_thread(self.measure_waterlevel_loop, ())
        _thread.start_new_thread(self.measure_soilhumidity_loop, ())
        _thread.start_new_thread(self.activate_needed_pumps_loop, ())


webserver = WebServer(wlan_ssid="Whyfi", wlan_pw="YiStillTheMain69")
webserver.start_server()