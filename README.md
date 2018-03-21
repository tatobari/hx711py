hx711.py
--------
Forked from https://github.com/tatobari/hx711py to add support for tare/offsets
for both channels of a 2-channel HX711.

Original tare(), set_offset(), set_reference_unit(), get_value(), get_weight()
functions call their channel A versions to retain backwards compatibility.  
Likewise, self.OFFSET and self.REFERENCE_UNIT are updated whenever the channel A
versions are updated, also for compatibility.

I also added a read_median() function that works like the current read_average()
function, but returns the median of the samples instead of the average.  The
hope is that this method will help smooth out some spikes in the data that I
think are CPU load related (I'm using this on a Pi Zero W).  The tare() and
get_value() functions have been converted to use this method instead of 
read_average().

Installation
------------
1. Clone or download and unpack this repository
2. In the repository directory, run
```
python setup.py install
```

Using a 2-channel HX711 module
------------------------------
Channel A has selectable gain of 128 or 64.  Using set_gain(128) or set_gain(64)
selects channel A with the specified gain.

Using set_gain(32) selects channel B at the fixed gain of 32.  The tare_B(),
get_value_B() and get_weight_B() functions do this for you.

This info was obtained from an HX711 datasheet located at
https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf

TODO:
-----
  * Incorporate a method for calculating reference value based off of a known
    mass.
  * Update example.py to handle both channels.

Original README
---------------

Info
----
Quick code credited to Philip Whitfield  "https://github.com/underdoeg/".
I've only made a few modifications on the way the captured bits are processed.

Instructions
------------
Check example.py to see how it works.
