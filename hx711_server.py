#! /usr/bin/python3

"""
Serve the latest HX711 reading over HTTP as JSON.

Run this on the machine connected to the HX711; clients poll /weight.
"""

import argparse
import json
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

from hx711 import HX711


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080
DEFAULT_DOUT_PIN = 5
DEFAULT_PD_SCK_PIN = 6

GAIN_ENUMS = {
    128: HX711.CH_A_GAIN_128,
    64: HX711.CH_A_GAIN_64,
    32: HX711.CH_B_GAIN_32,
}


class LatestReading:
    """Thread-safe holder for the most recent reading."""

    def __init__(self):
        self._lock = threading.Lock()
        self._value = None

    def set(self, value):
        with self._lock:
            self._value = value

    def get(self):
        with self._lock:
            return self._value


def read_forever(hx, reading, unit):
    while True:
        weight = hx.read_weight()
        if weight is not None:
            reading.set({"ts": time.time(), "weight": weight, "unit": unit})


class Handler(BaseHTTPRequestHandler):
    reading = None  # set in main()

    def do_GET(self):
        if self.path not in ("/", "/weight"):
            self.send_error(404)
            return

        payload = self.reading.get()
        if payload is None:
            self.send_error(503, "No reading yet")
            return

        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def _handle_sigterm(signum, frame):
    raise KeyboardInterrupt


def parse_args():
    parser = argparse.ArgumentParser(
        description="Serve the latest HX711 reading over HTTP as JSON."
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="bind address (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="TCP port (default: %(default)s)",
    )
    parser.add_argument(
        "--dout",
        type=int,
        default=DEFAULT_DOUT_PIN,
        help="DOUT GPIO pin (default: %(default)s)",
    )
    parser.add_argument(
        "--pd-sck",
        type=int,
        default=DEFAULT_PD_SCK_PIN,
        help="PD_SCK GPIO pin (default: %(default)s)",
    )
    parser.add_argument(
        "--gain",
        type=int,
        choices=(128, 64, 32),
        default=128,
        help="channel A gain 128/64, or channel B gain 32 (default: %(default)s)",
    )
    parser.add_argument(
        "--m",
        type=float,
        help="calibration m (default: 1.0)",
    )
    parser.add_argument(
        "--c",
        type=float,
        help="calibration c (default: 0.0)",
    )
    parser.add_argument(
        "--unit",
        default="units",
        help="unit label reported to clients (default: %(default)s)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    hx = HX711(args.dout, args.pd_sck)

    if args.m is not None:
        hx.set_m(args.m)
    if args.c is not None:
        hx.set_c(args.c)

    hx.reset()
    hx.set_channel_gain(GAIN_ENUMS[args.gain])

    reading = LatestReading()
    Handler.reading = reading

    threading.Thread(
        target=read_forever, args=(hx, reading, args.unit), daemon=True
    ).start()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print("Serving http://{}:{}/weight".format(args.host, args.port))
    signal.signal(signal.SIGTERM, _handle_sigterm)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        hx.cleanup()


if __name__ == "__main__":
    main()


# EOF - hx711_server.py
