#! /usr/bin/python3

"""
Interactive calibration helper for the HX711.

Collect raw readings for one or more known loads and fit

    load = m * raw + c

so the results can be passed to HX711.set_m()/set_c() and used with
HX711.read_weight().
"""

import argparse
import statistics
import sys

from hx711 import HX711


DEFAULT_DOUT_PIN = 5
DEFAULT_PD_SCK_PIN = 6
DEFAULT_SAMPLE_COUNT = 100
MAX_CONSECUTIVE_TIMEOUTS = 10

GAIN_ENUMS = {
    128: HX711.CH_A_GAIN_128,
    64: HX711.CH_A_GAIN_64,
    32: HX711.CH_B_GAIN_32,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calibrate an HX711 load cell and report m and c."
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
        "--samples",
        type=int,
        default=DEFAULT_SAMPLE_COUNT,
        help="raw samples to take per load (default: %(default)s)",
    )
    parser.add_argument(
        "--gain",
        type=int,
        choices=(128, 64, 32),
        default=128,
        help="channel A gain 128/64, or channel B gain 32 (default: %(default)s)",
    )
    parser.add_argument(
        "--unit",
        default="units",
        help="label for the known loads, e.g. kg (default: %(default)s)",
    )

    args = parser.parse_args()

    if args.samples < 1:
        parser.error("--samples must be at least 1")

    return args


def collect_samples(hx, sample_count):
    samples = []
    consecutive_timeouts = 0

    while len(samples) < sample_count:
        value = hx.read_word()

        if value is None:
            consecutive_timeouts += 1
            if consecutive_timeouts >= MAX_CONSECUTIVE_TIMEOUTS:
                raise RuntimeError(
                    "HX711 stayed unready for {} reads".format(
                        consecutive_timeouts
                    )
                )
            continue

        consecutive_timeouts = 0
        samples.append(value)

    return samples


def summarize(samples):
    median = statistics.median(samples)
    mean = statistics.mean(samples)
    stdev = statistics.stdev(samples) if len(samples) > 1 else 0.0
    return median, mean, stdev, min(samples), max(samples)


def linear_fit(points):
    """Return (m, c, r_squared) for load = m * raw + c."""
    count = len(points)
    mean_raw = sum(raw for raw, _ in points) / count
    mean_load = sum(load for _, load in points) / count

    sxx = sum((raw - mean_raw) ** 2 for raw, _ in points)
    sxy = sum((raw - mean_raw) * (load - mean_load) for raw, load in points)
    ss_tot = sum((load - mean_load) ** 2 for _, load in points)

    if sxx == 0:
        raise ValueError("all raw readings are identical")
    if ss_tot == 0:
        raise ValueError("all known loads are identical")

    m = sxy / sxx
    c = mean_load - m * mean_raw
    ss_res = sum((load - (m * raw + c)) ** 2 for raw, load in points)
    r_squared = 1.0 - (ss_res / ss_tot)

    return m, c, r_squared


def prompt_known_load(unit):
    while True:
        try:
            text = input("Known load in {} (blank to finish): ".format(unit))
        except EOFError:
            return None

        text = text.strip()
        if not text:
            return None

        try:
            return float(text)
        except ValueError:
            print("Please enter a number, or leave blank to finish.")


def main():
    args = parse_args()
    hx = HX711(args.dout, args.pd_sck)
    points = []

    try:
        hx.reset()
        hx.set_channel_gain(GAIN_ENUMS[args.gain])

        print("Calibrating with {} sample(s) per load.".format(args.samples))

        while True:
            known_load = prompt_known_load(args.unit)
            if known_load is None:
                break

            try:
                input("Let the scale settle, then press Enter to measure...")
            except EOFError:
                pass

            try:
                samples = collect_samples(hx, args.samples)
            except RuntimeError as exc:
                print("Measurement failed: {}".format(exc))
                continue

            median, mean, stdev, low, high = summarize(samples)
            points.append((median, known_load))

            print(
                "  raw: median {:.1f}, mean {:.1f}, stdev {:.1f}, "
                "min {}, max {}".format(median, mean, stdev, low, high)
            )

            if len(points) < 2:
                continue

            try:
                m, c, r_squared = linear_fit(points)
            except ValueError as exc:
                print("  cannot fit yet: {}".format(exc))
            else:
                print(
                    "  fit: load = {!r} * raw + {!r} (R^2 = {:.5f})".format(
                        m, c, r_squared
                    )
                )

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
    finally:
        hx.cleanup()

    if len(points) < 2:
        print("Need at least two different loads to calibrate.")
        return 1

    try:
        m, c, r_squared = linear_fit(points)
    except ValueError as exc:
        print("Calibration failed: {}".format(exc))
        return 1

    print()
    print("Calibration")
    print("  points: {}".format(len(points)))
    print("  m = {!r}".format(m))
    print("  c = {!r}".format(c))
    print("  R^2 = {:.6f}".format(r_squared))
    if len(points) < 3:
        print("  (R^2 is always 1 with two points; add more loads to check the fit.)")
    print()
    print("Use it with:")
    print("  hx.set_m({!r})".format(m))
    print("  hx.set_c({!r})".format(c))
    print("  hx.read_weight()  # = m * raw + c")

    return 0


if __name__ == "__main__":
    sys.exit(main())


# EOF - calibrate_sensor.py
