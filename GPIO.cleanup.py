import RPi.GPIO as GPIO

# Use BCM GPIO numbering
GPIO.setmode(GPIO.BCM)

# Clean up all GPIO pins
GPIO.cleanup()

print("All GPIO pins have been cleaned up.")
