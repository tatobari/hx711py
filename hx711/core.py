#! /usr/bin/python3

import time
import threading

from .fake_hx711 import FakeHx711
from .fake_gpio import FakeGpio

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    print("No RPi package, simulating GPIO connected to fake HX711.")
    FAKE_HX711 = FakeHx711()

    FAKE_HX711.inject_raw_samples([0x111,0x222,0x333])
    GPIO = FakeGpio(FAKE_HX711)


def twos_complement_24bit_to_int(input_value):
    return -(input_value & 0x800000) + (input_value & 0x7fffff)


class HX711:
    # Input and gain selection is controlled by the number of the input PD_SCK
    # pulses (Table 3).  PD_SCK clock pulses should not be less than 25 or more
    # than 27 within one conversion period, to avoid causing serial
    # communication error.
    #
    # Table 3 Input Channel and Gain Selection:
    # +---------------+---------------+------+
    # | PD_SCK Pulses | Input Channel | Gain |
    # +---------------+---------------+------+
    # | 25 (24 + 1)   | A             | 128  |
    # | 26 (24 + 2)   | B             | 32   |
    # | 27 (24 + 3)   | A             | 64   |
    # +---------------+---------------+------+
    CH_A_GAIN_128 = 1
    CH_B_GAIN_32 = 2
    CH_A_GAIN_64 = 3

    # Maximum time allowed to clock out one sample (24 data bits plus the
    # gain-selection pulses).  If it takes longer than this, the reading may
    # be corrupt, so read_word() returns None.
    _CLOCK_TIMEOUT_SECONDS = 0.0125

    def __init__(self, dout, pd_sck, gpio_module=None):
        self._gpio = gpio_module

        if self._gpio is None:
            self._gpio = GPIO

        self._pd_sck = pd_sck
        self._dout = dout

        # Mutex for reading from the HX711, in case multiple threads in client
        # software try to access get values from the class at the same time.
        self._read_lock = threading.Lock()

        self._gpio.setmode(self._gpio.BCM)
        self._gpio.setup(self._pd_sck, self._gpio.OUT)
        self._gpio.setup(self._dout, self._gpio.IN)

        # HX711 defaults to Channel A Gain 128 on power up.
        self._gain = self.CH_A_GAIN_128

    def is_ready(self):
        return self._gpio.input(self._dout) == 0

    def set_channel_gain(self, enum_value):
        if enum_value not in (
            self.CH_A_GAIN_128,
            self.CH_B_GAIN_32,
            self.CH_A_GAIN_64,
        ):
            raise ValueError(
                "HX711::set_channel_gain() invalid channel/gain: {!r}".format(
                    enum_value
                )
            )

        self._gain = enum_value

        self._gpio.output(self._pd_sck, False)

        # Read out a set of raw bytes and throw it away.
        self.read_word()

    def get_channel_gain(self):
        return self._gain

    def read_word(self, timeout_seconds=0.5):
        # Wait for and get the Read Lock, in case another thread is already
        # driving the HX711 serial interface.
        with self._read_lock:
            deadline = time.monotonic() + timeout_seconds

            # Make sure clock is low.
            self._gpio.output(self._pd_sck, False)

            while self._gpio.input(self._dout) == 1:
                if time.monotonic() >= deadline:
                    return None

                time.sleep(0.000001)

            clock_deadline = time.monotonic() + self._CLOCK_TIMEOUT_SECONDS

            raw_value = 0

            for _ in range(24):
                # Clock HX711 Digital Serial Clock (PD_SCK).  DOUT will be
                # ready 1us after PD_SCK rising edge, so we sample after
                # lowering PD_SCL, when we know DOUT will be stable.
                self._gpio.output(self._pd_sck, True)
                self._gpio.output(self._pd_sck, False)
                raw_value <<= 1
                raw_value |= int(self._gpio.input(self._dout))

            # Add extra clocks to tell the HX711 what the next reading should
            # be, we've chosen values of GAIN so that it corresponds to the
            # required clocks after 24 bits of data have been read.
            for _ in range(self._gain):
                self._gpio.output(self._pd_sck, True)
                self._gpio.output(self._pd_sck, False)

            # Took too long to send all clocks, we can't trust this reading.
            if time.monotonic() >= clock_deadline:
                return None

            return twos_complement_24bit_to_int(raw_value)

    def power_down(self):
        # Wait for and get the Read Lock, in case another thread is already
        # driving the HX711 serial interface.
        with self._read_lock:
            # Because a rising edge on HX711 Digital Serial Clock (PD_SCK).
            # We then leave it held up and wait 100us.  After 60us the HX711
            # should be powered down.
            self._gpio.output(self._pd_sck, False)
            self._gpio.output(self._pd_sck, True)

            time.sleep(0.0001)

    def power_up(self):
        # Wait for and get the Read Lock, in case another thread is already
        # driving the HX711 serial interface.
        with self._read_lock:
            # Lower the HX711 Digital Serial Clock (PD_SCK) line.
            self._gpio.output(self._pd_sck, False)

            # Wait 100 us for the HX711 to power back up.
            time.sleep(0.0001)

        # HX711 will now be defaulted to Channel A with gain of 128.  If this
        # isn't what client software has requested from us, take a sample and
        # throw it away, so that next sample from the HX711 will be from the
        # correct channel/gain.
        if self._gain != self.CH_A_GAIN_128:
            self.read_word()

    def reset(self):
        self.power_down()
        self.power_up()

    def cleanup(self):
        # Release the GPIO pins if the underlying module supports it.
        cleanup = getattr(self._gpio, "cleanup", None)
        if cleanup is not None:
            cleanup()


def hx711_add_event_detect(hx711_instance, event_callback):
        GPIO.add_event_detect(self._dout, GPIO.FALLING, 
            callback=event_callback)


# EOF - core.py
