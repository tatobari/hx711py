import time
import RPi.GPIO as GPIO
from hx711 import HX711

# Setup HX711
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(1)
hx.reset()
hx.tare()

# Configuration
num_samples = 15

print(f"Place known weight on scale and enter it's weight in grams:",end="")
known_weight = int(input())

# Collect samples
print("Collecting samples...")
samples = []
for i in range(num_samples):
    reading = hx.get_weight(1)
    samples.append(reading)
    time.sleep(0.2)

# Remove outliers (simple method: remove top and bottom 20%)
samples.sort()
clean_samples = samples[3:-3]  # Remove 3 highest and 3 lowest

# Calculate reference unit
average = sum(clean_samples) / len(clean_samples)
reference_unit = average / known_weight

print(f"\nAverage reading: {average:.1f}")
print(f"Reference unit: {reference_unit:.2f}")
print(f"\nAdd this to your script:")
print(f"hx.set_reference_unit({reference_unit:.2f})")

GPIO.cleanup()