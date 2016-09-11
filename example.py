import RPi.GPIO as GPIO
import time
import sys
from hx711 import HX711

def cleanAndExit():
    print "Cleaning..."
    GPIO.cleanup()
    print "Bye!"
    sys.exit()

hx = HX711(5, 6)

# I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
# Still need to figure out why does it change.
# If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
# There is some code below to debug and log the order of the bits and the bytes.
hx.set_reading_format("LSB", "MSB")

# To set the reference unit comment the "hx.set_reference_unit(92)" line, put 1kg on your sensor
# or some weight that you know and use rule of thirds to calculate the reference unit.
# In this case, 92 is 1 gram.
hx.set_reference_unit(92)

hx.reset()
hx.tare()

while True:
    try:
        # This is usefull to debug wether to use MSB or LSB in the reading formats.
        #np_arr8_string = hx.get_np_arr8_string()
        #binary_string = hx.get_binary_string()
        #print binary_string + " " + np_arr8_string
        
        # Prints the weight. Comment if you're debbuging the MSB and LSB issue.
        val = hx.get_weight(5)
        print val

        hx.power_down()
        hx.power_up()
        time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
