import numpy as np
import matplotlib.pyplot as plt
import pandapower as ppo
import pandapipes as ppi
import pandapower.control as control
import pandas as pd
import pandapower.timeseries as ts
from simple_pid import PID
import time
import random


class CtrlValve(control.basic_controller.Controller):
    """
        Example class of a Valve-Controller. Models an abstract control valve.
    """

    def __init__(self, net, valve_id, data_source=None, profile_name=None, in_service=True, enable_plotting=False,
                 name='', mdot_set_kg_per_s=0, gain=-1000, tol=0,
                 recycle=True, order=0, level=0, **kwargs):
        super().__init__(net, in_service=in_service, recycle=recycle, order=order, level=level,
                         initial_powerflow=True, **kwargs)

        # Init related valve parameters from net
        self.valve_id = valve_id  # index of the controlled valve
        self.from_junction = net.valve.at[valve_id, "from_junction"]
        self.to_junction = net.valve.at[valve_id, "to_junction"]
        self.diameter = net.valve.at[valve_id, "diameter_m"]
        self.loss_coeff = net.valve.at[valve_id, "loss_coefficient"]
        self.opened = net.valve.at[valve_id, "opened"]

        # Init controller attributes
        self.in_service = bool(net.controller['in_service'].iloc[-1])
        self.initial_run = bool(net.controller['initial_run'].iloc[-1])
        self.level = net.controller['level'].iloc[-1]
        self.order = net.controller['order'].iloc[-1]
        self.recycle = bool(net.controller['recycle'].iloc[-1])
        self.applied = False

        # specific attributes
        self.name = name  # Valve control name
        self.mdot_set_kg_per_s = mdot_set_kg_per_s  # Mass flow setpoint - [kg/s]
        self.tol = tol  # absolute tolerance

        # profile attributes
        self.data_source = data_source
        self.profile_name = profile_name

        # init pid control
        self._init_pid_control(gain)

        # init plot
        self.enable_plotting = enable_plotting

    def _init_pid_control(self, gain):
        self.pid = PID(gain, 0, 0)
        self.pid.output_limits = (None, None)  # Output will always be above 0, but with no upper bound
        self.loss_coeff_min = 0
        self.loss_coeff_max = 1e6

    def initialize_control(self, net):
        """
        At the beginning of each run_control call reset applied-flag
        """
        self.pid.setpoint = self.mdot_set_kg_per_s

        # clear plot
        if self.enable_plotting == True:
            self.axes = plt.gca()
            self.axes.set_xlim(0, 100)
            self.axes.set_ylim(0, 1)
            self.xdata = []
            self.ydata = []
            self.line, = self.axes.plot([], [], 'b')

    # Also remember that 'is_converged()' returns the boolean value of convergence:
    def is_converged(self, net):
        mdot = np.nan_to_num(net.res_valve.at[self.valve_id, 'mdot_from_kg_per_s'])
        mdot_set = self.mdot_set_kg_per_s

        # Set absolute tolerance
        loTol = mdot_set - self.tol
        upTol = mdot_set + self.tol

        if loTol <= mdot <= upTol:
            # plt.show()
            self.applied = True
        else:
            self.applied = False
        # check if controller already was applied
        return self.applied

    # Also a first step we want our controller to be able to write its P and Q and state of charge values back to the
    # data structure net.
    def write_to_net(self, net):
        # write p, q and soc_percent to bus within the net
        net.valve.at[self.valve_id, "loss_coefficient"] = self.loss_coeff
        net.valve.at[self.valve_id, "opened"] = self.opened

    # In case the controller is not yet converged, the control step is executed. In the example it simply
    # adopts a new value according to the previously calculated target and writes back to the net.
    def control_step(self, net):
        mdot = np.nan_to_num(net.res_valve.at[self.valve_id, 'mdot_from_kg_per_s'])
        mdot_set = self.mdot_set_kg_per_s

        # Set valve status and position
        self._set_valve_status()
        if self.opened:
            self._set_valve_position(net)

        # Update plot
        if self.enable_plotting == True:
            self.update_plot(net)

        # Call write_to_net and set the applied variable True
        self.write_to_net(net)
        self.applied = True

    def _set_valve_status(self):
        # Get flow results
        mdot_set = self.mdot_set_kg_per_s

        # set valve status
        if mdot_set < 1e-6:  # To avoid float issues
            self.opened = False

    def _set_valve_position(self, net):
        # Get flow results
        mdot = np.nan_to_num(net.res_valve.at[self.valve_id, 'mdot_from_kg_per_s'])
        mdot_set = self.mdot_set_kg_per_s

        # set valve position
        # PID control
        output = self.pid(mdot)
        self.loss_coeff += output  # Controlled variable: dloss/dt

        # Validate limits of loss_coeff
        min = self.loss_coeff_min
        max = self.loss_coeff_max
        if min <= self.loss_coeff <= max:
            pass
        elif self.loss_coeff < min:
            self.loss_coeff = min
        else:
            self.loss_coeff = max

    # In a time-series simulation the battery should read new power values from a profile and keep track
    # of its state of charge as depicted below.
    def time_step(self, net, time):
        # read new values from a profile
        if self.data_source:
            if self.profile_name is not None:
                self.mdot_set_kg_per_s = self.data_source.get_time_step_value(
                                                                    time_step=time,
                                                                    profile_name=self.profile_name)

        self.applied = False  # reset applied variable

    # TODO: If deprecated, remove and call by setattr()
    # def set_mdot_setpoint(self, value):
    #     self.mdot_set_kg_per_s = value

    def update_plot(self, net):
        mdot = net.res_valve.at[self.valve_id, 'mdot_from_kg_per_s']
        mdot_set = self.mdot_set_kg_per_s

        error = (mdot_set - mdot) / mdot_set
        error_abs = np.sqrt(np.power(error, 2))

        # self.xdata.append(loss_coeff)
        self.xdata.append(self.i)
        self.ydata.append(error_abs)

        self.line.set_xdata(self.xdata)
        self.line.set_ydata(self.ydata)
        plt.draw()
        plt.pause(1e-17)

    def to_json(self):
        return {'in_service': self.in_service,
                'initial_run': self.initial_run,
                'level': self.level,
                'order': self.order,
                'recycle': self.recycle,
                'name': self.name,
                'type': 'CtrlValve',
                'object': {
                    'data_source': self.data_source,
                    'valve_id': self.valve_id,
                    'mdot_set_kg_per_s': self.mdot_set_kg_per_s,
                    'profile_name': self.profile_name,
                    'tol': self.tol,
                    'gain': self.pid.Kp,
                    'loss_coeff_min': self.loss_coeff_min,
                    'loss_coeff_max': self.loss_coeff_max,
                    'enable_plotting': self.enable_plotting
                }
        }