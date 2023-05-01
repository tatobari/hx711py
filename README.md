# UTK Mechanical Engineering Senior Design Project

Task: Design and create a one-plane swing trainer to help instruct new golfers to learn
& feel the "one-plane swing"

Implementation: The team has elected to design their own weight distribution sensor by implementing load cell readings with a raspberry pi interface to display the status and tracking of the client's center of gravity in relation to space. 

The 'User' will be the Pro giving the lesson and is intended to be used as a tool to shed light on undesirable habits in beginner golfers.

The raspberry pi interface runs off the hx711 amplifier and accompanied software for use with the raspberry pi that can be downloaded [here](https://github.com/tatobari/hx711py) or by cloning this repository.

```
git clone https://github.com/tatobari/hx711py
```

## Advisor

Dr. William Miller

## Members

Christian White

Robert Vandergriff

Job Dooley

Chilo Espinoza

[Will Buziak](https://github.com/wbuz24/Undergrad-Repo/blob/master/S23/will-buziak-resume.pdf)

## Sponsor
[Fairways and Greens](https://fairwaysandgreens.com/)


## HX711 for Raspberry Py
----
This repository was forked from [Tatobari's](https://github.com/tatobari) [HX711 repo](https://github.com/tatobari/hx711py). The following is quoted from that repository's README.md with slight changes to reflect how it works within this fork. 

----
Quick code credited to [underdoeg](https://github.com/underdoeg/)'s [Gist HX711.py](https://gist.github.com/underdoeg/98a38b54f889fce2b237).
I've only made a few modifications on the way the captured bits are processed and to support Two's Complement, which it didn't.

Update: 25/02/2021
----
For the past years I haven't been able to maintain this library because I had too much workload. Now I'm back and I've been working on a few fixes and modifications to simplify this library, and I might be commiting the branch by mid-March. I will also publish it to PIP.

Instructions
------------
The source code can be found in src/main.py

For compiling and running through the command line, python3 is necessary.

Other dependencies include:
 - PyQt5 (included in python3 installation)
 - RPi.GPIO
 - Git


Installation
------------
1. Clone or download and unpack this repository
2. In the repository directory, run
```
python3 src/setup.py install
```

Compilation
-----------
```
python3 src/main.py
```

Using a 2-channel HX711 module
------------------------------
Channel A has selectable gain of 128 or 64.  Using set_gain(128) or set_gain(64)
selects channel A with the specified gain.

Using set_gain(32) selects channel B at the fixed gain of 32.  The tare_B(),
get_value_B() and get_weight_B() functions do this for you.

This info was obtained from an HX711 datasheet located at
https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf

