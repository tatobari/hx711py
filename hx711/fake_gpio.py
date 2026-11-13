#! /usr/bin/python3

class FakeGpio:
    BCM = "UseBroadcomNumbering"
    BOARD = "UsePhysicalBoardNumbering"
    OUT = "fake_gpio_output"
    IN = "fake_gpio_input"

    def __init__(self, fake_hx711):
        self._fake_hx711 = fake_hx711
        self._input_pin = None
        self._output_pin = None
    
    def setmode(self, value):
        assert value in [self.BCM, self.BOARD]

    def setup(self, pin, value_b):
        if value_b == self.OUT:
            self._output_pin = pin
            return

        if value_b == self.IN:
            self._input_pin = pin
            return

        raise ValueError("setup({}, {})".format(pin, value_b))

    def output(self, pin, value):
        if pin != self._output_pin:
            raise ValueError("output({}, {})!! Not setup as an output!".format(pin, value))

        self._fake_hx711.set_pd_sck(value)
        
    def input(self, pin):
        if pin == self._input_pin:
            return self._fake_hx711.dout()

        raise ValueError("input({})!! Not setup as an input!".format(pin))

    def cleanup(self):
        self._input_pin = None
        self._output_pin = None


# EOF - fake_gpio.py
