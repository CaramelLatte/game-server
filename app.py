# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from routes.minecraft import routes

hostName = "0.0.0.0"
serverPort = 9999

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        route_content = routes[self.path]
        return bytes(route_content, "UTF-8")

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")