#! /usr/bin/python2

import time
import sys

EMULATE_HX711=False

referenceUnit = -441

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711


# Import the HueController class from hue_controller.py
from hue_controller import HueController

# Instantiate the HueController
BRIDGE_IP = '192.168.1.46'
USER_TOKEN = 'BplzC08YY96lJDa8IT8EjaW9KcvvU87Ubn68il7u'
light_id = 47  # Replace with your specific light ID
hue = HueController(BRIDGE_IP, USER_TOKEN)


def cleanAndExit():
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print("Bye!")
    sys.exit()

hx = HX711(6, 5)

hx.set_reading_format("MSB", "MSB")

hx.set_reference_unit(referenceUnit)

hx.reset()

hx.tare()

print("Tare done! Add weight now...")

# Flag to track the weight status
is_weight_above_600 = False



while True:
    try:
        

        val = hx.get_weight(5)
        # print(val)

           # Check if the weight crosses the threshold and update the flag
        if val < -600 and not is_weight_above_600:
            is_weight_above_600 = True
            # Insert API call here to turn on the light
            # Example: make_api_call(turn_on_light)
            hue.turn_on_light(light_id)


        elif val >= -600 and is_weight_above_600:
            is_weight_above_600 = False
            # Insert API call here to turn off the light
            # Example: make_api_call(turn_off_light)
            hue.turn_off_light(light_id)

        hx.power_down()
        hx.power_up()
        time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
