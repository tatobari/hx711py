#! /usr/bin/python3

import time

from hx711 import HX711


RUN_SECONDS = 60.0
SAMPLES_PER_BATCH = 100


def print_summary(batch_count, total_rate, min_rate, max_rate, drop_count):
    print()

    if batch_count == 0:
        print("No samples collected.")
        return

    mean_rate = total_rate / batch_count
    print(
        "Overall: Mean {:.2f} Hz, Min {:.2f} Hz, Max {:.2f} Hz, Dropped {}".format(
            mean_rate, min_rate, max_rate, drop_count
        )
    )


hx = HX711(5, 6)

hx.set_channel_gain(hx.CH_A_GAIN_128)
hx.reset()

deadline = time.time() + RUN_SECONDS

batch_count = 0
total_rate = 0.0
min_rate = float("inf")
max_rate = float("-inf")
drop_count = 0

try:
    while time.time() < deadline:
        start_time = time.time()
        samples_read = 0

        for _ in range(SAMPLES_PER_BATCH):
            if hx.read_word() is not None:
                samples_read += 1
            else:
                drop_count += 1

        time_delta = time.time() - start_time
        sample_rate = samples_read / time_delta if time_delta > 0 else 0.0

        batch_count += 1
        total_rate += sample_rate
        min_rate = min(min_rate, sample_rate)
        max_rate = max(max_rate, sample_rate)

        mean_rate = total_rate / batch_count

        print(
            "Sample rate: {:.2f} Hz (Max: {:.2f}, Mean: {:.2f}, Min: {:.2f}) "
            "Dropped: {}".format(
                sample_rate, max_rate, mean_rate, min_rate, drop_count
            )
        )

except KeyboardInterrupt:
    print("\nInterrupted.")

finally:
    print_summary(batch_count, total_rate, min_rate, max_rate, drop_count)
    hx.cleanup()


# EOF - measure_sample_rate.py
