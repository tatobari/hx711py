import RPi.GPIO as GPIO

def cleanup_gpio_pins():
    GPIO.cleanup()

if __name__ == "__main__":
    cleanup_gpio_pins()
