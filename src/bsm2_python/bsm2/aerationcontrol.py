import control as ct
import numpy as np


class Sensor:
    """Sensor class for simulating the response of a system to an input signal.

    Parameters
    ----------
    num : array-like
        Numerator coefficients of the transfer function.
    den : array-like
        Denominator coefficients of the transfer function.
    min_value : float
        Minimum output value.
    max_value : float
        Maximum output value.
    std : float
        Standard deviation of the noise.
    """

    def __init__(
        self,
        num: float | np.ndarray | list[float],
        den: float | np.ndarray | list[float],
        min_value: float,
        max_value: float,
        std: float,
    ):
        self.num = num
        self.den = den
        self.min_value = min_value
        self.max_value = max_value
        self.std = std
        self.state_space = ct.tf2ss(num, den)
        n_states = self.state_space.nstates
        self.state = np.zeros(n_states)

    def output(self, input_signal, dt, noise):
        dt = np.array([0, dt])
        response = ct.forced_response(self.state_space, U=input_signal, T=dt, X0=self.state)
        self.state = response.states[:, -1]
        y_out = response.outputs[-1]
        output_signal = y_out + noise * self.max_value * self.std
        if output_signal < self.min_value:
            output_signal = self.min_value
        elif output_signal > self.max_value:
            output_signal = self.max_value
        return output_signal


class PID:
    """PID controller with anti-windup.

    Parameters
    ----------
    k : float
        Proportional gain.
    t_i : float
        Integral time constant.
    t_d : float
        Derivative time constant.
    t_t : float
        Anti-windup time constant.
    offset : float
        Offset value.
    min_value : float
        Minimum output value.
    max_value : float
        Maximum output value.
    setpoint : float
        Desired setpoint.
    aw_init : float, optional
        Initial anti-windup value. If not provided, it will be set to 0.
    use_antiwindup : bool, optional
        If `True`, anti-windup is used. Default is `True`.
    """

    def __init__(
        self,
        k: float,
        t_i: float,
        t_d: float,
        t_t: float,
        offset: float,
        min_value: float,
        max_value: float,
        setpoint: float,
        aw_init: float | None = None,
        *,
        use_antiwindup: bool = True,
    ):
        self.k = k
        self.t_i = t_i
        self.t_d = t_d
        self.t_t = t_t
        self.offset = offset
        self.min_value = min_value
        self.max_value = max_value
        self.setpoint = setpoint
        self.integral = 0.0
        self.derivative = 0.0
        self.error = 0.0
        self.prev_error = 0.0
        self.prev_signal = 0.0
        self.prev_lim = 0.0
        self.aw = 0.0 if aw_init is None else aw_init
        self.use_antiwindup = use_antiwindup

    def output(self, signal: float, dt: float, inject: float = 0):
        """Calculate the control signal based on the PID controller.

        Parameters
        ----------
        signal : float
            Input signal to the PID controller.
        dt : float
            Time step for the simulation.
        inject : float, optional
            Additional signal to be injected into the control signal. Default is 0.
        """
        dt_arr = np.array([0, dt])
        self.error = self.k * (self.setpoint - signal)
        self.integral += self.error / self.t_i * (dt_arr[1] - dt_arr[0])
        self.derivative = self.k * self.t_d * (self.error - self.prev_error) / (dt_arr[1] - dt_arr[0])
        self.prev_error = self.error
        if self.use_antiwindup:
            self.aw = (self.prev_lim - self.prev_signal) / self.t_t * (dt_arr[1] - dt_arr[0])
        else:
            self.aw = 0
        self.integral += self.aw
        control_signal = self.error + self.integral + self.derivative + self.offset + inject
        self.prev_signal = control_signal
        control_signal = max(control_signal, self.min_value)
        control_signal = min(control_signal, self.max_value)
        self.prev_lim = control_signal
        return control_signal


class Actuator:
    """Actuator class for simulating the response of a system to an input signal.

    Parameters
    ----------
    num : array-like
        Numerator coefficients of the transfer function.
    den : array-like
        Denominator coefficients of the transfer function.
    """

    def __init__(self, num: float | np.ndarray | list[float], den: float | np.ndarray | list[float]):
        self.num = num
        self.den = den
        self.state_space = ct.tf2ss(num, den)
        n_states = self.state_space.nstates
        self.state = np.zeros(n_states)

    def output(self, input_signal: float, dt: float):
        """Calculate the output of the actuator based on the input signal and time step.

        Parameters
        ----------
        input_signal : float
            Input signal to the actuator.
        dt : float
            Time step for the simulation.
        """
        dt_arr = np.array([0, dt])
        response = ct.forced_response(self.state_space, U=input_signal, T=dt_arr, X0=self.state)
        self.state = response.states[:, -1]
        y_out = response.outputs[-1]
        return y_out
