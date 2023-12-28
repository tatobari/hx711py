import logging
import time
import sys



EMULATE_HX711=False
referenceUnit = -441

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

# Import the HueController class from hue_controller.py
from hue_controller import HueController

# Instantiate the HueController
BRIDGE_IP = '192.168.1.46'
USER_TOKEN = 'BplzC08YY96lJDa8IT8EjaW9KcvvU87Ubn68il7u'
light_id = 47  # Replace with your specific light ID
hue = HueController(BRIDGE_IP, USER_TOKEN)


def cleanAndExit():
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print("Bye!")
    sys.exit()

hx = HX711(6, 5)

hx.set_reading_format("MSB", "MSB")

hx.set_reference_unit(referenceUnit)

hx.reset()

hx.tare()

print("Tare done! Add weight now...")



# Setup logging
logging.basicConfig(filename='weight_light_control.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def cleanAndExit():
    logging.info("Cleaning up and exiting.")
    # Add any cleanup code here
    exit()


is_weight_above_600 = False

while True:
    try:
        val = hx.get_weight(5)
        # logging.info(f"Weight value read: {val}")

        # Check if the weight crosses the threshold and update the flag
        if val < -600 and not is_weight_above_600:
            is_weight_above_600 = True
            logging.info("Weight below -600, turning on light.")
            hue.turn_on_light(light_id)

        elif val >= -600 and is_weight_above_600:
            is_weight_above_600 = False
            logging.info("Weight above -600, turning off light.")
            hue.turn_off_light(light_id)

        # hx.power_down()
        # hx.power_up()
        time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
    except Exception as e:
        logging.error("An error occurred: " + str(e))
        hx.power_down()
        time.sleep(1) # Delay for sensor stabilization
        hx.power_up()
        time.sleep(1) 
        # cleanAndExit()
