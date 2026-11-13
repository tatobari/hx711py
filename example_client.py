#! /usr/bin/python3

"""
Poll an hx711_server.py instance and print timestamp/weight values.
"""

import argparse
import datetime
import json
import time
import urllib.error
import urllib.request


DEFAULT_URL = "http://raspberrypi.local:8080/weight"
DEFAULT_INTERVAL = 0.5
DEFAULT_TIMEOUT = 2.0


def parse_args():
    parser = argparse.ArgumentParser(description="Poll an HX711 HTTP server.")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="reading URL (default: %(default)s)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL,
        help="seconds between polls (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="request timeout in seconds (default: %(default)s)",
    )
    return parser.parse_args()


def fetch(url, timeout):
    response = urllib.request.urlopen(url, timeout=timeout)
    try:
        return json.loads(response.read().decode("utf-8"))
    finally:
        response.close()


def main():
    args = parse_args()

    try:
        while True:
            try:
                reading = fetch(args.url, args.timeout)
                when = datetime.datetime.fromtimestamp(reading["ts"])
                print(
                    "{}  {:.3f} {}".format(
                        when.strftime("%Y-%m-%d %H:%M:%S"),
                        reading["weight"],
                        reading.get("unit", ""),
                    ).rstrip()
                )
            except urllib.error.HTTPError as exc:
                if exc.code == 503:
                    print("Waiting for the first reading...")
                else:
                    print("HTTP error: {}".format(exc))
            except Exception as exc:
                print("Error: {}".format(exc))

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()


# EOF - example_client.py
