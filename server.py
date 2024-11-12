#!/usr/bin/env python3

import http.server
import json
import urllib.parse
import tomlkit
from pathlib import Path

import clevertoad


CONFIG_FILE = Path("config.toml")
HTML_FILE = Path("static/index.html")


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as file:
            return tomlkit.load(file)
    return {
        "dice_type": 20,
        "critical_fail": "You borfed it.",
        "critical_success": "High Roller, indeed!",
        "prophecy_parts": {
            "subjects": [],
            "actions": [],
            "objects": [],
            "spatial_prepositions": [],
            "temporal_prepositions": [],
            "places": [],
            "times": []
        }
    }


def save_config(data):
    with open(CONFIG_FILE, "w") as file:
        tomlkit.dump(data, file)


def content_type(path):
    if path.endswith(".js"):
        return "application/javascript"
    elif path.endswith(".css"):
        return "text/css"
    elif path.endswith(".woff2"):
        return "font/woff2"


def make_handler(toad):

    class ConfigHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                if HTML_FILE.exists():
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    with open(HTML_FILE, "r") as file:
                        self.wfile.write(file.read().encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"HTML file not found")
            elif self.path.startswith("/speak"):
                query = urllib.parse.urlparse(self.path).query
                message = urllib.parse.unquote(query)
                toad.speech_engine.say(message)
                self.send_response(204)
                self.end_headers()
            elif self.path.startswith("/static/"):
                try:
                    file_path = "." + self.path  # Local file path
                    with open(file_path, "rb") as file:
                        self.send_response(200)
                        self.send_header("Content-Type", content_type(self.path))
                        self.end_headers()
                        self.wfile.write(file.read())
                except FileNotFoundError:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"File not found")
            elif self.path == "/config":
                config = load_config()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(config).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_PUT(self):
            if self.path == "/config":
                # Parse the incoming JSON data
                content_length = int(self.headers["Content-Length"])
                post_data = self.rfile.read(content_length)
                update_data = json.loads(post_data.decode())

                # Validate that the update_data contains all necessary lists
                parts = [
                    "subjects", "actions", "objects", "spatial_prepositions",
                    "temporal_prepositions", "places", "times"
                ]
                dice_preferences = ["dice_type", "critical_fail",
                                    "critical_success"]
                if (all(p in update_data["prophecy_parts"] for p in parts) and
                   all(k in update_data for k in dice_preferences) and
                   int(update_data['dice_type']) >= 2):
                    save_config(update_data)
                    toad.update_config(update_data)

                    # Send a success response
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success"}).encode())
                else:
                    # Send an error response if validation fails
                    self.send_response(400)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "message": "Invalid data structure"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

    return ConfigHandler


if __name__ == "__main__":
    config = load_config()
    toad = clevertoad.CleverToad(config)
    server_address = ("", 8000)
    httpd = http.server.HTTPServer(server_address, make_handler(toad))
    httpd.serve_forever()
