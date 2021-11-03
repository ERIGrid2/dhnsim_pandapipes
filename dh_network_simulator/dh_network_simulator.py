from dataclasses import dataclass, field
import pandapipes as pp
from collections import deque
import pandapipes.plotting as plot
from pandapipes.pandapipes_net import pandapipesNet
from .dh_network_simulator_core import *
from pandapower.timeseries.data_sources.frame_data import DFData
from typing import Dict
# Do not print python UserWarnings
import sys
import logging

if not sys.warnoptions:
    import warnings


@dataclass
class DHNetworkSimulator():
    """
        District Heating Network Simulator API class containing the following objects:
            pandapipesNet: DHN containing all network components and characteristics based on the pandapipes library

        and public functions:
            load_network(): Imports and initializes the pandapipes network components from .json files or by using the default pandapipes import filehandler
            save_network(): Exports the pandapipes network components to .json files or by using the default pandapipes export filehandler
            plot_network_topology(): Plots the network components based on the geodata of the network junctions
            run_simulation(): Runs the static or quasi-dynamic heat flow simulation (steady-state mass flows and pressures) for a time step t
            get_value_of_network_component(): Getter for network component parameters and attributes
            set_value_of_network_component(): Setter for network component parameters and attributes

    """

    logging_enabled: bool = True  # Logging modes: 'default', 'all'
    net: pandapipesNet = field(init=False)

    # Internal variables
    collector_connections: dict = field(init=False)
    historical_data: dict = field(init=False)  # Dict of FIFO shift registers for each datapoint

    def __repr__(self):
        rep = str(f'DHNetworkSimulator(logging={self.logging})')
        return rep

    def __post_init__(self):
        self._init_logging()
        self._init_dh_network()
        self._init_collector_connections()
        self._init_historical_data_storage()

    def _init_logging(self):
        if self.logging_enabled:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            self.logger.info(f'DH Network Simulator: Logging (level="{logging.getLevelName(self.logger.level)}") enabled.')

        # Ignore filter warning of hydraulic dynamics
        warnings.filterwarnings("ignore", message="Pipeflow converged, however, the results are phyisically incorrect as pressure is negative at nodes*")

    def _init_dh_network(self):
        # create empty network
        self.net = pp.create_empty_network("net", add_stdtypes=False)
        # create fluid
        pp.create_fluid_from_lib(self.net, "water", overwrite=True)

    def _init_collector_connections(self):
        # Define stored attributes of the simulation
        self.collector_connections = {
            'junction': ['t_k']
        }

    def _init_historical_data_storage(self):
        dict = {}
        for key, param_list in self.collector_connections.items():
            component = getattr(self.net, key)
            dict.update({key: {}})
            for i in component.name:
                dict[key].update({i: {}})
                for param in param_list:
                    dict[key][i].update({param:[]})

        self.historical_data = dict


    def load_network(self, from_file=False, path='', format='json_default'):
        # import from file
        if from_file is True:
            try:
                import_network_components(net=self.net,
                                      format=format,
                                      path=path)
            except ImportError as error:
                # Throw error if import was not successful
                self.logger.error(error)

        # initialize historical data storage
        self._init_historical_data_storage()

    def save_network(self, path='', format='json_default'):
        export_network_components(net=self.net,
                                  format=format,
                                  path=path)

    def run_simulation(self, t, sim_mode='static'):
        # Run hydraulic flow (steady-state)
        try:
            run_hydraulic_control(net=self.net)
        except:
            # Throw UserWarning
            # self.logger.error(f"Simulation mode '{sim_mode}' does not exist. Simulation has stopped.")
            self.logger.warning(f'ControllerNotConverged: Maximum number of iterations per controller is reached.')

        if sim_mode == 'static':
            run_static_pipeflow(self.net)
        elif sim_mode == 'dynamic':
            # Run dynamic pipeflow
            run_dynamic_pipeflow(net=self.net,
                                 historical_data=self.historical_data,
                                 collector_connections=self.collector_connections,
                                 t=t)
        else:
            self.logger.error(f"Simulation mode '{sim_mode}' does not exist. Simulation has stopped.")

    def get_value_of_network_component(self, type, name, parameter):
        error = False

        # Get corresponding network component
        if type == 'sink':
            component = self.net.sink
            result = self.net.res_sink
        elif type == 'source':
            component = self.net.source
            result = self.net.res_source
        elif type == 'junction':
            component = self.net.junction
            result = self.net.res_junction
        elif type == 'valve':
            component = self.net.valve
            result = self.net.res_valve
        elif type == 'ext_grid':
            component = self.net.ext_grid
            result = self.net.res_ext_grid
        elif type == 'heat_exchanger':
            component = self.net.heat_exchanger
            result = self.net.res_heat_exchanger
        elif type == 'controller':
            component = self.net.controller
            result = self.net.controller
        else:
            self.logger.error(f"Component {name} cannot be found. Update not successful.")
            error = True

        if not error:
            val = get_value_of(component, name, type, parameter, result)
            return val

    def set_value_of_network_component(self, type, name, parameter, value):
        error = False

        # Get corresponding network component
        if type == 'sink':
            component = self.net.sink
        elif type == 'source':
            component = self.net.source
        elif type == 'junction':
            component = self.net.junction
        elif type == 'valve':
            component = self.net.valve
        elif type == 'ext_grid':
            component = self.net.ext_grid
        elif type == 'heat_exchanger':
            component = self.net.heat_exchanger
        elif type == 'controller':
            component = self.net.controller
        else:
            self.logger.error(f"Component {name} cannot be found. Update not successful.")
            error = True

        if not error:
            set_value_of(component, name, type, parameter, value)

    def plot_network_topology(self):
        # plot network
        plot.simple_plot(self.net, plot_sinks=True, plot_sources=True, sink_size=4.0, source_size=4.0)

    def load_data(self):
        # TODO: Create API for datafiles in .csv format
        file = ''
        profiles_source = pd.read_csv(file, index_col=0)
        data_source = DFData(profiles_source)
        return data_source