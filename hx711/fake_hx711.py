#! /usr/bin/python3

"""
HX711 emulator.
"""
import time

# Output Data Rate and Format:
#
# When using the on-chip oscillator, output data rate is typically 10 (RATE=0)
# or 80SPS (RATE=1).
#    When using external clock or crystal, output data rate is directly
# proportional to the clock or crystal frequency.  Using 11.0592MHz clock or
# crystal results in an accurate 10 (RTE=0) or 80SPS (RATE=1) output data rate.
#    The output 24 bits of data is in 2’s complement format.  When input
# differential signal goes out of the 24 bit range, the output data will be
# saturated at 800000h (MIN) or 7FFFFFh (MAX), until the input signal comes back
# to the input range.
#
# Serial Interface:
#
# Pin PD_SCK and DOUT are used for data retrieval, input selection, gain
# selection and power down controls.
#    When output data is not ready for retrieval, digital output pin DOUT is
# high. Serial clock input PD_SCK should be low. When DOUT goes to low, it
# indicates data is ready for retrieval.  By applying 25~27 positive clock
# pulses at the PD_SCK pin, data is shifted out from the DOUT output pin.  Each
# PD_SCK pulse shifts out one bit, starting with the MSB bit first, until all 24
# bits are shifted out. The 25th pulse at PD_SCK input will pull DOUT pin back
# to high.
#    Input and gain selection is controlled by the number of the input PD_SCK
# pulses (Table 3).  PD_SCK clock pulses should not be less than 25 or more than
# 27 within one conversion period, to avoid causing serial communication error.
#
# Table 3 Input Channel and Gain Selection:
# +---------------+---------------+------+
# | PD_SCK Pulses | Input Channel | Gain |
# +---------------+---------------+------+
# | 25            | A             | 128  |
# | 26            | B             | 32   |
# | 27            | A             | 64   |
# +---------------+---------------+------+
#
#       _____        ___   ___   ___   ______//___   ___________________________
#            |      /   \ /   \ /   \ /           \ /     /
# DOUT       |     / MSB X     X     X             X LSB /
#            |____/_____/ \___/ \___/ \______//___/ \___/
#
#                  __    __    __    __            __    __    Next conversion:
# PD_SCK          |1 |  |2 |  |3 |  |4 |          |24|  |25|   CH A, Gain 128
#        _________|  |__|  |__|  |__|  |_____//___|  |__|  |____________________
#
#                  __    __    __    __            __    __    __  Next:
# PD_SCK          |1 |  |2 |  |3 |  |4 |          |24|  |25|  |26| CH B, Gain 32
#        _________|  |__|  |__|  |__|  |_____//___|  |__|  |__|  |______________
#
#                  __    __    __    __            __    __    __    __  CH A
# PD_SCK          |1 |  |2 |  |3 |  |4 |          |24|  |25|  |26|  |27| G: 64
#        _________|  |__|  |__|  |__|  |_____//___|  |__|  |__|  |__|  |________
#
#
# +--------+-----------------------------------------+-----+---------+-----+------+
# | Symbol | Note                                    | Min | Typical | Max | Unit |
# +--------+-----------------------------------------+-----+---------+-----+------+
# | T1     | DOUT falling edge to PD_SCK rising edge | 0.1 | -       | -   | us   |
# | T2     | PD_SCK rising edge to DOUT data ready   | -   | -       | 0.1 | us   |
# | T3     | PD_SCK high time                        | 0.2 | 1       | 50  | us   |
# | T4     | PD_SCK low time                         | 0.2 | 1       | -   | us   |
# +--------+-----------------------------------------+-----+---------+-----+------+
#
# Reset and Power-Down:
#
# When chip is powered up, on-chip power on rest circuitry will reset the chip.
# Pin PD_SCK input is used to power down the HX711.  When PD_SCK Input is low,
# chip is in normal working mode.
#
#            +-------------/ /------------+
# PD_SCK     |                            |
#         ___|                            |______________
#
#            |<--60us-->|<--PoweredDown-->|<---Normal----
#
# When PD_SCK pin changes from low to high and stays at high for longer than
# 60μs, HX711 enters power down mode.  When internal regulator is used for HX711
# and the external transducer, both HX711 and the transducer will be powered
# down.  When PD_SCK returns to low, chip will reset and enter normal operation
# mode.  After a reset or power-down event, input selection is default to
# Channel A with a gain of 128.

