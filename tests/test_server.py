import threading

from hx711_server import LatestReading


def test_latest_reading_starts_empty():
    assert LatestReading().get() is None


def test_latest_reading_returns_most_recent_value():
    reading = LatestReading()

    reading.set({"ts": 1.0, "weight": 2.0, "unit": "kg"})
    reading.set({"ts": 3.0, "weight": 4.0, "unit": "kg"})

    assert reading.get() == {"ts": 3.0, "weight": 4.0, "unit": "kg"}


def test_latest_reading_can_be_reset_to_none():
    reading = LatestReading()
    reading.set({"weight": 2.0})
    reading.set(None)

    assert reading.get() is None


def test_latest_reading_is_thread_safe():
    reading = LatestReading()
    errors = []

    def writer():
        try:
            for seq in range(1000):
                reading.set({"seq": seq})
        except Exception as exc:
            errors.append(exc)

    def reader():
        try:
            for _ in range(1000):
                value = reading.get()
                if value is not None and "seq" not in value:
                    raise AssertionError(value)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
