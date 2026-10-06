"""Regression tests for PI integral accumulation and saturation tracking."""

import numpy as np
import pytest

from bsm2_python.bsm2.aerationcontrol import PID


def make_pid(**overrides):
    params = {
        'k': 2.0,
        't_i': 1.0,
        't_d': 0.0,
        't_t': 0.5,
        'offset': 0.0,
        'min_value': -100.0,
        'max_value': 100.0,
        'setpoint': 1.0,
    }
    params.update(overrides)
    return PID(**params)


def test_constant_error_accumulates_and_zero_error_retains_integral():
    pid = make_pid(use_antiwindup=False)
    assert [pid.output(0.0, 0.1) for _ in range(3)] == pytest.approx([2.2, 2.4, 2.6])
    assert pid.output(1.0, 0.1) == pytest.approx(0.6)


@pytest.mark.parametrize(('dt', 'count'), [(0.1, 10), (0.025, 40)])
def test_integral_depends_on_elapsed_time(dt, count):
    pid = make_pid(use_antiwindup=False)
    for _ in range(count):
        pid.output(0.0, dt)
    assert pid.integral == pytest.approx(2.0)


@pytest.mark.parametrize('antiwindup', [True, False])
@pytest.mark.parametrize('offset', [0.0, 0.4])
def test_integral_matches_independent_back_calculation(antiwindup, offset):
    pid = make_pid(min_value=0.0, max_value=1.0, offset=offset, use_antiwindup=antiwindup)
    integral = 0.0
    previous_raw = 0.0
    previous_limited = 0.0
    inputs = [(0.0, 0.1, 0.0)] * 20 + [(2.0, 0.2, 0.3)] * 10 + [(0.8, 0.05, 0.0)] * 20
    for signal, dt, injection in inputs:
        error = 2.0 * (1.0 - signal)
        correction = (previous_limited - previous_raw) / 0.5 if antiwindup else 0.0
        integral += dt * (error + correction)
        raw = error + integral + offset + injection
        limited = float(np.clip(raw, 0.0, 1.0))
        assert pid.output(signal, dt, injection) == pytest.approx(limited)
        assert pid.integral == pytest.approx(integral)
        previous_raw, previous_limited = raw, limited