class FakeHx711:
    """Simulates a HX711, currently only emulates channel A: Gain 128,
    attempting to use other settings will raise an exception
    """

    # Sample rate is 80 Hz --> period 0.0125ms
    SAMPLE_PERIOD_SECONDS = 0.0125

    # Holding PD_SCK pin high for 60us will turn it off.
    POWER_OFF_PERIOD_SECONDS = 0.00006

    REFERENCE_A_UNIT = 13.819
    REFERENCE_B_UNIT = 13.819

    def __init__(self, value_list=None):
        self._powered_down = True
        self._pd_sck_value = True
        self._power_down_deadline_time = None
        self._pending_value_list = value_list
        if self._pending_value_list is None:
            self._pending_value_list = []
        self._raw_value = 0x001337
        self._clock_posedge_count = 0
        self._clock_negedge_count = 0
        self._next_sample_due_time = time.time() + self.SAMPLE_PERIOD_SECONDS
        self._sample_ready = False
        self._prev_clock_count = None

    def inject_float_samples(self, sample_list):
        """Inject a list of real samples to be output by the HX711 emulator."""
        for sample in sample_list:
            self._pending_value_list.append(int(sample * self.REFERENCE_A_UNIT))

    def inject_raw_samples(self, sample_list):
        self._pending_value_list += sample_list

    def update_next_sample_due_time(self):
        self._next_sample_due_time = time.time() + self.SAMPLE_PERIOD_SECONDS

    def update_power_down_deadline_time(self):
        self._power_down_deadline_time = time.time() + self.POWER_OFF_PERIOD_SECONDS

    def update(self, pos_edge=False, neg_edge=False):
        if self._power_down_deadline_time is not None:
            if time.time() >= self._power_down_deadline_time:
                # print("Powering down.")
                self._powered_down = True
                self._power_down_deadline_time = None

        if time.time() >= self._next_sample_due_time:
            self.next_sample()

        if pos_edge:
            self.update_power_down_deadline_time()
            self._clock_posedge_count += 1

        if neg_edge:
            self._power_down_deadline_time = None

            if self._powered_down:
                # print("Neg edge when powered down, we'll wake up now.")
                self._powered_down = False
                self._clock_posedge_count = 0
                self._clock_negedge_count = 0
                self.update_next_sample_due_time()
                self._sample_ready = False
                return

            self._clock_negedge_count += 1

    def next_sample(self):
        self.update_next_sample_due_time()
        self._sample_ready = True
        if len(self._pending_value_list) > 0:
            self._raw_value = self._pending_value_list.pop(0)

        prev_clock_count = self._clock_posedge_count

        # New sample, reset the clock edge counts.
        self._clock_posedge_count = 0
        self._clock_negedge_count = 0

        if prev_clock_count in [0, 25]:
            # print("Selected for next conversion: Channel A Gain 128")
            return

        if prev_clock_count == 26:
            # print("Selected for next conversion: Channel B Gain 32")
            raise ValueError("Channel B Gain 32 not supported, yet!")

        if prev_clock_count == 27:
            # print("Selected for next conversion: Channel A Gain 64")
            raise ValueError("Channel A Gain 64 not supported, yet!")

        # This is undetermined behaviour.
        #raise ValueError(f"Unrecognised clock count! ({prev_clock_count})")
        print("Unrecognised clock count! ({})".format(prev_clock_count))

    def dout(self):
        """Read the DOUT pin of our emulated HX711."""
        self.update()

        if self._powered_down:
            # TODO: Check this assumption that powering down sets DOUT to high.
            return 1

        # If HX711 doesn't have a sample, yet.  It holds DOUT high.
        if not self._sample_ready:
            return 1

        # If sample is ready but we've had no clocks HX711 lowers DOUT to signal this.
        if self._clock_posedge_count == 0:
            return 0

        # If we've clocked out all our sample bits the HX711 raises DOUT until
        # it has a new sample ready.
        if self._clock_posedge_count > 24:
            return 1

        bit_selected = 24 - self._clock_posedge_count

        bit_value = (self._raw_value >> bit_selected) & 0x1

        # print("bit_selected:", bit_selected, "==", bit_value)
        return bit_value

    def set_pd_sck(self, pd_sck):
        """Set the input value of the PD_SCK pin of our emulated HX711."""
        if self._pd_sck_value == pd_sck:
            self.update()
        else:
            self._pd_sck_value = pd_sck

            if pd_sck:
                self.update(pos_edge=True)
            else:
                self.update(neg_edge=True)


# EOF - class_fake_hx711.py
