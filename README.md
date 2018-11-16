# HX711 for Raspbery Py
----
Quick code credited to [underdoeg](https://github.com/underdoeg/)'s [Gist HX711.py](https://gist.github.com/underdoeg/98a38b54f889fce2b237).
I've only made a few modifications on the way the captured bits are processed and to support Two's Complement, which it didn't.

Instructions
------------
Check example.py to see how it works.

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

