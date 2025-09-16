from flask import Flask
from flask_cors import CORS
from games import *
import datetime
import json
import dotenv
from threading import Timer
import requests
import subprocess
import os
import logging
from typing import List, Optional
from routes.game_bp import game_bp
from manager import server_manager

app = Flask(__name__)
CORS(app)
dotenv.load_dotenv()

# Configure logging for the module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RepeatedTimer:
    #Timer class to run a function periodically.
    def __init__(self, interval: int, function: callable) -> None:
        self._timer: Optional[Timer] = None
        self.interval: int = interval
        self.function: callable = function
        self.is_running: bool = False
        self.start()

    def _run(self) -> None:
        try:
            self.is_running = False
            self.start()
            self.function()
        except Exception as e:
            logging.error(f"Error in RepeatedTimer: {e}")

    def start(self) -> None:
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self) -> None:
        if self._timer:
            self._timer.cancel()
        self.is_running = False


# Set up the periodic update timer
rt = RepeatedTimer(10, server_manager.update)


# Register blueprints
app.register_blueprint(game_bp)


@app.route('/health')
def health_check():
    try:
        return json.dumps({"status": "ok"}), 200
    except Exception as e:
        logging.error(f"Error in health check endpoint: {e}")
        return json.dumps({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    try:
        chain = os.getenv("SSL_CHAIN")
        privkey = os.getenv("SSL_PRIVKEY")
        if not chain or not privkey:
            raise ValueError("SSL_CHAIN or SSL_PRIVKEY environment variables are not set.")
        app.run(ssl_context=(chain, privkey), host="0.0.0.0", port=8080)
    except Exception as e:
        logging.error(f"Error starting the server: {e}")

rt.stop()  # Stop the timer when the script ends. Server behaves weirdly if you don't do this.