import pytest

from hx711.core import HX711, twos_complement_24bit_to_int


class RecordingGpio:
    """Minimal RPi.GPIO stand-in that returns a scripted 24-bit sample."""

    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"

    def __init__(self, sample=0, ready=True):
        self.sample = sample
        self.ready = ready
        self.pd_sck = False
        self.rising_edges = 0
        self.bits_read = 0
        self.cleanup_called = False

    def setmode(self, mode):
        pass

    def setup(self, pin, direction):
        pass

    def output(self, pin, value):
        if value and not self.pd_sck:
            self.rising_edges += 1
        self.pd_sck = value

    def input(self, pin):
        if not self.ready:
            return 1

        if self.rising_edges == 0:
            return 0

        if self.rising_edges > 24:
            return 1

        bit_index = 24 - self.rising_edges
        self.bits_read += 1
        return (self.sample >> bit_index) & 1

    def cleanup(self):
        self.cleanup_called = True


class ReadCountingHX711(HX711):
    def __init__(self, gpio_module):
        super().__init__(5, 6, gpio_module=gpio_module)
        self.read_count = 0

    def read_word(self, timeout_seconds=0.5):
        self.read_count += 1
        return 0


@pytest.mark.parametrize(
    "value, expected",
    [
        (0x000000, 0),
        (0x000001, 1),
        (0x7FFFFF, 0x7FFFFF),
        (0x800000, -0x800000),
        (0xFFFFFE, -2),
        (0xFFFFFF, -1),
    ],
)
def test_twos_complement_24bit_to_int(value, expected):
    assert twos_complement_24bit_to_int(value) == expected


@pytest.mark.parametrize(
    "sample, expected",
    [
        (0x000001, 1),
        (0x7FFFFF, 0x7FFFFF),
        (0x800000, -0x800000),
        (0xFFFFFE, -2),
        (0xFFFFFF, -1),
    ],
)
def test_read_word_round_trip(sample, expected):
    gpio = RecordingGpio(sample=sample)
    hx = HX711(5, 6, gpio_module=gpio)

    assert hx.read_word() == expected
    assert gpio.bits_read == 24


@pytest.mark.parametrize(
    "gain, expected_clock_edges",
    [
        (HX711.CH_A_GAIN_128, 25),
        (HX711.CH_B_GAIN_32, 26),
        (HX711.CH_A_GAIN_64, 27),
    ],
)
def test_read_word_sends_gain_selection_clocks(gain, expected_clock_edges):
    gpio = RecordingGpio(sample=0)
    hx = HX711(5, 6, gpio_module=gpio)
    hx._gain = gain

    assert hx.read_word() == 0
    assert gpio.rising_edges == expected_clock_edges


@pytest.mark.parametrize(
    "gain",
    [HX711.CH_A_GAIN_128, HX711.CH_B_GAIN_32, HX711.CH_A_GAIN_64],
)
def test_set_channel_gain_accepts_valid_values(gain):
    gpio = RecordingGpio(sample=0)
    hx = HX711(5, 6, gpio_module=gpio)

    hx.set_channel_gain(gain)

    assert hx.get_channel_gain() == gain
    assert gpio.bits_read == 24


@pytest.mark.parametrize("gain", [0, 4, -1, 128, None, "A"])
def test_set_channel_gain_rejects_invalid_values(gain):
    gpio = RecordingGpio(sample=0)
    hx = HX711(5, 6, gpio_module=gpio)

    with pytest.raises(ValueError):
        hx.set_channel_gain(gain)

    assert hx.get_channel_gain() == HX711.CH_A_GAIN_128
    assert gpio.rising_edges == 0


def test_read_word_timeout_returns_none_and_releases_lock(capsys):
    gpio = RecordingGpio(ready=False)
    hx = HX711(5, 6, gpio_module=gpio)

    assert hx.read_word(timeout_seconds=0.01) is None
    assert "Timed out" in capsys.readouterr().out
    assert gpio.rising_edges == 0

    # The read lock must have been released despite the timeout.
    assert hx._read_lock.acquire(blocking=False)
    hx._read_lock.release()


def test_is_ready_reflects_dout_level():
    assert HX711(5, 6, gpio_module=RecordingGpio(ready=True)).is_ready()
    assert not HX711(5, 6, gpio_module=RecordingGpio(ready=False)).is_ready()


def test_power_up_discards_sample_for_non_default_gain():
    hx = ReadCountingHX711(RecordingGpio())
    hx._gain = HX711.CH_A_GAIN_64

    hx.power_up()

    assert hx.read_count == 1


def test_power_up_keeps_sample_for_default_gain():
    hx = ReadCountingHX711(RecordingGpio())

    hx.power_up()

    assert hx.read_count == 0


def test_cleanup_delegates_to_gpio_module():
    gpio = RecordingGpio()
    hx = HX711(5, 6, gpio_module=gpio)

    hx.cleanup()

    assert gpio.cleanup_called


def test_cleanup_without_gpio_cleanup_does_not_raise():
    class GpioWithoutCleanup:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"

        def setmode(self, mode):
            pass

        def setup(self, pin, direction):
            pass

        def output(self, pin, value):
            pass

        def input(self, pin):
            return 0

    hx = HX711(5, 6, gpio_module=GpioWithoutCleanup())

    hx.cleanup()
