#! /usr/bin/python2

import time
import sys

EMULATE_HX711=False

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

def cleanAndExit():
    print "Cleaning..."

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print "Bye!"
    sys.exit()

hx = HX711(5, 6)

# I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
# Still need to figure out why does it change.
# If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
# There is some code below to debug and log the order of the bits and the bytes.
# The first parameter is the order in which the bytes are used to build the "long" value.
# The second paramter is the order of the bits inside each byte.
# According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
hx.set_reading_format("MSB", "MSB")

# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
#hx.set_reference_unit(113)
#hx.set_reference_unit(15)

hx.reset()

print "Taring:"
tareResult = hx.tare(80)

print "Tared:", tareResult

###hx.set_offset(2000)

##sys.exit()

movingAverage = 0.0

###hx.set_gain(128)

while True:
    try:
        # These three lines are usefull to debug wether to use MSB or LSB in the reading formats
        # for the first parameter of "hx.set_reading_format("LSB", "MSB")".
        # Comment the two lines "val = hx.get_weight(5)" and "print val" and uncomment the three lines to see what it prints.
        if False:
            np_arr8_string = hx.get_np_arr8_string()
            binary_string = hx.get_binary_string()
            print binary_string + " " + np_arr8_string
        
        # Prints the weight. Comment if you're debbuging the MSB and LSB issue.
        if False:
            val = hx.get_weight(times=1)
            print val

        if False:
            val = hx.get_weight(30)
            print "My read:", val / 1000.0, "kg"

            
        if True:
            val = hx.get_value(30)
            print "My read:", val


        
        # movingAverage *= 0.9
        # movingAverage += 0.1 * val
        # print "MY READ:", val, "MA:", movingAverage, "  --  ", movingAverage / 1000.0, "kg"
        ###print "offset=", hx.get_offset()
        ###print "gain=", hx.get_gain()
        
            
        if False:
            hx.power_down()
            hx.power_up()
            time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
