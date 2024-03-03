import time
import sys
from emulated_hx711 import HX711


def cleanAndExit():
    print("Cleaning...")
        
    print("Bye!")
    sys.exit()

referenceUnit = 1
hx = HX711(5, 6)


hx.set_reading_format("MSB", "MSB")

#hx.set_reference_unit(113)
hx.set_reference_unit(referenceUnit)

hx.reset()

hx.tare()

print("Tare done! Add weight now...")

while True:
    try:
        val = hx.get_weight(5)
        print(val)

        hx.power_down()
        hx.power_up()
        time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
