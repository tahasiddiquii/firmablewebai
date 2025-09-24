from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "Hello from FirmableWebAI!",
            "status": "working",
            "timestamp": "2024-01-01"
        }
        
        self.wfile.write(json.dumps(response).encode())
