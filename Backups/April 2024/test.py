try:
    import usocket as socket  # importing socket
except:
    import socket
import network  # importing network
import gc
import ujson as json

gc.collect()
ssid = 'RPI_PICO_AP'  # Set access point name
password = '12345678'  # Set your access point password

ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)  # activating

html = """<!DOCTYPE html>
<html>
<head>
    <title>Wi-Fi Configuration</title>
    <style>
        body {
            background-color: #F5F5F5;
            font-family: Helvetica, Arial, sans-serif;
            text-align: center; /* Inhalte horizontal zentrieren */
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh; /* Die volle Höhe des Viewports einnehmen */
            margin: 0; /* entfernt den Standardabstand */
        }
        h1 {
            color: #008000;
            font-weight: bold;
            font-size: 4em; /* doppelt so groß */
            margin-top: 0; /* entfernt den Standardabstand */
            margin-bottom: 20px; /* mehr Platz nach unten */
        }
        input[type="text"], input[type="password"], input[type="submit"] {
            width: 600px; /* doppelt so breit */
            font-weight: bold;
            font-size: 3em; /* doppelt so groß */
            margin-bottom: 20px; /* mehr Platz nach unten */
            border: 1px solid #008000; /* Rahmen in der Farbe des Textes */
            padding: 10px; /* Platz um den Text innerhalb der Felder */
        }
        p {
            color: #008000;
            font-weight: bold;
            font-size: 3em; /* doppelt so groß */
            margin: 0; /* entfernt den Standardabstand */
            text-align: center; /* zentriert den Text */
            margin-bottom: 20px; /* mehr Platz nach unten */
        }
    </style>
</head>
<body>
    <div>
        <h1>Enter Wi-Fi Credentials</h1>
        <form action="/save" method="POST">
            <p>Network:</p>
            <input type="text" name="network"><br>
            <p>Password:</p>
            <input type="password" name="password"><br><br>
            <input type="submit" value="Submit">
        </form>
        <p id="message"></p>
    </div>

    <script>
        window.onload = function() {
            var form = document.querySelector('form');
            form.onsubmit = function(event) {
                event.preventDefault();
                var network = document.querySelector('input[name="network"]').value;
                var password = document.querySelector('input[name="password"]').value;
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '/save');
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.onload = function() {
                    if (xhr.status === 200) {
                        document.getElementById('message').textContent = 'Connection Successful!';
                    }
                };
                xhr.send('network=' + encodeURIComponent(network) + '&password=' + encodeURIComponent(password));
            };
        };
    </script>
</body>
</html>
"""


# Anfrageverarbeitung
def handle_request(request):
    try:
        if request.startswith("POST /save"):
            # Parse the request to extract network and password parameters
            params_start_index = request.find("network=")
            params_end_index = request.find("&password=")
            network = request[params_start_index + len("network="): params_end_index]
            password = request[params_end_index + len("&password="):]
            
            # Save the network and password to the JSON file
            save_wifi_config(network, password)
            
            # Connect to Wi-Fi (if needed)
            connect_to_wifi(network, password)
            
            # Return a success response
            return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
    except Exception as e:
        print("Exception:", e)
    
    # If an error occurs or the request doesn't match the expected format, return the HTML page
    return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html


def save_wifi_config(network, password):
    config = {'network': network, 'password': password}
    with open('wifi_config.json', 'w') as f:
        json.dump(config, f)


def connect_to_wifi(network, password):
    # Here goes the code to connect to Wi-Fi
    pass


while not ap.active():
    pass
print('Connection is successful')
print(ap.ifconfig())

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # creating socket object
s.bind(('', 80))
s.listen(5)

while True:
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    print('Content = %s' % str(request))
    response = handle_request(request.decode("utf-8"))  # Decode the request bytes to string
    conn.send(response)
    conn.close()
