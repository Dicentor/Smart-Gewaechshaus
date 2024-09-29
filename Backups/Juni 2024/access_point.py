import network
import socket
import ure
import utime
import ussl
import json

def create_access_point(password: str, essid: str = "Smart-GH") -> tuple[str, str]:
    """
    Creates a publicly visible acces point with provided essid as displayed name
    and password for authentification of incoming connection requests.

    Parameters
    ----------
    essid : str, optional
        Name of the created acces point, publicly visible (Default: 'Smart-GH').
    password : str
        Password for authentification
        
    Returns
    -------
    tuple of str
        IPv4 address and subnetmask of the created access point
    
    Notes
    -----
    After running this method, the acces point will stay active on the raspberry pi. No keep alive
    is needed.
    """
    # Configuration of WLan-AccessPoint
    wap = network.WLAN(network.AP_IF)
    wap.config(essid=essid, password=password)
    wap.active(True)
    # Debug-Output of network configuration
    net_config = wap.ifconfig()
    print(f"WLan-AccesPoint {essid} started succesfully:")
    print(f"	IPv4-Address: {net_config[0]}/{net_config[1]}")
    print(f"	Standard-Gateway: {net_config[2]}")
    print(f"	DNS-Server: {net_config[3]}")
    return (net_config[0], net_config[1]), wap


