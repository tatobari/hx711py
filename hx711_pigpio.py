import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
import time
         
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
                    self._data_tick = tick
                    self._previous_edge_long = current_edge_long

if __name__ == "__main__":

    last_count = -1
    scale_read = 0
    def scale_read_cb(count, mode, reading):
        if count!=last_count:
            scale_read = reading
            last_count = count

    # open pigpio: sudo pigpiod
    pi = pigpio.pi()
    if not pi.connected:
        exit(0)

    s = HX711(pi, DATA_PIN=5, CLOCK_PIN=6, mode=HX711.CH_A_GAIN_128, callback=scale_read_cb)

    try:
        print("start with CH_A_GAIN_128 and callback")

        s.start()
        time.sleep(2)
        print("scale start!!")

        stop = time.time() + 3600

        while time.time() < stop:
            # start = time.time()
            print("Loop")
            
            print("scale reading: ", scale_read)
            # print("time of reading: ", time.time()-start)
            time.sleep(0.05)

    except KeyboardInterrupt:
        pass

    s.pause()
    s.cancel()
    pi.stop()

