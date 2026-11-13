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
    
    def __init__(self, dout, pd_sck, gain=128):
        self.PD_SCK = pd_sck
        self.DOUT = dout

        # Mutex for reading from the HX711, in case multiple threads in client
        # software try to access get values from the class at the same time.
        self.readLock = threading.Lock()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PD_SCK, GPIO.OUT)
        GPIO.setup(self.DOUT, GPIO.IN)

        # HX711 defaults to Channel A Gain 128 on power up.
        self._gain = self.CH_A_GAIN_128

        # The value returned by the hx711 that corresponds to your reference
        # unit AFTER dividing by the SCALE.
        self.REFERENCE_UNIT = 1
        self.REFERENCE_UNIT_B = 1

        self.OFFSET = 1
        self.OFFSET_B = 1
        self.lastVal = int(0)

        self.DEBUG_PRINTING = False

        self.byte_format = 'MSB'
        self.bit_format = 'MSB'

    def is_ready(self):
        return GPIO.input(self.DOUT) == 0

    def set_channel_gain(self, enum_value):
        if enum_value in [1, 2, 3]:
            self._gain = enum_value

            GPIO.output(self.PD_SCK, False)

            # Read out a set of raw bytes and throw it away.
            self.read_word()
        
    def get_channel_gain(self):
        return self._gain

    def read_word(self, timeout_seconds=0.5):
        deadline = time.time() + timeout_seconds

        # Make sure clock is low.
        GPIO.output(self.PD_SCK, False)
        
        while GPIO.input(self.DOUT) == 1:
            if time.time() >= deadline:
                #raise ValueError("Timed out waiting for HX711 to be ready.")
                print("Timed out waiting for HX711 to be ready.")
                return None
            time.sleep(0.000001)

        deadline = time.time() + 0.0125
            
        raw_value = 0

        for _ in range(24):
            # Clock HX711 Digital Serial Clock (PD_SCK).  DOUT will be
            # ready 1us after PD_SCK rising edge, so we sample after
            # lowering PD_SCL, when we know DOUT will be stable.
            GPIO.output(self.PD_SCK, True)
            GPIO.output(self.PD_SCK, False)
            raw_value <<= 1
            raw_value |= int(GPIO.input(self.DOUT))

        # Add extra clocks to tell the HX711 what the next reading should be,
        # we've chosen values of GAIN so that it corresponds to the required
        # clocks after 24 bits of data have been read.
        for _ in range(self._gain):
            GPIO.output(self.PD_SCK, True)
            GPIO.output(self.PD_SCK, False)

        # Took too long to measure send all clocks, we can't trust this reading.
        if time.time() >= deadline:
            return None

        return twos_complement_24bit_to_int(raw_value)

    # Compatibility function, uses channel A version
    def get_value(self, times=3):
        return self.get_value_A(times)


    def get_value_A(self, times=3):
        return self.read_median(times) - self.get_offset_A()


    def get_value_B(self, times=3):
        # for channel B, we need to set_gain(32)
        g = self.get_gain()
        self.set_gain(32)
        value = self.read_median(times) - self.get_offset_B()
        self.set_gain(g)
        return value

    # Compatibility function, uses channel A version
    def get_weight(self, times=3):
        return self.get_weight_A(times)


    def get_weight_A(self, times=3):
        value = self.get_value_A(times)
        value = value / self.REFERENCE_UNIT
        return value

    def get_weight_B(self, times=3):
        value = self.get_value_B(times)
        value = value / self.REFERENCE_UNIT_B
        return value
    

    # Sets tare for channel A for compatibility purposes
    def tare(self, times=15):
        return self.tare_A(times)
    
    
    def tare_A(self, times=15):
        # Backup REFERENCE_UNIT value
        backupReferenceUnit = self.get_reference_unit_A()
        self.set_reference_unit_A(1)
        
        value = self.read_average(times)

        if self.DEBUG_PRINTING:
            print("Tare A value:", value)
        
        self.set_offset_A(value)

        # Restore the reference unit, now that we've got our offset.
        self.set_reference_unit_A(backupReferenceUnit)

        return value


    def tare_B(self, times=15):
        # Backup REFERENCE_UNIT value
        backupReferenceUnit = self.get_reference_unit_B()
        self.set_reference_unit_B(1)

        # for channel B, we need to set_gain(32)
        backupGain = self.get_gain()
        self.set_gain(32)

        value = self.read_average(times)

        if self.DEBUG_PRINTING:
            print("Tare B value:", value)
        
        self.set_offset_B(value)

        # Restore gain/channel/reference unit settings.
        self.set_gain(backupGain)
        self.set_reference_unit_B(backupReferenceUnit)
       
        return value

    # sets offset for channel A for compatibility reasons
    def set_offset(self, offset):
        self.set_offset_A(offset)

    def set_offset_A(self, offset):
        self.OFFSET = offset

    def set_offset_B(self, offset):
        self.OFFSET_B = offset

    def get_offset(self):
        return self.get_offset_A()

    def get_offset_A(self):
        return self.OFFSET

    def get_offset_B(self):
        return self.OFFSET_B

    def set_reference_unit(self, reference_unit):
        self.set_reference_unit_A(reference_unit)

    def set_reference_unit_A(self, reference_unit):
        # Make sure we aren't asked to use an invalid reference unit.
        if reference_unit == 0:
            raise ValueError("HX711::set_reference_unit_A() can't accept 0 as a reference unit!")
            return

        self.REFERENCE_UNIT = reference_unit

        
    def set_reference_unit_B(self, reference_unit):
        # Make sure we aren't asked to use an invalid reference unit.
        if reference_unit == 0:
            raise ValueError("HX711::set_reference_unit_A() can't accept 0 as a reference unit!")
            return

        self.REFERENCE_UNIT_B = reference_unit


    def get_reference_unit(self):
        return get_reference_unit_A()

    def get_reference_unit_A(self):
        return self.REFERENCE_UNIT

    def get_reference_unit_B(self):
        return self.REFERENCE_UNIT_B
        
    def power_down(self):
        # Wait for and get the Read Lock, in case another thread is already
        # driving the HX711 serial interface.
        self.readLock.acquire()

        # Because a rising edge on HX711 Digital Serial Clock (PD_SCK).  We then
        # leave it held up and wait 100us.  After 60us the HX711 should be
        # powered down.
        GPIO.output(self.PD_SCK, False)
        GPIO.output(self.PD_SCK, True)

        time.sleep(0.0001)

        # Release the Read Lock, now that we've finished driving the HX711
        # serial interface.
        self.readLock.release()           

    def power_up(self):
        # Wait for and get the Read Lock, incase another thread is already
        # driving the HX711 serial interface.
        self.readLock.acquire()

        # Lower the HX711 Digital Serial Clock (PD_SCK) line.
        GPIO.output(self.PD_SCK, False)

        # Wait 100 us for the HX711 to power back up.
        time.sleep(0.0001)

        # Release the Read Lock, now that we've finished driving the HX711
        # serial interface.
        self.readLock.release()

        # HX711 will now be defaulted to Channel A with gain of 128.  If this
        # isn't what client software has requested from us, take a sample and
        # throw it away, so that next sample from the HX711 will be from the
        # correct channel/gain.
        if self._gain != self.CH_A_GAIN_128:
            self.read_word()

    def reset(self):
        self.power_down()
        self.power_up()


def hx711_add_event_detect(hx711_instance, event_callback):
        GPIO.add_event_detect(self.DOUT, GPIO.FALLING, 
            callback=event_callback)


# EOF - hx711.py
