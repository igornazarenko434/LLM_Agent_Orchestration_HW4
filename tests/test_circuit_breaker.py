import time
import pytest

from hw4_tourguide.tools.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


@pytest.mark.resilience
def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker("test", failure_threshold=2, timeout=0.1, time_func=time.monotonic)

    def boom():
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        cb.call(boom)
    with pytest.raises(RuntimeError):
        cb.call(boom)
    assert cb.state == CircuitBreaker.OPEN
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(lambda: None)


@pytest.mark.resilience
def test_circuit_breaker_half_open_and_closes(monkeypatch):
    now = [0.0]

    def fake_time():
        return now[0]

    cb = CircuitBreaker("test", failure_threshold=1, timeout=1.0, time_func=fake_time)

    def boom():
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        cb.call(boom)
    assert cb.state == CircuitBreaker.OPEN

    # advance time past timeout to allow half-open
    now[0] = 2.0
    result = cb.call(lambda: "ok")
    assert result == "ok"
    assert cb.state == CircuitBreaker.CLOSED


@pytest.mark.resilience
def test_circuit_breaker_half_open_failure_reopens(monkeypatch):
    now = [0.0]

    def fake_time():
        return now[0]

    cb = CircuitBreaker("test", failure_threshold=1, timeout=1.0, time_func=fake_time)

    def boom():
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        cb.call(boom)
    assert cb.state == CircuitBreaker.OPEN

    now[0] = 2.0
    with pytest.raises(RuntimeError):
        cb.call(boom)
    assert cb.state == CircuitBreaker.OPEN