def get_all_available_networks() -> list[str]:
    """
    Scans for available Wi-Fi networks and returns a list of SSIDs.

    Returns
    -------
    list of str
        A list of SSIDs of visible local networks.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    networks = wlan.scan()
    return [net[0].decode("utf-8") for net in networks]


def build_index_html() -> str:
    """
    Builds HTML content for the root endpoint '/' of the webserver.

    Returns
    -------
    str
        HTML content for the root endpoint.

    Notes
    -----
    This function generates HTML content for displaying a form to connect to available networks.
    The form includes input fields for network selection and password entry.
    Upon submission, it triggers a JavaScript function to show a loader animation and submit the form asynchronously.
    """
    available_networks = get_all_available_networks()
    response = """<!DOCTYPE html>
        <html>
          <head>
          <script>
              function showLoader(event) {
                console.log("showLoader");
                event.preventDefault();
                document.getElementById("input-container").style.display = "none";
                document.getElementById("loader").style.display = "grid";
                setTimeout(function() {
                  document.getElementById("wifi-form").submit();
                }, 4000);
              }
            </script>
            <style>
              body {
                  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' version='1.1' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:svgjs='http://svgjs.dev/svgjs' width='1920' height='1080' preserveAspectRatio='none' viewBox='0 0 1920 1080'%3e%3cg mask='url(%26quot%3b%23SvgjsMask1001%26quot%3b)' fill='none'%3e%3crect width='1920' height='1080' x='0' y='0' fill='rgba(25%2c 201%2c 100%2c 1)'%3e%3c/rect%3e%3cpath d='M0%2c676.259C132.55%2c693.391%2c278.878%2c680.385%2c385.264%2c599.483C489.644%2c520.106%2c523.862%2c380.97%2c555.612%2c253.739C583.085%2c143.649%2c581.337%2c30.548%2c554.767%2c-79.763C529.994%2c-182.617%2c483.831%2c-279.599%2c409.112%2c-354.497C337.485%2c-426.296%2c238.302%2c-453.324%2c144.249%2c-491.266C39.463%2c-533.537%2c-64.101%2c-619.308%2c-173.047%2c-589.345C-282.004%2c-559.379%2c-311.076%2c-417.791%2c-395.604%2c-342.793C-498.282%2c-251.69%2c-684.088%2c-235.941%2c-720.516%2c-103.595C-756.051%2c25.504%2c-633.003%2c143.417%2c-560.403%2c255.927C-496.99%2c354.199%2c-419.732%2c437.355%2c-326.17%2c507.531C-226.22%2c582.498%2c-123.909%2c660.244%2c0%2c676.259' fill='%23139b4d'%3e%3c/path%3e%3cpath d='M1920 1945.85C2078.942 1919.162 2137.41 1716.35 2274.563 1631.71 2415.74 1544.587 2629.131 1582.676 2726.339 1448.243 2824.098 1313.049 2824.257 1113.443 2760.93 959.093 2700.826 812.5989999999999 2518.01 770.39 2403.402 661.13 2303.367 565.764 2264.934 395.756 2131.652 359.18100000000004 1998.375 322.60699999999997 1878.174 447.558 1743.865 480.14 1600.258 514.977 1414.324 446.30999999999995 1316.375 556.956 1218.616 667.3879999999999 1298.9299999999998 842.452 1292.688 989.806 1287.191 1119.577 1251.426 1245.154 1281.874 1371.422 1317.017 1517.163 1368.2359999999999 1664.882 1479.659 1765.183 1600.013 1873.5230000000001 1760.302 1972.665 1920 1945.85' fill='%2331e57e'%3e%3c/path%3e%3c/g%3e%3cdefs%3e%3cmask id='SvgjsMask1001'%3e%3crect width='1920' height='1080' fill='white'%3e%3c/rect%3e%3c/mask%3e%3c/defs%3e%3c/svg%3e");
                  background-size: cover;
                  background-repeat: no-repeat;
                  height: 100vh;
                  width: 100%;
                  font-family: Arial, Helvetica, sans-serif;
              }
              h1 {
                  font-size: 2.5rem;
                  text-align: center;
                  margin-bottom: 30px;
              }
              form {
                  text-align: left;
              }
              label {
                  font-size: 2.5rem;
                  display: block;
                  margin-top: 40px;
                  margin-bottom: -20px;
              }
              input[type="text"], input[type="password"], select {
                  width: 99%;
                  font-size: 3.5rem;
                  -webkit-appearance: none;
                  border: 1px solid #ccc;
                  padding: 0;
                  border-radius: 15px;
              }
              .input-container {
                  width: 80%;
                  margin: 0 auto;
                  margin-top: 50%;
                  padding: 40px;
                  border-radius: 20px;
                  background-color: white;
              }
              input[type="submit"] {
                  font-size: 2.5rem;
                  width: 100%;
                  margin-top: 30px;
                  padding: 20px;
                  background-color: #4caf50;
                  color: #fff;
                  border: none;
                  border-radius: 15px;
                  cursor: pointer;
              }
              .loader {
                    margin: 0 auto;
                    margin-top: 50%;
                    width: 150px;
                    aspect-ratio: 1; 
                    display: none;
              }
              .loader:before,
              .loader:after {
                    content: "";
                    grid-area: 1/1;
                    width: 70px;
                    aspect-ratio: 1;
                    box-shadow: 0 0 0 3px #fff inset;
                    filter: drop-shadow(80px 80px 0 #fff);
                    animation: l8 2s infinite alternate;
              }
              .loader:after {
                    margin: 0 0 0 auto; 
                    filter: drop-shadow(-80px 80px 0 #fff);
                    animation-delay: -1s;
              }
              @keyframes l8 {
                    0%,10%   {border-radius:0}
                    30%,40%  {border-radius:50% 0}
                    60%,70%  {border-radius:50%}
                    90%,100% {border-radius:0 50%}
              }
            </style>
          </head>
          <body>
            <div class="input-container" id="input-container">
              <h1>Verbindung herstellen</h1>
              <form id="wifi-form" method="get" action="/connect">
                <label for="network">Netzwerk</label><br>
                <select id="network" name="network">
    """
    for network_name in available_networks:
        response += f"        		<option value='{network_name}'>{network_name}</option>\n"
    response += """
        </select><br>
                <label for="password">Passwort</label><br>
                <input type="password" id="password" name="password"><br>
                <input type="submit" value="Verbinden" onclick="showLoader(event)">
              </form>
            </div>
            <div class="loader" id="loader"/>
          </body>
        </html>
    """
    return response


def build_status_html(status: str, ssid: bytes) -> str:
    """
    Build HTML content for displaying connection status.

    Parameters
    ----------
    status : str
        The connection status, either 'success' or 'error'.
    ssid : bytes
        The SSID of the network.

    Returns
    -------
    str
        HTML content to display the connection status.

    Raises
    ------
    ValueError
        If the provided status is neither 'success' nor 'error'.
    """
    response = """<!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body {
              background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' version='1.1' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:svgjs='http://svgjs.dev/svgjs' width='1920' height='1080' preserveAspectRatio='none' viewBox='0 0 1920 1080'%3e%3cg mask='url(%26quot%3b%23SvgjsMask1001%26quot%3b)' fill='none'%3e%3crect width='1920' height='1080' x='0' y='0' fill='rgba(25%2c 201%2c 100%2c 1)'%3e%3c/rect%3e%3cpath d='M0%2c676.259C132.55%2c693.391%2c278.878%2c680.385%2c385.264%2c599.483C489.644%2c520.106%2c523.862%2c380.97%2c555.612%2c253.739C583.085%2c143.649%2c581.337%2c30.548%2c554.767%2c-79.763C529.994%2c-182.617%2c483.831%2c-279.599%2c409.112%2c-354.497C337.485%2c-426.296%2c238.302%2c-453.324%2c144.249%2c-491.266C39.463%2c-533.537%2c-64.101%2c-619.308%2c-173.047%2c-589.345C-282.004%2c-559.379%2c-311.076%2c-417.791%2c-395.604%2c-342.793C-498.282%2c-251.69%2c-684.088%2c-235.941%2c-720.516%2c-103.595C-756.051%2c25.504%2c-633.003%2c143.417%2c-560.403%2c255.927C-496.99%2c354.199%2c-419.732%2c437.355%2c-326.17%2c507.531C-226.22%2c582.498%2c-123.909%2c660.244%2c0%2c676.259' fill='%23139b4d'%3e%3c/path%3e%3cpath d='M1920 1945.85C2078.942 1919.162 2137.41 1716.35 2274.563 1631.71 2415.74 1544.587 2629.131 1582.676 2726.339 1448.243 2824.098 1313.049 2824.257 1113.443 2760.93 959.093 2700.826 812.5989999999999 2518.01 770.39 2403.402 661.13 2303.367 565.764 2264.934 395.756 2131.652 359.18100000000004 1998.375 322.60699999999997 1878.174 447.558 1743.865 480.14 1600.258 514.977 1414.324 446.30999999999995 1316.375 556.956 1218.616 667.3879999999999 1298.9299999999998 842.452 1292.688 989.806 1287.191 1119.577 1251.426 1245.154 1281.874 1371.422 1317.017 1517.163 1368.2359999999999 1664.882 1479.659 1765.183 1600.013 1873.5230000000001 1760.302 1972.665 1920 1945.85' fill='%2331e57e'%3e%3c/path%3e%3c/g%3e%3cdefs%3e%3cmask id='SvgjsMask1001'%3e%3crect width='1920' height='1080' fill='white'%3e%3c/rect%3e%3c/mask%3e%3c/defs%3e%3c/svg%3e");
              background-size: cover;
              background-repeat: no-repeat;
              height: 100vh;
              width: 100%;
              font-family: Arial, Helvetica, sans-serif;
          }
          h1 {
              font-size: 2.5rem;
              text-align: center;
              margin-bottom: 30px;
              margin-top: 50px;
          }
          p {
              font-size: 1.5rem;
              text-align: center;
              margin-bottom: 30px;
          }
          .input-container {
              width: 80%;
              margin: 0 auto;
              margin-top: 50%;
              padding: 40px;
              padding-top: 10px;
              border-radius: 20px;
              background-color: white;
          }
          i {
            margin: 0 auto;
            margin-top: 40px;
          }
          .gg-check {
              box-sizing: border-box;
              color: #4caf50;
              position: relative;
              display: block;
              transform: scale(var(--ggs,8));
              width: 22px;
              height: 22px;
              border: 2px solid transparent;
              border-radius: 100px
          }
          .gg-check::after {
              content: "";
              display: block;
              box-sizing: border-box;
              position: absolute;
              left: 3px;
              top: -1px;
              width: 6px;
              height: 10px;
              border-width: 0 2px 2px 0;
              border-style: solid;
              transform-origin: bottom left;
              transform: rotate(45deg)
          }
          .gg-close {
              box-sizing: border-box;
              color: red;
              position: relative;
              display: block;
              transform: scale(var(--ggs,6));
              width: 22px;
              height: 22px;
              border: 2px solid transparent;
              border-radius: 40px
          }
          .gg-close::after,
          .gg-close::before {
              content: "";
              display: block;
              box-sizing: border-box;
              position: absolute;
              width: 16px;
              height: 2px;
              background: currentColor;
              transform: rotate(45deg);
              border-radius: 5px;
              top: 8px;
              left: 1px
          }
          .gg-close::after {
              transform: rotate(-45deg)
          }
          .return-button {
              font-size: 2.5rem;
              width: 100%;
              margin-top: 40px;
              padding: 20px;
              background-color: #4caf50;
              color: #fff;
              border: none;
              border-radius: 15px;
              cursor: pointer;
              transition: background-color 0.3s ease-in-out;
          }
          .return-button:hover {
              background-color: #45a049; /* Darker shade of green on hover */
          }
        </style>
      </head>
      <body>
        <div class="input-container">
    """
    if status != "success" and status != "error":
        raise ValueError(f"Status 'success' or 'error' expected, {status} provided")
    if status == "success":
        response +="""
          <i class="gg-check"></i>
          <h1>Verbindung hergestellt</h1>
        """
        response += f"      <p>Die Anmeldeinformationen für das Netzwerk {ssid.decode('utf-8')} wurden erfolgreich gespeichert!</p>"
    else:
        response +="""
          <i class="gg-close"></i>
          <h1>Verbindung fehlgeschlagen</h1>
        """
        response += f"      <p>Die Verbindung zum Netzwerk {ssid.decode('utf-8')} konnte nicht hergestellt werden. Bitte versuche es nochmal."
        response += "       <button class='return-button' onclick='redirectToRoot()'>Zurück</button>"
    response += """
        </div>
        <script>
          function redirectToRoot() {
              window.location.href = "/";
          }
        </script>
      </body>
      </html>
    """
    return response


def save_wifi_credentials(ssid: bytes, password: bytes):
    """
    Save Wi-Fi credentials to a JSON file.

    Parameters
    ----------
    ssid : bytes
        The SSID (network name) of the Wi-Fi network.
    password : bytes
        The password of the Wi-Fi network.

    Notes
    -----
    This function takes the SSID and password as bytes objects and converts them to
    UTF-8 encoded strings before saving them to the JSON file.
    """
    credentials = {"ssid": ssid.decode("utf-8"), "password": password.decode("utf-8")}
    with open("/wifi_config.json", "w") as file:
        json.dump(credentials, file)


def check_wifi_credentials(ssid: bytes, password: bytes) -> bool:
    """
    Check the validity of Wi-Fi credentials by attempting to connect to a temporary WLAN.

    Parameters
    ----------
    ssid : str
        The SSID (network name) of the Wi-Fi network.
    password : str
        The password of the Wi-Fi network.

    Returns
    -------
    bool
        True if the credentials are valid and connection is successful, False otherwise.

    Notes
    -----
    It checks for connection success within 5 seconds and returns True if successful, False otherwise.
    """
    temp_wlan = network.WLAN(network.STA_IF)
    temp_wlan.active(True)
    temp_wlan.connect(ssid, password)
    # Check if the WLAN is connected
    for _ in range(10): # try for 10 seconds
        if temp_wlan.isconnected():
            temp_wlan.disconnect()
            print("valid")
            return True
        utime.sleep(1)  
    temp_wlan.disconnect
    print("not valid")
    return False


def unquote(string) -> bytes:
    """
    Decodes a percent-encoded string.

    Parameters
    ----------
    string : str or bytes
        The percent-encoded string to decode.

    Returns
    -------
    bytes
        The decoded byte string.

    Notes
    -----
    This function decodes a percent-encoded string, replacing percent-encoded
    characters with their corresponding byte representation. If the input is
    already a byte string, it is assumed to be percent-encoded, otherwise it
    is encoded as UTF-8 before decoding. Non-ASCII characters are assumed to
    be percent-encoded.

    Examples
    --------
    >>> unquote('abc%20def')
    b'abc def'
    >>> unquote(b'abc%20def')
    b'abc def'
    """
    if not string:
        return b''
    if isinstance(string, str):
        string = string.encode('utf-8')
    bits = string.split(b'%')
    if len(bits) == 1:
        return string
    res = bytearray(bits[0])
    append = res.append
    extend = res.extend
    for item in bits[1:]:
        try:
            append(int(item[:2], 16))
            extend(item[2:])
        except KeyError:
            append(b'%')
            extend(item)
    return res


def handle_request(request: str, wlan) -> str:
    """
    Handle HTTP request and generate appropriate HTTP response.

    Parameters
    ----------
    request : str
        The HTTP request string.

    Returns
    -------
    str
        The HTTP response string.

    Notes
    -----
    This function parses the HTTP request and generates an appropriate HTTP
    response based on the request type and parameters.

    If the request is a GET request to the '/connect' endpoint with valid
    network credentials, it attempts to connect to the specified network,
    saves the credentials if successful, and returns a success response.

    If the request is a GET request to the '/connect' endpoint with invalid
    network credentials or incorrect format, it returns an error response.

    For any other request, it returns the HTML form page
    """
    if request.startswith("GET /connect?"):
        print("POST REQUEST")
        params = ure.match("GET /connect\?network=(.+?)&password=(.+?) HTTP", request)
        if params:
            ssid = unquote(params.group(1))
            password = unquote(params.group(2))
            if check_wifi_credentials(ssid, password):
                save_wifi_credentials(ssid, password)
                wlan.active(True)
                wlan.connect(ssid, password)
                for _ in range(5):
                    if wlan.isconnected():
                        print("Verbindung hergestellt!")
                        break
                return build_status_html("success", ssid)
        return build_status_html("error", ssid)
    else:
        print("DEFAULT REQUEST")
        # Respond with the HTML form page
        return build_index_html()


def start_webserver(ap_ipv4: str, wlan, wap):
    """
    Starts a simple web server on the specified IPv4 address.

    Parameters
    ----------
    ap_ipv4 : str
        The IPv4 address on which the web server will listen.

    Notes
    -----
    This function creates a TCP/IP socket, binds it to the specified IPv4 address
    and port 80, and listens for incoming connections. Upon receiving a connection,
    it receives the HTTP request from the client, processes it using the handle_request
    function, generates an appropriate HTTP response, and sends it back to the client.
    Finally, it closes the connection.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ap_ipv4, 80)) 
    server_socket.listen(5)
    print("Web server started. Listening for connections...")
    while True:
        # Wait for a connection
        client_socket, client_address = server_socket.accept()
        print("Client connected:", client_address)
        # Receive the HTTP request from the client
        request_data = client_socket.recv(1024)
        print("Request received:")
        print(request_data.decode("utf-8"))
        # Send HTTP response
        response = handle_request(request_data.decode("utf-8"),wlan)
        client_socket.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        client_socket.send(response.encode())
        # Close the connection
        client_socket.close()
        if wlan.isconnected():
            wap.active(False)
            break


if __name__ == "__main__":
    ipv4, subnetmask = create_access_point(essid="Test", password="password")
    start_webserver(ipv4)

