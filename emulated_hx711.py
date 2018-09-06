#import RPi.GPIO as GPIO
import time
##import numpy  # sudo apt-get python-numpy
import random
import math




class HX711:
    def __init__(self, dout, pd_sck, gain=128):
        self.PD_SCK = pd_sck
        self.DOUT = dout

        self.GAIN = 0
        self.REFERENCE_UNIT = 1  # The value returned by the hx711 that corresponds to your reference unit AFTER dividing by the SCALE.
        
        self.OFFSET = 1
        self.lastVal = long(0)

        self.byte_format = 'LSB'
        self.bit_format = 'MSB'

        self.set_gain(gain)

        self.last_read_time = time.time()

        self.sampleRateHz = 10.0

        self.resetTimeStamp = time.time()

        self.tareLock = False

        time.sleep(1)

    def convertToTwosComplement24bit(self, inputValue):
       # HX711 has saturating logic.
       if inputValue >= 0x7fffff:
          return 0x7fffff

       # If it's a positive value, just return it, masked with our max value.
       if inputValue >= 0:
          return inputValue & 0x7fffff

       if inputValue < 0:
          # HX711 has saturating logic.
          if inputValue < -0x800000:
             inputValue = -0x800000

          diff = inputValue + 0x800000

          return 0x800000 + diff

    def convertFromTwosComplement24bit(self, inputValue):
        return -(inputValue & 0x800000) + (inputValue & 0x7fffff)


    def is_ready(self):
        # Calculate how long we should be waiting between samples, given the
        # sample rate.
        sampleDelaySeconds = 1.0 / self.sampleRateHz

        return time.time() >= self.last_read_time + sampleDelaySeconds

    def set_gain(self, gain):
        if gain is 128:
            self.GAIN = 1
        elif gain is 64:
            self.GAIN = 3
        elif gain is 32:
            self.GAIN = 2


    
    def generateFakeSample(self):
       sampleTimeStamp = time.time() - self.resetTimeStamp

       noiseScale = 10.0
       noiseValue = random.randrange(-(noiseScale * 1000),(noiseScale * 1000)) / 1000.0
       sample     = math.sin(math.radians(sampleTimeStamp * 20)) * 72.0

       if sample < 0.0:
          sample = -sample

       sample += noiseValue

       sample *= 1000

       sample *= self.REFERENCE_UNIT

       return int(sample)



    def read(self):
        while not self.is_ready():
            pass

        self.last_read_time = time.time()

        rawValue = self.generateFakeSample()

        convertedValue = self.convertToTwosComplement24bit(rawValue)

        deconvertedValue = self.convertFromTwosComplement24bit(convertedValue)

        ###print "   read() =", deconvertedValue

        return deconvertedValue



    def read_long(self):

        return self.read()

    def read_average(self, times=3):
        values = long(0)
        for i in range(times):
            values += self.read_long()

        return values / times

    def get_value(self, times=3):
        while self.tareLock:
           ###print "Tare locked!"
           pass

        return self.read_average(times) - self.OFFSET

    def get_weight(self, times=3):
        value = self.get_value(times)
        value = value / self.REFERENCE_UNIT
        return value

    def tare(self, times=15):
        self.tareLock = True

        # Backup REFERENCE_UNIT value
        reference_unit = self.REFERENCE_UNIT
        self.set_reference_unit(1)

        value = self.read_average(times)
        self.set_offset(value)

        self.set_reference_unit(reference_unit)

        self.tareLock = False
        return value;

    def set_reading_format(self, byte_format="LSB", bit_format="MSB"):

        if byte_format == "LSB":
            self.byte_format = "LSB"
        elif byte_format == "MSB":
            self.byte_format = "LSB"
        else:
            print "HX711().set_reading_format(): Unrecognised byte_format \"%s\"!" % byte_format

        if bit_format == "LSB":
            self.bit_format = "LSB"
        elif bit_format == "MSB":
            self.bit_format = "LSB"
        else:
            print "HX711().set_reading_format(): Unrecognised bit_format \"%s\"!" % bit_format


    def set_offset(self, offset):
        self.OFFSET = offset

    def set_reference_unit(self, reference_unit):
        self.REFERENCE_UNIT = reference_unit

    # HX711 datasheet states that setting the PDA_CLOCK pin on high for >60 microseconds would power off the chip.
    # I used 100 microseconds, just in case.
    # I've found it is good practice to reset the hx711 if it wasn't used for more than a few seconds.
    def power_down(self):
        time.sleep(0.0001)

    def power_up(self):
        time.sleep(0.0001)

    def reset(self):
        # Mark time when we were reset.  We'll use this for sample generation.
        self.resetTimeStamp = time.time()

        self.power_down()
        self.power_up()


# EOF - emulated_hx711.py
