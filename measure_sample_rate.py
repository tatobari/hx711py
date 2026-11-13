#! /usr/bin/python3

from hx711 import HX711

import sys
import time


hx = HX711(5, 6)

hx.reset()

deadline = time.time() + 60.0

sample_rate_list = []
sample_count = 100

drop_count = 0

while time.time() < deadline:
    start_time = time.time()
    sample_count = 0

    for _ in range(100):
        if hx.read_word() is not None:
            sample_count += 1
        else:
            drop_count += 1

    end_time = time.time()

    time_delta = end_time - start_time

    sample_rate = sample_count / time_delta

    sample_rate_list.append(sample_rate)

    mean_sample_rate = sum(sample_rate_list) / len(sample_rate_list)
    min_sample_rate = min(sample_rate_list)
    max_sample_rate = max(sample_rate_list)

    output_string = "Sample rate: {:.2f} Hz (".format(sample_rate)
    output_string += "Max: {:.2f}, ".format(max_sample_rate)
    output_string += "Mean: {:.2f}, ".format(mean_sample_rate)
    output_string += "Min: {:.2f})".format(min_sample_rate)
    output_string += " Dropped: {}".format(drop_count)

    print(output_string)


# EOF - measure_sample_rate.py
