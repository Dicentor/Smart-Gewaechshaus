# Bibliotheken laden
from machine import Pin, ADC
import network
import utime as time
from utime import sleep, sleep_us, ticks_us
import socket
from dht import DHT22
import urequests
import ujson

# Funktion zum Senden einer Push-Benachrichtigung
def send_push_notification(message):
    url = "https://fcm.googleapis.com/fcm/send"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "key=YOUR_SERVER_KEY"
    }
    data = {
        "to": "YOUR_DEVICE_TOKEN",
        "notification": {
            "title": "Smart Gewächshaus",
            "body": message
        }
    }
    response = urequests.post(url, json=data, headers=headers)
    print(response.text)
    response.close()

# WLAN-Konfiguration
wlanSSID = 'Whyfi'
wlanPW = 'YiStillTheMain69'
network.country('DE')

# Initialisierung: Status-LED
led_onboard = Pin('LED', Pin.OUT, value=0)

# Initialisierung GPIOs, Aktorik und Sensorik
time.sleep(1)
dht22_sensor = DHT22(Pin(15, Pin.IN, Pin.PULL_UP))
pump1     = Pin(1, Pin.OUT)
pump2     = Pin(2, Pin.OUT)
pump3     = Pin(3, Pin.OUT)
lamp      = Pin(4, Pin.OUT)
fan       = Pin(5, Pin.OUT)
CMS1      = ADC(Pin(26, Pin.IN))
CMS2      = ADC(Pin(27, Pin.IN))
CMS3      = ADC(Pin(28, Pin.IN))
trigger_P = Pin(9, Pin.OUT)
echo_P    = Pin(10, Pin.IN)
trigger_W = Pin(11, Pin.OUT)
echo_W    = Pin(12, Pin.IN)

# HTML-Datei
html = """<!doctype html>
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
  <p><b>Bodenfeuchte:</b> <span id="soil_moisture">SOIL_MOISTURE</span></p>
  <hr>
  <p>Deine Mama riecht nach Maggi</p>

  <script type="text/javascript">
    setInterval(function() {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open("GET", "http://192.168.0.57/temperature", false); // false for synchronous request
        xmlHttp.send(null);
        document.getElementById('temperature').textContent = xmlHttp.responseText;
        xmlHttp.open("GET", "http://192.168.0.57/humidity", false); // false for synchronous request
        xmlHttp.send(null);
        document.getElementById('humidity').textContent = xmlHttp.responseText;
        console.log(xmlHttp.responseText);
    }, 24000);
</script>
</body>

</html>
"""

#"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="shortcut icon" href="data:"><title>Raspberry Pi Pico</title></head><body><h1 align="center">Smart Gewächshaus</h1><hr><p><b>Temperatur:</b> TEMPERATURE °C</p><p><b>Luftfeuchtigkeit:</b> HUMIDITY % RH</p><hr><p align="center">Deine Mama riecht nach Maggi</p></body></html>"""
# Funktion: DHT22 abfragen
def dht22Measure():
    global temperature, humidity
    # Messung durchführen
    dht22_sensor.measure()
    # Werte lesen
    temperature = dht22_sensor.temperature()
    humidity = dht22_sensor.humidity()

def get_soil_moisture():
    global soil_moisture1
    soil_moisture1 = CMS1.read_u16()
    return soil_moisture1
    

def distance():
    global distance, lamp_too_low
     # Abstand messen
    trigger_P.low()
    sleep_us(2)
    trigger_P.high()
    sleep_us(5)
    trigger_P.low()
    # Zeitmessungen
    while echo_P.value() == 0:
       signaloff = ticks_us()
    while echo_P.value() == 1:         
       signalon = ticks_us()
    # Vergangene Zeit ermitteln
    timepassed = signalon - signaloff
    # Abstand/Entfernung ermitteln
    # Entfernung über die Schallgeschwindigkeit (34320 cm/s bei 20 °C) berechnen
    # Durch 2 teilen, wegen Hin- und Rückweg
    distance = timepassed * 0.03432 / 2
    # Ergebnis ausgeben
    print('    Off:', signaloff)
    print('     On:', signalon)
    print('   Zeit:', timepassed)
    print('Abstand:', str("%.2f" % distance), 'cm')
    print()
    # Überprüfen, ob der Abstand kleiner als 15 cm ist
    if distance < 15:
        lamp_too_low = True
    else:
        lamp_too_low = False
    
    
