import sys
from hx711 import HX711


def cleanAndExit():
    print("Cleaning...")

    print("Bye!")
    sys.exit()


hx = HX711(5, 6)

# Tell the HX711 we'll be reading Channel A with gain 128.
hx.set_channel_gain(hx.CH_A_GAIN_128)

hx.reset()

hx.set_m(7.19942404607631e-05)
hx.set_c(-0.14398848092153457)

# read_word() returns a signed 24-bit raw reading, or None on timeout.
while True:
    try:
        val = hx.read_weight()
        print(val)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
