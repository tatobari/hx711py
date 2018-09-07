#

import RPi.GPIO as GPIO
import time
import threading


class HX711:
    def __init__(self, dout, pd_sck, gain=128):
        self.PD_SCK = pd_sck

        self.DOUT = dout

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PD_SCK, GPIO.OUT)
        GPIO.setup(self.DOUT, GPIO.IN)

        self.GAIN = 0
        self.REFERENCE_UNIT = 1  # The value returned by the hx711 that corresponds to your reference unit AFTER dividing by the SCALE.
        
        self.OFFSET = 1
        self.lastVal = long(0)

        self.DEBUG_PRINTING = False
        
        self.byte_format = 'MSB'
        self.bit_format = 'MSB'

        self.set_gain(gain)

        # Mutex for reading from the HX711, in case multiple threads in client
        # software try to access get values from the class at the same time.
        self.readRock = threading.Lock()

        time.sleep(1)

        
    def convertFromTwosComplement24bit(self, inputValue):
        return -(inputValue & 0x800000) + (inputValue & 0x7fffff)

    
    def is_ready(self):
        return GPIO.input(self.DOUT) == 0

    
    def set_gain(self, gain):
        if gain is 128:
            self.GAIN = 1
        elif gain is 64:
            self.GAIN = 3
        elif gain is 32:
            self.GAIN = 2

        GPIO.output(self.PD_SCK, False)

        # Read out a set of raw bytes and throw it away.
        self.readRawBytes()

        
    def get_gain(self):
        if self.GAIN == 1:
            return 128
        if self.GAIN == 3:
            return 64
        if self.GAIN == 2:
            return 32

        # Shouldn't get here.
        return 0
        

    def readNextBit(self):
       # Clock HX711 Digital Serial Clock (PD_SCK).  DOUT will be
       # ready 1us after PD_SCK rising edge, so we sample after
       # lowering PD_SCL, when we know DOUT will be stable.
       GPIO.output(self.PD_SCK, True)
       GPIO.output(self.PD_SCK, False)
       value = GPIO.input(self.DOUT)

       # Convert Boolean to int and return it.
       if value:
          return 1
       else:
          return 0


    def readNextByte(self):
       byteValue = 0

       # Read bits and build the byte from top, or bottom, depending
       # on whether we are in MSB or LSB bit mode.
       for x in range(8):
          if self.bit_format == 'MSB':
             byteValue <<= 1
             byteValue |= self.readNextBit()
          else:
             byteValue >>= 1              
             byteValue |= self.readNextBit() * 0x80

       # Return the packed byte.
       return byteValue 
        

    def readRawBytes(self):
        # Wait for and get the Read Lock, incase another thread is already
        # driving the HX711 serial interface.
        self.readLock.acquire()

        # Wait until HX711 is ready for us to read a sample.
        while not self.is_ready():
           pass

        # Read three bytes of data from the HX711.
        firstByte  = self.readNextByte()
        secondByte = self.readNextByte()
        thirdByte  = self.readNextByte()

        # HX711 Channel and gain factor are set by number of bits read
        # after 24 data bits.
        for i in range(self.GAIN):
           # Clock a bit out of the HX711 and throw it away.
           self.readNextBit()

        # Release the Read Lock, now that we've finished driving the HX711
        # serial interface.
        self.readLock.release()           

        # Depending on how we're configured, return and orderd list of raw byte values.
        if self.byte_format == 'LSB':
           return [thirdByte, secondByte, firstByte]
        else:
           return [firstByte, secondByte, thirdByte]


    def read_long(self):
        # Get a sample from the HX711 in the form of raw bytes.
        dataBytes = self.readRawBytes()


        if self.DEBUG_PRINTING:
            print dataBytes,
        
        # Join the raw bytes into a single 24bit 2s complement value.
        twosComplementValue = ((dataBytes[0] << 16) |
                               (dataBytes[1] << 8)  |
                               dataBytes[2])

        if self.DEBUG_PRINTING:
            print "Twos: 0x%06x" % twosComplementValue
        
        # Convert from 24bit twos-complement to a signed value.
        signedIntValue = self.convertFromTwosComplement24bit(twosComplementValue)

        # Record the latest sample value we've read.
        self.lastVal = signedIntValue

        # Return the sample value we've read from the HX711.
        return long(signedIntValue)

    
    def read_average(self, times=3):
        # If we're only average across one value, just read it and return it.
        if times == 1:
            return self.read_long()

        # If we're averages across a low amount of values, just take an
        # arithmetic mean.
        if times < 5:
            values = long(0)
            for i in range(times):
                values += self.read_long()

            return values / times

        # If we're taking a lot of samples, we'll collect them in a list, remove
        # the outliers, then take the mean of the remaining set.
        valueList = []

        for x in range(times):
            valueList += [self.read_long()]

        valueList.sort()

        # We'll be trimming 20% of outlier samples from top and bottom of collected set.
        trimAmount = int(len(valueList) * 0.2)

        # Trim the edge case values.
        valueList = valueList[trimAmount:-trimAmount]

        # Return the mean of remaining samples.
        return sum(valueList) / len(valueList)

    
    def get_value(self, times=3):
        return self.read_average(times) - self.OFFSET

    
    def get_weight(self, times=3):
        value = self.get_value(times)
        value = value / self.REFERENCE_UNIT
        return value

    
    def tare(self, times=15):      
        # Backup REFERENCE_UNIT value
        reference_unit = self.REFERENCE_UNIT
        self.set_reference_unit(1)

        value = self.read_average(times)

        if self.DEBUG_PRINTING:
            print "Tare value:", value
        
        self.set_offset(value)

        # Restore the reference unit, now that we've got our offset.
        self.set_reference_unit(reference_unit)

        return value;

    
    def set_reading_format(self, byte_format="LSB", bit_format="MSB"):

        if byte_format == "LSB":
            self.byte_format = byte_format
        elif byte_format == "MSB":
            self.byte_format = byte_format
        else:
            print "Unrecognised byte_format: \"%s\"" % byte_format

        if bit_format == "LSB":
            self.bit_format = bit_format
        elif bit_format == "MSB":
            self.bit_format = bit_format
        else:
            print "Unrecognised bit_format: \"%s\"" % bit_format

            

    def set_offset(self, offset):
        self.OFFSET = offset

        
    def get_offset(self):
        return self.OFFSET

    
    def set_reference_unit(self, reference_unit):
        # Make sure we aren't asked to use an invalid reference unit.
        if reference_unit == 0:
            print "HX711().set_reference_unit(): Can't use 0 as a reference unit!!"
            return

        self.REFERENCE_UNIT = reference_unit


    def power_down(self):
        # Wait for and get the Read Lock, incase another thread is already
        # driving the HX711 serial interface.
        self.readLock.acquire()

        # Cause a rising edge on HX711 Digital Serial Clock (PD_SCK).  We then
        # leave it held up and wait 100 us.  After 60us the HX711 should be
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

        # HX711 will now be defaulted to Channel A with gain of 128.  Consider
        # automatically handling this.
        if self.get_gain() != 128:
            print "HX711().power_up(): Warning!  HX711 now set to Channel A with gain of 128."


    def reset(self):
        self.power_down()
        self.power_up()


# EOF - hx711.py
