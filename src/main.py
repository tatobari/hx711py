#! /usr/bin/python2

import time
import sys
from PyQt5.QtWidgets import *
import numpy
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
import os

def main():
    app =QApplication([]) # create a window
    window = QWidget()
    
    runButton = QPushButton(window) # run button
    runButton.setText("Run")
    runButton.move(50, 50)
    runButton.clicked.connect(getVals)

    exitButton = QPushButton(window) # exit button
    exitButton.setText("Exit")
    exitButton.move(50, 100)
    exitButton.clicked.connect(cleanAndExit)

    window.show() # show window
    app.exec_()

def cleanAndExit(): # function to clean and close the system
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()

    print("Bye!")
    sys.exit()

def getVals(): # function containing the weight data collection
   

   # if os.environ.get('DISPLAY','') == '':
   #     print('no display found. Using :0.0')
   #     os.environ.__setitem__('DISPLAY', ':0.0')

    # measurement begins here

   # EMULATE_HX711=False

   # referenceUnit = 1

   # if not EMULATE_HX711:
   #     import RPi.GPIO as GPIO
   #     from hx711 import HX711
   # else:
   #     from emulated_hx711 import HX711
        
    hx1 = HX711(20, 21) # top left
    hx2 = HX711(13, 19) # bottom left
    hx3 = HX711(14, 15) # top right
    hx4 = HX711(2, 3) # bottom right

# I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
# Still need to figure out why does it change.
# If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
# There is some code below to debug and log the order of the bits and the bytes.
# The first parameter is the order in which the bytes are used to build the "long" value.
# The second paramter is the order of the bits inside each byte.
# According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
    hx1.set_reading_format("MSB", "MSB")
    hx2.set_reading_format("MSB", "MSB")
    hx3.set_reading_format("MSB", "MSB")
    hx4.set_reading_format("MSB", "MSB")


# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
#hx.set_reference_unit(113)
    hx1.set_reference_unit(referenceUnit)
    hx2.set_reference_unit(referenceUnit)
    hx3.set_reference_unit(referenceUnit)
    hx4.set_reference_unit(referenceUnit)

    hx1.reset()
    hx2.reset()
    hx3.reset()
    hx4.reset()

    hx1.tare()
    hx2.tare()
    hx3.tare()
    hx4.tare()

    print("Tare done! Add weight now...")
    while True:
        try:
        # These three lines are usefull to debug wether to use MSB or LSB in the reading formats
        # for the first parameter of "hx.set_reading_format("LSB", "MSB")".
        # Comment the two lines "val = hx.get_weight(5)" and "print val" and uncomment these three lines to see what it prints.

        # np_arr8_string = hx.get_np_arr8_string()
        # binary_string = hx.get_binary_string()
        # print binary_string + " " + np_arr8_string

        # Prints the weight. Comment if you're debbuging the MSB and LSB issue.
            val1 = hx1.get_weight(5) * -1
            val2 = hx2.get_weight(5) * -1
            val3 = hx3.get_weight(5) * -1
            val4 = hx4.get_weight(5) * -1
        # print(val1)

        # To get weight from both channels (if you have load cells hooked up 
        # to both channel A and B), do something like this
        #val_A = hx.get_weight_A(5)
        #val_B = hx.get_weight_B(5)
            print("1: %s  2: %s 3: %s 4: %s", val1, val2, val3, val4)

            hx1.power_down()
            hx1.power_up()
            hx2.power_down()
            hx2.power_up()
            hx3.power_down()
            hx3.power_up()
            hx4.power_down()
            hx4.power_up()

            time.sleep(0.4)

        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()

if __name__ == '__main__':
    if os.environ.get('DISPLAY','') == '':
        print('no display found. Using :0.0')
        os.environ.__setitem__('DISPLAY', ':0.0')

    # measurement begins here

    EMULATE_HX711=False

    referenceUnit = 1

    if not EMULATE_HX711:
        import RPi.GPIO as GPIO
        from hx711 import HX711
    else:
        from emulated_hx711 import HX711
     
    main()
