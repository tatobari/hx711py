import time
import RPi.GPIO as GPIO # Baked into Raspbian Python, don't need to setup 
from hx711 import HX711 # Sensor
import logging
# Init sensor
weight_sensor = HX711(16, 20)

# Set reading format
weight_sensor.set_reading_format("MSB", "MSB")
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
reference_unit = 1220
weight_sensor.set_reference_unit(reference_unit)
weight_sensor.reset()
weight_sensor.tare()
logging.info(f"Tare done! Weight measurement should be accurate now...")

def get_current_weight(num_of_reads=5):
    # Get weight
    curr_weight = weight_sensor.get_weight(times=num_of_reads) # Gets 5 reads by default
    logging.info(f"Weight Reading: {curr_weight}")
    # Power down
    logging.info(f"Powering sensor down...")
    weight_sensor.power_down()
    weight_sensor.power_up()
    time.sleep(0.1)
    return curr_weight

