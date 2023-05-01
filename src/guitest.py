import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
import time
import sys
from PyQt5.QtWidgets import *

 
class WeighingSystem(object):

    def __init__(self, pi):
        self.last_count1 = -1
        self.last_count2 = -1
        self.last_count3 = -1
        self.last_count4 = -1
        self.scale_read1 = 0
        self.scale_read2 = 0
        self.scale_read3 = 0
        self.scale_read4 = 0
        self.s1 = HX711(pi, DATA_PIN=20, CLOCK_PIN=21, mode=HX711.CH_A_GAIN_128, callback=self.scale1_read_cb)
        self.s2 = HX711(pi, DATA_PIN=13, CLOCK_PIN=19, mode=HX711.CH_A_GAIN_128, callback=self.scale2_read_cb)
        self.s3 = HX711(pi, DATA_PIN=14, CLOCK_PIN=15, mode=HX711.CH_A_GAIN_128, callback=self.scale3_read_cb)
        self.s4 = HX711(pi, DATA_PIN=2, CLOCK_PIN=3, mode=HX711.CH_A_GAIN_128, callback=self.scale4_read_cb)

        self.s1.start()
        time.sleep(2)
        self.s2.start()
        time.sleep(2)
        self.s3.start()
        time.sleep(2)
        self.s4.start()
        time.sleep(2)
        print("both start!!")

    def scale1_read_cb(self, count, mode, reading):
        if count!=self.last_count1:
            self.scale_read1 = reading
            self.last_count1 = count

    def scale2_read_cb(self, count, mode, reading):
        if count!=self.last_count2:
            self.scale_read2 = reading
            self.last_count2 = count
        
    def scale3_read_cb(self, count, mode, reading):
        if count!=self.last_count3:
            self.scale_read4 = reading
            self.last_count4 = count

    def scale4_read_cb(self, count, mode, reading):
        if count!=self.last_count4:
            self.scale_read4 = reading
            self.last_count4 = count

