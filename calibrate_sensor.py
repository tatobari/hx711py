#! /usr/bin/python3

from hx711 import HX711

import sys
import time
import statistics
import numpy


hx = HX711(5, 6)

hx.reset()

load_list = []
scale_list = []

while True:
    print("Add a known load to the scale, let it settle before hitting return.")
    print("You can enter the known loads as any unit you like, as long as you're consistent.")
    known_load = float(input("Input known load: "))
    print("Measuring:")

    for x in range(10):
        sample_list = []

        for _ in range(10):
            sample = hx.read_word()

            if sample is None:
                continue

            sample_list.append(sample)

        median = statistics.median(sample_list)

        load_list.append(known_load)
        scale_list.append(median)
        # print(median)
    
    if len(load_list) > 1:
        fit = numpy.polyfit(scale_list, load_list, 1)

        m = float(fit[0])
        c = float(fit[1])
        
        print("y = m*x + c;  m = {}, c ={}".format(m, c))


# EOF - calibrate_sensor.py