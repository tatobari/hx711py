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

# read_word() returns a signed 24-bit raw reading, or None on timeout.
while True:
    try:
        val = hx.read_word()
        print(val)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