class HX711:
    CH_A_GAIN_64  = 0 # Channel A gain 64
    CH_A_GAIN_128 = 1 # Channel A gain 128
    CH_B_GAIN_32  = 2 # Channel B gain 32
    X_128_CLK = 25
    X_32_CLK  = 26
    X_64_CLK  = 27
    DATA_CLKS = 24
    PULSE_LEN = 15
    # If the data line goes low after being high for at least
    # this long it indicates that a new reading is available.
    TIMEOUT = ((X_64_CLK + 3) * 2 * PULSE_LEN)
    # The number of readings to skip after a mode change.
    SETTLE_READINGS = 5 # normally just one mode
    def __init__(self, pi, DATA_PIN, CLOCK_PIN, mode=CH_A_GAIN_128, callback=None):
        """
        Instantiate with the Pi, the data GPIO, and the clock GPIO.
        Optionally the channel and gain may be specified with the
        mode parameter as follows.
        CH_A_GAIN_64  - Channel A gain 64
        CH_A_GAIN_128 - Channel A gain 128
        CH_B_GAIN_32  - Channel B gain 32
        Optionally a callback to be called for each new reading may be
        specified.  The callback receives three parameters, the count,
        the mode, and the reading.  The count is incremented for each
        new reading.
        """
        self.pi = pi
        self.DATA = DATA_PIN
        self.CLOCK = CLOCK_PIN
        self.callback = callback

        self._paused = True
        self._data_level = 0
        self._clocks = 0

        self._mode = mode
        self._value = 0

        self._rmode = mode
        self._rval = 0
        self._count = 0

        self._sent = 0
        self._data_tick = pi.get_current_tick()
        self._previous_edge_long = False
        self._in_wave = False

        self._skip_readings = HX711.SETTLE_READINGS

        pi.write(CLOCK_PIN, 1) # Reset the sensor.

        pi.set_mode(DATA_PIN, pigpio.INPUT)

        pi.wave_add_generic(
            [pigpio.pulse(1<<CLOCK_PIN, 0, HX711.PULSE_LEN),
            pigpio.pulse(0, 1<<CLOCK_PIN, HX711.PULSE_LEN)])

        self._wid = pi.wave_create()
        # callback function for processing the gpio reading  
        self._cb1 = pi.callback(DATA_PIN, pigpio.EITHER_EDGE, self._callback)
        self._cb2 = pi.callback(CLOCK_PIN, pigpio.FALLING_EDGE, self._callback)
        self._cb3 = pi.callback(DATA_PIN, pigpio.EITHER_EDGE, self._callback)
        self._cb4 = pi.callback(CLOCK_PIN, pigpio.FALLING_EDGE, self._callback)

        self.set_mode(mode) 
    # user interface of reading
    def get_reading(self):
        """
        Returns the current count, mode, and reading.
        The count is incremented for each new reading.
        """
        return self._count, self._rmode, self._rval

    def set_callback(self, callback):
        """
        Sets the callback to be called for every new reading.
        The callback receives three parameters, the count,
        the mode, and the reading.  The count is incremented
        for each new reading.
        The callback can be cancelled by passing None.
        """
        self.callback = callback

    def set_mode(self, mode):
        """
        Sets the mode.
        CH_A_GAIN_64  - Channel A gain 64
        CH_A_GAIN_128 - Channel A gain 128
        CH_B_GAIN_32  - Channel B gain 32
        """
        self._mode = mode

        if mode == HX711.CH_A_GAIN_128:
            self._pulses = HX711.X_128_CLK
        elif mode == HX711.CH_B_GAIN_32:
            self._pulses = HX711.X_32_CLK
        elif mode == HX711.CH_A_GAIN_64:
            self._pulses = HX711.X_64_CLK
        else:
            raise ValueError

        self.pause()
        self.start()

    def pause(self):
        """
        Pauses readings.
        """
        self._skip_readings = HX711.SETTLE_READINGS
        self._paused = True
        self.pi.write(self.CLOCK, 1)
        time.sleep(0.002)
        self._clocks = HX711.DATA_CLKS + 1

    def start(self):
        """
        Starts readings.
        """
        self._wave_sent = False
        self.pi.write(self.CLOCK, 0)
        self._clocks = HX711.DATA_CLKS + 1
        self._value = 0
        self._paused = False
        self._skip_readings = HX711.SETTLE_READINGS

    def cancel(self):
        """
        Cancels the sensor and release resources.
        """
        self.pause()

        if self._cb1 is not None:
            self._cb1.cancel()
            self._cb1 = None

        if self._cb2 is not None:
            self._cb2.cancel()
            self._cb2 = None

        if self._cb3 is not None:
            self._cb3.cancel()
            self._cb3 = None

        if self._cb4 is not None:
            self._cb4.cancel()
            self._cb4 = None

        if self._wid is not None:
            self.pi.wave_delete(self._wid)
            self._wid = None

    def _callback(self, gpio, level, tick):
    #   interrupt from the clock pin
        if gpio == self.CLOCK:
            if level == 0:
                self._clocks += 1
                if self._clocks <= HX711.DATA_CLKS:
                    self._value = (self._value << 1) + self._data_level
                    if self._clocks == HX711.DATA_CLKS:
                        self._in_wave = False
                        if self._value & 0x800000: # unsigned to signed
                            self._value |= ~0xffffff
                        if not self._paused:
                            if self._skip_readings <= 0:
                                self._count = self._sent
                                self._rmode = self._mode
                                self._rval = self._value
                                if self.callback is not None:
                                    self.callback(self._count, self._rmode, self._rval)
                            else:
                                self._skip_readings -= 1
        else:
            self._data_level = level
            if not self._paused:
                if self._data_tick is not None:
                    current_edge_long = pigpio.tickDiff(self._data_tick, tick) > HX711.TIMEOUT
                    if current_edge_long and not self._previous_edge_long:
                        if not self._in_wave:
                            self._in_wave = True
                            self.pi.wave_chain([255, 0, self._wid, 255, 1, self._pulses, 0])
                            self._clocks = 0
                            self._value = 0
                            self._sent += 1
            try:
                self._previous_edge_long = current_edge_long
                self._data_tick = tick
            except:
                print("Over time for reading")

def getVals(): 
    weighing_system = WeighingSystem(pi)
    try:
        print("start with CH_A_GAIN_128 and callback")
        
        start = time.time()
        while True:
            print("scale1: ", weighing_system.scale_read1, "scale2: ", weighing_system.scale_read2, "scale3: ", weighing_system.scale_read3, "scale4: ", weighing_system.scale_read4)
            #print("scale1: ", weighing_system.scale_read1)
            #print("scale2: ", weighing_system.scale_read2)
            # print("scale3: ", weighing_system.scale_read3)
            # print("scale4: ", weighing_system.scale_read4)
                # start = time.time()
            time.sleep(0.1)

    except Exception as e:
        print("error: ", e)

    weighing_system.s1.pause()
    weighing_system.s1.cancel()
    weighing_system.s2.pause()
    weighing_system.s2.cancel()
    weighing_system.s3.pause()
    weighing_system.s3.cancel()
    weighing_system.s4.pause()
    weighing_system.s4.cancel()
    pi.stop()

def window():
    app = QApplication([]) # create a window
    window = QWidget()
    
    runButton = QPushButton(window) # run button
    runButton.setText("Run")
    runButton.move(50, 50)
    # runButton.clicked.connect(getVals())

    exitButton = QPushButton(window) # exit button
    exitButton.setText("Exit")
    exitButton.move(50, 100)
    exitButton.clicked.connect(exit(0))

    window.setGeometry(100, 100, 320, 200)
    window.setWindowTitle("Golf balance window")
    window.show() # show window
    app.exec_()

if __name__ == "__main__":
    pi = pigpio.pi()

    window()
