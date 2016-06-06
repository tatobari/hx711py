import RPi.GPIO as GPIO
import time
import sys
import numpy  # sudo apt-get python-numpy


def createBoolList(size=8):
    ret = []
    for i in range(8):
        ret.append(False)
    return ret


def cleanAndExit():
    print "Cleaning..."
    GPIO.cleanup()
    print "Bye!"
    sys.exit()


class HX711:
    def __init__(self, dout, pd_sck, gain=128):
        self.PD_SCK = pd_sck
        self.DOUT = dout

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PD_SCK, GPIO.OUT)
        GPIO.setup(self.DOUT, GPIO.IN)

        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1
        self.ONE_KILO = 1
        self.lastVal = 0

        #GPIO.output(self.PD_SCK, True)
        #GPIO.output(self.PD_SCK, False)

        self.set_gain(gain)

        time.sleep(1)

    def is_ready(self):
        return GPIO.input(self.DOUT) == 0

    def set_gain(self, gain):
        if gain is 128:
            self.GAIN = 1
        elif gain is 64:
            self.GAIN = 3
        elif gain is 32:
            self.GAIN = 2

        GPIO.output(self.PD_SCK, False)
        self.read()

    def read(self):
        while not self.is_ready():
            #print("WAITING")
            pass

        dataBits = [createBoolList(), createBoolList(), createBoolList()]
        dataBytes = [0x0] * 4

        for j in range(2, -1, -1):
            for i in range(0, 8):
                GPIO.output(self.PD_SCK, True)
                dataBits[j][i] = GPIO.input(self.DOUT)
                GPIO.output(self.PD_SCK, False)
            dataBytes[j] = numpy.packbits(numpy.uint8(dataBits[j]))

        #set channel and gain factor for next reading
        for i in range(self.GAIN):
            GPIO.output(self.PD_SCK, True)
            GPIO.output(self.PD_SCK, False)

        #check for all 1
        #if all(item is True for item in dataBits[0]):
        #    return int(self.lastVal)

        dataBytes[2] ^= 0x80
        np_arr8 = numpy.uint8(dataBytes)
        np_arr32 = np_arr8.view('uint32')
        self.lastVal = np_arr32

        return int(self.lastVal)

    def read_average(self, times=3):
        values = 0
        for i in range(times):
            values += self.read()

        return values / times

    def get_value(self, times=3):
        return self.read_average(times) - self.OFFSET

    def get_units(self, times=3):
        return self.get_value(times) / self.SCALE

    def get_weight(self, times=3):
        return ("%.3f" % float(float(self.get_units(times)) / float(self.ONE_KILO)))

    def tare(self, times=15):
        # Backup SCALE value
        scale = self.SCALE
        self.set_scale(1)

        # Backup ONE_KILO VALUE
        one_kilo = self.ONE_KILO
        self.set_one_kilo(1)

        value = self.read_average(times)
        self.set_offset(value)

        self.set_scale(scale)
        self.set_one_kilo(one_kilo)

    def set_scale(self, scale):
        self.SCALE = scale

    def set_offset(self, offset):
        self.OFFSET = offset

    def set_one_kilo(self, one_kilo):
        self.ONE_KILO = one_kilo

    # HX711 datasheet states that setting the PDA_CLOCK pin on high for a more than 60 microseconds would power off the chip.
    # I'd recommend it to prevent noise from messing up with it. I used 100 microseconds, just in case.
    def power_down(self):
        GPIO.output(self.PD_SCK, False)
        GPIO.output(self.PD_SCK, True)
        time.sleep(0.0001)

    def power_up(self):
        GPIO.output(self.PD_SCK, False)
        time.sleep(0.0001)

############# EXAMPLE
hx = HX711(5, 6)
hx.set_scale(1000)
hx.set_one_kilo(92)
hx.power_down()
hx.power_up()
hx.tare()

while True:
    try:
        val = hx.get_weight(5)
        print val

        hx.power_down()
        hx.power_up()
        time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
