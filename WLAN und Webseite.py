# Bibliotheken laden
from machine import Pin
import network
import utime as time
import socket
from dht import DHT22

# WLAN-Konfiguration
wlanSSID = 'Whyfi'
wlanPW = 'YiStillTheMain69'
network.country('DE')

# Initialisierung: Status-LED
led_onboard = Pin('LED', Pin.OUT, value=0)

# Initialisierung GPIO und DHT22
time.sleep(1)
dht22_sensor = DHT22(Pin(15, Pin.IN, Pin.PULL_UP))

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
        print('HTTP-Request von Client', addr)
        request = conn.recv(1024)
        #print('Request:', request)
        request = str(request)
        request = request.split()
        print('URL:', request[1])
        # Sensor abfragen
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
