import RPi.GPIO as GPIO
import time
import threading

class HX711:

    def __init__(self, dout, pd_sck, gain=128):
        self.PD_SCK = pd_sck

        self.DOUT = dout

        # Mutex for reading from the HX711, in case multiple threads in client
        # software try to access get values from the class at the same time.
        self.readLock = threading.Lock()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PD_SCK, GPIO.OUT)
        GPIO.setup(self.DOUT, GPIO.IN)

        # The value returned by the hx711 that corresponds to your reference
        # unit AFTER dividing by the SCALE.
        self.REFERENCE_UNIT_A = 1
        self.REFERENCE_UNIT_B = 1

        self.OFFSET_A = 1
        self.OFFSET_B = 1
        self.lastVal = int(0)

        self.byteFormat = 'MSB' # 'MSB' or 'LSB'
        self.bitFormat = 'MSB' # 'MSB' or 'LSB'
        
        # GAIN must be between 1 and 3. None is an invalid value.
        self.GAIN = None
        self.setGain(gain)


        # Think about whether this is necessary.
        time.sleep(1)

        
        # Think about whether this is necessary.
        time.sleep(1)
        
        self.readyCallbackEnabled = False
        self.paramCallback = None
        self.lastRawBytes = None


    def powerDown(self):
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


    def powerUp(self):
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
        if self.getGain() != 128:
            self.readRawBytes()


    def reset(self):
        self.powerDown()
        self.powerUp()


    def isReady(self):
        return GPIO.input(self.DOUT) == GPIO.LOW


    def setGain(self, gain):
        
        if gain == 128:
            self.GAIN = 1
        elif gain == 64:
            self.GAIN = 3
        elif gain == 32:
            self.GAIN = 2
        else:
            return False
        
        self.reset()

        GPIO.output(self.PD_SCK, False)

        # Read out a set of raw bytes and throw it away.
        self.readRawBytes()
        
        return True


    def getGain(self):
        if self.GAIN == 1:
            return 128
        elif self.GAIN == 3:
            return 64
        elif self.GAIN == 2:
            return 32

        raise ValueError("HX711::getGain() gain is currently an invalid value")


    def setChannel(self, channel='A'):
        if channel == 'A':
            self.setGain(128)
            return True
        elif channel == 'B':
            self.setGain(32)
            return True
        
        raise ValueError("HX711::setChannel() invalid channel: \"%s\"" % channel)

    
    def getChannel(self):
        if self.GAIN == 1:
            return 'A'
        elif self.GAIN == 3:
            return 'A'
        elif self.GAIN == 2:
            return 'B'
        
        raise ValueError("HX711::getChannel() gain is currently an invalid value")


    def readNextBit(self):
       # Clock HX711 Digital Serial Clock (PD_SCK).  DOUT will be
       # ready 1us after PD_SCK rising edge, so we sample after
       # lowering PD_SCL, when we know DOUT will be stable.
       GPIO.output(self.PD_SCK, True)
       GPIO.output(self.PD_SCK, False)
       bitValue = GPIO.input(self.DOUT)

       # Convert Boolean to int and return it.
       return int(bitValue)


    def readNextByte(self):
       byteValue = 0

       # Read bits and build the byte from top, or bottom, depending
       # on whether we are in MSB or LSB bit mode.
       for x in range(8):
            if self.bitFormat == 'MSB':
                # Most significant Byte first.
                byteValue <<= 1
                byteValue |= self.readNextBit()
            else:
                # Less significant Byte first.
                byteValue >>= 1              
                byteValue |= self.readNextBit() * 0x80

       # Return the packed byte.
       return byteValue 


    def readRawBytes(self, blockUntilReady=True):
        
        if self.GAIN is None:
            raise ValueError("HX711::readRawBytes() called without setting gain first!")
        
        # Try to get the Read Lock. If we can't, we lost our opportunity to read.
        # Though this behaviour is not ideal, it seems key to avoid time consuming interrupt handlers.
        if self.readLock.acquire(blockUntilReady) is False:
            # If we couldn't get the lock, it's probably because someone else
            # is reading the HX711 right now.  We'll just skip this reading and
            # return None.
            return None

        # Wait until HX711 is ready for us to read a sample.
        while self.isReady() is not True:
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

        # Depending on how we're configured, return an orderd list of raw byte values.
        if self.byteFormat == 'MSB':
            # Most significant Byte first.
            return [firstByte, secondByte, thirdByte]
        else:
            # Less Significant Byte first.
            return [thirdByte, secondByte, firstByte]

    def getRawBytes(self, channel='A'):
        
        # Get current channel
        currentChannel = self.getChannel()
        
        # Compare the requested channel with the current channel
        if channel != currentChannel:
            # Temporarily switch to the requested channel
            self.setChannel(channel)
        
        rawBytes = self.readRawBytes()
        
        # Compare the requested channel with the current channel
        if channel != currentChannel:
            # Switch back to the original channel
            self.setChannel(currentChannel)
        
        return rawBytes


    def getLastRawBytes(self):
        rawBytes = self.lastRawBytes
        self.lastRawBytes = None
        return rawBytes


    def readyCallback(self, pin):
        # Check if the callback is for the DOUT pin.
        if(pin != self.DOUT):
            return
        
        self.lastRawBytes = self.readRawBytes(blockUntilReady=False)
        if self.paramCallback is not None:
            self.paramCallback(self.lastRawBytes)

    
    def enableReadyCallback(self, paramCallback=None):
        self.paramCallback = paramCallback if paramCallback is not None else self.paramCallback
        GPIO.add_event_detect(self.DOUT, GPIO.FALLING, callback=self.readyCallback)
        self.readyCallbackEnabled = True

    
    def disableReadyCallback(self):
        GPIO.remove_event_detect(self.DOUT)
        self.paramCallback = None
        self.readyCallbackEnabled = False


    def setReadingFormat(self, byteFormat="MSB", bitFormat="MSB"):
        
        if byteFormat != 'MSB' and byteFormat != 'LSB':
            raise ValueError(f"HX711::setReadingFormat() invalid byteFormat: '{byteFormat}'" )
        
        if bitFormat != 'MSB' and bitFormat != 'LSB':
            raise ValueError(f"HX711::setReadingFormat() invalid bitFormat: '{byteFormat}'" )
        
        self.byteFormat = byteFormat
        self.bitFormat = bitFormat

    
    def convertFromTwosComplement24bit(self, inputValue):
        return -(inputValue & 0x800000) + (inputValue & 0x7fffff)

    
    def rawBytesToLong(self, rawBytes=None):
        
        if rawBytes is None:
            return None

        # Join the raw bytes into a single 24bit 2s complement value.
        twosComplementValue = ((rawBytes[0] << 16) |
                               (rawBytes[1] << 8)  |
                               rawBytes[2])
        
        # Convert from 24bit twos-complement to a signed value.
        signed_int_value = self.convertFromTwosComplement24bit(twosComplementValue)

        # Record the latest sample value we've read.
        self.lastVal = signed_int_value

        # Return the sample value we've read from the HX711.
        return int(signed_int_value)


    def getLong(self, channel='A'):
                
        currentChannel = self.getChannel()
        if channel != currentChannel:
            self.setChannel(channel)
        
        # Get a sample from the HX711 in the form of raw bytes.
        rawBytes = self.readRawBytes()
        
        if channel != currentChannel:
            self.setChannel(currentChannel)
        
        if rawBytes is None:
            return None
        
        return self.rawBytesToLong(rawBytes)


    def setOffset(self, offset, channel='A'):
        if channel == 'A':
            self.OFFSET_A = offset
            return True
        elif channel == 'B':
            self.OFFSET_B = offset
            return True
        
        raise ValueError("HX711::setOffset() invalid channel: \"%s\"" % channel)


    def setOffsetA(self, offset):
        return self.setOffset(offset, 'A')


    def setOffsetB(self, offset):
        return self.setOffset(offset, 'B')


    def getOffset(self, channel='A'):
        if channel == 'A':
            return self.OFFSET_A
        elif channel == 'B':
            return self.OFFSET_B
        
        raise ValueError("HX711::getOffset() invalid channel: \"%s\"" % channel)


    def getOffsetA(self):
        return self.getOffset('A')


    def getOffsetB(self):
        return self.getOffset('B')
    
    
    def rawBytesToLongWithOffset(self, rawBytes=None, channel='A'):
        
        if rawBytes is None:
            return None
        
        longValue = self.rawBytesToLong(rawBytes)
        offset = self.getOffset(channel)
        return longValue - offset


    def getLongWithOffset(self, channel='A'):
        
        currentChannel = self.getChannel()
        if channel != currentChannel:
            self.setChannel(channel)
        
        rawBytes = self.readRawBytes()
        
        if channel != currentChannel:
            self.setChannel(currentChannel)
        
        if rawBytes is None:
            return None
        
        return self.rawBytesToLongWithOffset(rawBytes, channel)
    
 
    def setReferenceUnit(self, referenceUnit, channel='A'):
        if channel == 'A':
            self.REFERENCE_UNIT_A = referenceUnit
            return True
        elif channel == 'B':
            self.REFERENCE_UNIT_B = referenceUnit
            return True
        
        raise ValueError("HX711::setReferenceUnit() invalid channel: \"%s\"" % channel)
    
    
    def getReferenceUnit(self, channel='A'):
        if channel == 'A':
            return self.REFERENCE_UNIT_A
        elif channel == 'B':
            return self.REFERENCE_UNIT_B
        
        raise ValueError("HX711::getReferenceUnit() invalid channel: \"%s\"" % channel)

    
    def rawBytesToWeight(self, rawBytes=None, channel='A'):
        
        if rawBytes is None:
            return None
        
        longWithOffset = self.rawBytesToLongWithOffset(rawBytes, channel)
        
        if channel == 'A':
            referenceUnit = self.REFERENCE_UNIT_A
        elif channel == 'B':
            referenceUnit = self.REFERENCE_UNIT_B
        else:
            raise ValueError("HX711::rawBytesToWeight() invalid channel: \"%s\"" % channel)
        
        if referenceUnit == 0:
            raise ValueError("HX711::rawBytesToWeight() referenceUnit is 0. It isn't possible to divide by zero!")
        
        return longWithOffset / referenceUnit

    
    def getWeight(self, channel='A'):
        
        currentChannel = self.getChannel()
        if channel != currentChannel:
            self.setChannel(channel)
        
        rawBytes = self.readRawBytes()
        
        if channel != currentChannel:
            self.setChannel(currentChannel)
        
        if rawBytes is None:
            return None
        
        return self.rawBytesToWeight(rawBytes, channel)


    def autosetOffset(self, channel='A'):
        
        currentReferenceUnit = self.getReferenceUnit(channel)
        
        self.setReferenceUnit(1, channel)
        
        currentChannel = self.getChannel()
        if channel != currentChannel:
            self.setChannel(channel)
            
        newOffsetValue = self.getLong(channel)
        
        self.setOffset(newOffsetValue, channel)
        
        self.setReferenceUnit(currentReferenceUnit, channel)
        
        if channel != currentChannel:
            self.setChannel(currentChannel)
        
        return True
    
# EOF - hx711.py
