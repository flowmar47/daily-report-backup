#!/usr/bin/env python3
"""
Simple HTTP server to display WhatsApp QR code
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8888

class QRHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp QR Code</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: Arial, sans-serif;
        }
        .container {
            text-align: center;
            max-width: 500px;
        }
        img {
            max-width: 100%;
            height: auto;
            border: 10px solid #f0f0f0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            color: #128C7E;
            margin-bottom: 20px;
        }
        .instructions {
            color: #666;
            margin-top: 20px;
            line-height: 1.6;
        }
        .refresh {
            margin-top: 20px;
            padding: 10px 20px;
            background: #128C7E;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .refresh:hover {
            background: #0e7a6c;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>WhatsApp QR Code</h1>
        <img src="/qr" alt="WhatsApp QR Code" id="qrcode">
        <div class="instructions">
            <p><strong>To link WhatsApp:</strong></p>
            <ol style="text-align: left;">
                <li>Open WhatsApp on your phone</li>
                <li>Go to Settings → Linked Devices</li>
                <li>Tap "Link Device"</li>
                <li>Scan this QR code</li>
            </ol>
        </div>
        <button class="refresh" onclick="location.reload()">Refresh QR Code</button>
    </div>
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""
            self.wfile.write(html.encode())
            
        elif self.path == '/qr':
            # Serve the QR code image
            qr_file = Path('whatsapp_qr_fresh.png')
            if not qr_file.exists():
                qr_file = Path('whatsapp_qr_headless.png')
            
            if qr_file.exists():
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                with open(qr_file, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, 'QR code not found')
        else:
            self.send_error(404)

print(f"Starting QR code server on port {PORT}")
print(f"Access from any device: http://<raspberry-pi-ip>:{PORT}")
print(f"Local access: http://localhost:{PORT}")
print("Press Ctrl+C to stop")

with socketserver.TCPServer(("", PORT), QRHandler) as httpd:
    httpd.serve_forever()