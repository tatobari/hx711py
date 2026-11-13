import time
import sys
from hx711 import HX711

# FakeGpio pretends to be raspberry pi GPIO module, so HX711 class doesn't know
# it's not talking to real hardware.
from hx711.fake_gpio import FakeGpio

# FakeHx711 tries to emulate pin level behaviour of HX711.
from hx711.fake_hx711 import FakeHx711


def cleanAndExit():
    print("Cleaning...")
        
    print("Bye!")
    sys.exit()

# Let's make a Fake HX711
fake_hx711 = FakeHx711()

# We'll put in fake raw samples from 0 to 1000
fake_hx711.inject_raw_samples(list(range(1000)))

# Now we'll point our HX711 class at a FakeGpio wrapper around our fake HX711.
hx = HX711(5, 6, gpio_module=FakeGpio(fake_hx711))

hx.reset()

while True:
    try:
        val = hx.read_word()
        print(val)

        time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