def waterlevel():
    global waterlevel, waterempty
     # Abstand messen
    trigger_W.low()
    sleep_us(2)
    trigger_W.high()
    sleep_us(5)
    trigger_W.low()
    # Zeitmessungen
    while echo_W.value() == 0:
       signaloff = ticks_us()
    while echo_W.value() == 1:         
       signalon = ticks_us()
    # Vergangene Zeit ermitteln
    timepassed = signalon - signaloff
    # Abstand/Entfernung ermitteln
    # Entfernung über die Schallgeschwindigkeit (34320 cm/s bei 20 °C) berechnen
    # Durch 2 teilen, wegen Hin- und Rückweg
    waterlevel = timepassed * 0.03432 / 2
    # Ergebnis ausgeben
    print('    Off:', signaloff)
    print('     On:', signalon)
    print('   Zeit:', timepassed)
    print('Abstand:', str("%.2f" % waterlevel), 'cm')
    print()
    # Überprüfen, ob der Abstand kleiner als 15 cm ist
    if waterlevel < 15:
        waterempty = True
    else:
        waterempty = False
    # 3 Sekunde warten
    sleep(3)
    
def soilhumidity():
    global soilhumidity1, soilhumidity2, soilhumidity3
    soilhumidity1 = CMS1.read_u16()
    soilhumidity2 = CMS2.read_u16()
    soilhumidity3 = CMS3.read_u16()
    
    # Überprüfen, ob der Wert von soilhumidity1 kleiner als 20000 ist und entsprechende Pumpe einschalten
    if soilhumidity1 < 20000:
        pump1.on()
    else:
        pump1.off()

    # Überprüfen, ob der Wert von soilhumidity2 kleiner als 20000 ist und entsprechende Pumpe einschalten
    if soilhumidity2 < 20000:
        pump2.on()
    else:
        pump2.off()

    # Überprüfen, ob der Wert von soilhumidity3 kleiner als 20000 ist und entsprechende Pumpe einschalten
    if soilhumidity3 < 20000:
        pump3.on()
    else:
        pump3.off()
    print(soilhumidity1)
        
def fan():
     if temperature > 30 or humidity > 50:
        fan.on()
     else:
        fan.off()
        

        

    
        
# Funktion: WLAN-Verbindung
def wlanConnect():
    import network
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print('WLAN-Verbindung herstellen')
        wlan.active(True)
        wlan.connect(wlanSSID, wlanPW)
        for i in range(10):
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            print('.')
            time.sleep(1)
    if wlan.isconnected():
        print('WLAN-Verbindung hergestellt')
        netConfig = wlan.ifconfig()
        print('IPv4-Adresse:', netConfig[0])
        print()
        return netConfig[0]
    else:
        print('Keine WLAN-Verbindung')
        print('WLAN-Status:', wlan.status())
        print()
        return ''

# WLAN-Verbindung herstellen
ipv4 = wlanConnect()

# HTTP-Server starten
if ipv4 != '':
    print('Server starten')
    addr = socket.getaddrinfo(ipv4, 80)[0][-1]
    server = socket.socket()
    server.bind(addr)
    server.listen(1)
    print('Server hört auf', addr)
    print()
    print('Beenden mit STRG + C')
    print()
# Auf eingehende Verbindungen hören
while True:
    try:
        conn, addr = server.accept()
        time.sleep(2)
        print('HTTP-Request von Client', addr)
        request = conn.recv(1024)
        #print('Request:', request)
        request = str(request)
        request = request.split()
        print('URL:', request[1])
        # Sensor abfragen
        soil_moisture = get_soil_moisture()
        dht22Measure()
        # URL auswerten
        if request[1] == '/temperature':
            response = str(temperature)
        elif request[1] == '/humidity':
            response = str(humidity)
        else:
            # Daten formatieren: Nachkommastellen kürzen und Punkt gegen Komma tauschen
            temperature = '{:.2f}'.format(temperature).replace('.',',')
            humidity = str(humidity).replace('.',',')
            # Daten für Response aufbereiten
            response = html
            response = response.replace('TEMPERATURE', temperature)
            response = response.replace('HUMIDITY', humidity)
            response = response.replace('SOIL_MOISTURE', str(soil_moisture))
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

try: conn.close()
except NameError: pass
try:
    server.close()
    print('Server beendet')
except NameError as e:
    print(e)