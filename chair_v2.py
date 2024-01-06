
import time
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Instantiate logger
from logging_handler import get_kafka_logger
BROKER = os.getenv('BROKER')
device_name = "chair-sensor-1"
topic = 'log-topic'
logger = get_kafka_logger(BROKER, topic, device_name)

# Instantiate the HueController
from hue_controller import HueController
BRIDGE_IP = os.getenv('BRIDGE_IP')
USER_TOKEN = os.getenv('USER_TOKEN')
light_id = 47  
hue = HueController(BRIDGE_IP, USER_TOKEN)

EMULATE_HX711=False
referenceUnit = -441

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

def cleanAndExit():
    logger.info("Cleaning up and exiting.")
    if not EMULATE_HX711:
        GPIO.cleanup()
    sys.exit()

hx = HX711(6, 5)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()
hue.turn_on_light(light_id)
hue.turn_off_light(light_id)

logger.info("Tare done! Add weight now...")

is_weight_above_600 = False

while True:
    try:
        val = hx.get_weight(5)
        # logger.info(f"Weight value read: {val}")

        # Check if the weight crosses the threshold and update the flag
        if val < -600 and not is_weight_above_600:
            is_weight_above_600 = True
            logger.info("{val} - Weight below -600, turning on light.")
            hue.turn_on_light(light_id)

        elif val >= -600 and is_weight_above_600:
            is_weight_above_600 = False
            logger.info("{val} - Weight above -600, turning off light.")
            hue.turn_off_light(light_id)

        # hx.power_down()
        # hx.power_up()
        time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
    except Exception as e:
        logger.error("An error occurred: " + str(e))
        hx.power_down()
        time.sleep(1) # Delay for sensor stabilization
        hx.power_up()
        time.sleep(1) 
        # cleanAndExit()
