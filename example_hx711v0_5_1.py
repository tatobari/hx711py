import time
import sys
import RPi.GPIO as GPIO
from hx711v0_5_1 import HX711

'''
About READ_MODE
----------------

If set to "interrupt based" (--interrupt_based), sets the class to use the "GPIO.add_event_detect"
to know when to poll and execute the passed callback.

If set to "polling based" (--polling_based), sets the example polls a new value from the HX711 using
the readRawBytes() method, which will wait until the HX711 is ready.
'''
READ_MODE_INTERRUPT_BASED = "--interrupt-based"
READ_MODE_POLLING_BASED = "--polling-based"
READ_MODE = READ_MODE_INTERRUPT_BASED

if len(sys.argv) > 1 and sys.argv[1] == READ_MODE_POLLING_BASED:
    READ_MODE = READ_MODE_POLLING_BASED
    print("[INFO] Read mode is 'polling based'.")
else:
    print("[INFO] Read mode is 'interrupt based'.")
    

hx = HX711(5, 6)

def printRawBytes(rawBytes):
    print(f"[RAW BYTES] {rawBytes}")

def printLong(rawBytes):
    print(f"[LONG] {hx.rawBytesToLong(rawBytes)}")

def printLongWithOffset(rawBytes):
    print(f"[LONG WITH OFFSET] {hx.rawBytesToLongWithOffset(rawBytes)}")

def printWeight(rawBytes):
    print(f"[WEIGHT] {hx.rawBytesToWeight(rawBytes)} gr")

def printAll(rawBytes):
    longValue = hx.rawBytesToLong(rawBytes)
    longWithOffsetValue = hx.rawBytesToLongWithOffset(rawBytes)
    weightValue = hx.rawBytesToWeight(rawBytes)
    print(f"[INFO] INTERRUPT_BASED | longValue: {longValue} | longWithOffsetValue: {longWithOffsetValue} | weight (grams): {weightValue}")

def getRawBytesAndPrintAll():
    rawBytes = hx.getRawBytes()
    longValue = hx.rawBytesToLong(rawBytes)
    longWithOffsetValue = hx.rawBytesToLongWithOffset(rawBytes)
    weightValue = hx.rawBytesToWeight(rawBytes)
    print(f"[INFO] POLLING_BASED | longValue: {longValue} | longWithOffsetValue: {longWithOffsetValue} | weight (grams): {weightValue}")

'''
About the reading format.
----------------
I've found out that, for some reason, the order of the bytes is not always the same between versions of python,
and the hx711 itself. I still need to figure out why.

If you're experiencing super random values, switch these values between `MSB` and `LSB` until you get more stable values.
There is some code below to debug and log the order of the bits and the bytes.

The first parameter is the order in which the bytes are used to build the "long" value. The second paramter is
the order of the bits inside each byte. According to the HX711 Datasheet, the second parameter is MSB so you
shouldn't need to modify it.
'''
hx.setReadingFormat("MSB", "MSB")

print("[INFO] Automatically setting the offset.")
hx.autosetOffset()
offsetValue = hx.getOffset()
print(f"[INFO] Finished automatically setting the offset. The new value is '{offsetValue}'.")

print("[INFO] You can add weight now!")

'''
# HOW TO CALCULATE THE REFFERENCE UNIT
1. Set the reference unit to 1 and make sure the offset value is set.
2. Load you sensor with 1kg or with anything you know exactly how much it weights.
3. Write down the 'long' value you're getting. Make sure you're getting somewhat consistent values.
    - This values might be in the order of millions, varying by hundreds or thousands and it's ok.
4. To get the wright in grams, calculate the reference unit using the following formula:
        
    referenceUnit = longValueWithOffset / 1000
        
In my case, the longValueWithOffset was around 114000 so my reference unit is 114,
because if I used the 114000, I'd be getting milligrams instead of grams.
'''

referenceUnit = 114
print(f"[INFO] Setting the 'referenceUnit' at {referenceUnit}.")
hx.setReferenceUnit(referenceUnit)
print(f"[INFO] Finished setting the 'referenceUnit' at {referenceUnit}.")

if READ_MODE == READ_MODE_INTERRUPT_BASED:
    print("[INFO] Enabling the callback.")
    hx.enableReadyCallback(printAll)
    print("[INFO] Finished enabling the callback.")


while True:
    try:
        if READ_MODE == READ_MODE_POLLING_BASED:
            getRawBytesAndPrintAll()
            
    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        print("[INFO] 'KeyboardInterrupt Exception' detected. Cleaning and exiting...")
        sys.exit()
        