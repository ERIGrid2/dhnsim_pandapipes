from dataclasses import dataclass, field
import pandapipes as pp
import pandapipes.plotting as plot
from pandapipes.pandapipes_net import pandapipesNet
from .dh_network_simulator_core import *
from pandapower.timeseries.data_sources.frame_data import DFData
# Do not print python UserWarnings
import sys

if not sys.warnoptions:
    import warnings


@dataclass
class DHNetworkSimulator():
    """
        District Heating Network Simulator class.
    """

    logging: str = 'default'  # Logging modes: 'default', 'all'
    net: pandapipesNet = field(init=False)

    def __init__(self):
        self._set_logging()

    def _set_logging(self):
        if self.logging is 'default':
            warnings.filterwarnings("ignore", message="Pipeflow converged, however, the results are phyisically incorrect as pressure is negative at nodes*")
        elif self.logging is 'all':
            pass
        else:
            warnings.warn(f"Logging mode '{self.logging}' does not exist. Logging mode set to 'all'.")

    def load_network(self, from_file=False, path='', format='json_default', net=pandapipesNet):

        # create empty network
        self.net = pp.create_empty_network("net", add_stdtypes=False)

        # create fluid
        pp.create_fluid_from_lib(self.net, "water", overwrite=True)

        if from_file is True:
            # import network components
            import_network_components(self.net, format=format, path=path)

        else:
            self._create_junctions()
            self._create_pipes()
            self._create_external_grid()
            self._create_substations()
            self._create_bypass()
            self._create_heatpump()
            self._create_controllers()

        export_network_components(self.net, format='json_default', path='./resources/dh_network/export/')

    def run_simulation(self, t, sim_mode='static'):
        # Run hydraulic flow (steady-state)
        run_hydraulic_control(self.net, t)

        if sim_mode is 'static':
            run_static_pipeflow(self.net)
        elif sim_mode is 'dynamic':
            run_dynamic_pipeflow(self.net, t)
        else:
            warnings.warn(f"Simulation mode '{sim_mode}' does not exist. Simulation has stopped.")

    def get_value_of_network_component(self, type, name, parameter):
        error = False

        # Get corresponding network component
        if type is 'sink':
            component = self.net.sink
            result = self.net.res_sink
        elif type is 'source':
            component = self.net.source
            result = self.net.res_source
        elif type is 'junction':
            component = self.net.junction
            result = self.net.res_junction
        elif type is 'valve':
            component = self.net.valve
            result = self.net.res_valve
        elif type is 'ext_grid':
            component = self.net.ext_grid
            result = self.net.res_ext_grid
        elif type is 'heat_exchanger':
            component = self.net.heat_exchanger
            result = self.net.res_heat_exchanger
        else:
            warnings.warn(f"Component {name} cannot be found. Update not successful.")
            error = True

        if not error:
            val = get_value_of(component, name, type, parameter, result)
            return val

    def set_value_of_network_component(self, type, name, parameter, value):
        error = False

        # Get corresponding network component
        if type is 'sink':
            component = self.net.sink
        elif type is 'source':
            component = self.net.source
        elif type is 'junction':
            component = self.net.junction
        elif type is 'valve':
            component = self.net.valve
        elif type is 'ext_grid':
            component = self.net.ext_grid
        elif type is 'heat_exchanger':
            component = self.net.heat_exchanger
        elif type is 'controller':
            component = self.net.controller
        else:
            warnings.warn(f"Component {name} cannot be found. Update not successful.")
            error = True

        if not error:
            set_value_of(component, name, type, parameter, value)

    def _add_to_component_list(self, df):
        if not self.componentList:
            self.componentList = [df]
        else:
            self.componentList.append(df)

    def _plot(self):
        # plot network
        plot.simple_plot(self.net, plot_sinks=True, plot_sources=True, sink_size=4.0, source_size=4.0)

    def load_data(self):
        file = ''
        profiles_source = pd.read_csv(file, index_col=0)
        data_source = DFData(profiles_source)
        return data_source

    def _create_junctions(self):
        # create nodes (with initial pressure and temperature)
        pn_init = 6
        tfluid_init = 273.15 + 75
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n1s", geodata=(0, 1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n1r", geodata=(0, -2.1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n2s", geodata=(3, 1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n2r", geodata=(3, -2.1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3s", geodata=(6, 1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3s_tank", geodata=(6, 3))  # create hp+tank injection point
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3sv", geodata=(6, 1.4))  # create tank valve
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3r", geodata=(6, -2.1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3r_tank", geodata=(6, -4.1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n4s", geodata=(10, 1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n4r", geodata=(11, -2.1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n5sv", geodata=(10, 1.5))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n5s", geodata=(10, 4))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n5r", geodata=(11, 4))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n6s", geodata=(15, 1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n6r", geodata=(16, -2.1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n7sv", geodata=(15, 1.5))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n7s", geodata=(15, 4))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n7r", geodata=(16, 4))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n8s", geodata=(19, 1))
        pp.create_junction(self.net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n8r", geodata=(19, -2.1))

    def _create_external_grid(self):
        net = self.net
        j = self.net.junction['name'].to_list()
        t_supply_grid_k = 273.15 + 75
        mdot_init = 7.5

        # create external grid
        pp.create_ext_grid(net, junction=j.index('n1s'), p_bar=6.0, t_k=t_supply_grid_k, name="ext_grid", type="pt")

        # create sink and source
        pp.create_sink(net, junction=j.index('n1r'), mdot_kg_per_s=mdot_init, name="sink_grid")
        pp.create_source(net, junction=j.index('n1r'), mdot_kg_per_s=0, name='source_grid')

    def _create_pipes(self):
        net = self.net
        j = self.net.junction['name'].to_list()

        l01 = 0.5

        # supply pipes
        pp.create_pipe_from_parameters(net, from_junction=j.index('n1s'), to_junction=j.index('n2s'), length_km=l01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l1s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n3sv'), to_junction=j.index('n3s'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l1s_tank")  # create tank pipe connection
        pp.create_pipe_from_parameters(net, from_junction=j.index('n3s'), to_junction=j.index('n4s'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l2s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n4s'), to_junction=j.index('n5sv'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l3s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n4s'), to_junction=j.index('n6s'), length_km=0.5,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l4s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n6s'), to_junction=j.index('n7sv'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l5s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n6s'), to_junction=j.index('n8s'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l6s")

        # return pipes
        pp.create_pipe_from_parameters(net, from_junction=j.index('n2r'), to_junction=j.index('n1r'), length_km=l01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l1r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n3r'), to_junction=j.index('n3r_tank'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l1r_tank")  # create tank pipe connection
        pp.create_pipe_from_parameters(net, from_junction=j.index('n4r'), to_junction=j.index('n3r'), length_km=0.5,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l2r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n5r'), to_junction=j.index('n4r'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l3r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n6r'), to_junction=j.index('n4r'), length_km=0.5,
                                       diameter_m=0.1, k_mm=0.01, sections=5, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l4r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n7r'), to_junction=j.index('n6r'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l5r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n8r'), to_junction=j.index('n6r'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l6r")

        # create grid connector valves
        pp.create_valve(net, j.index('n2s'), j.index('n3s'), diameter_m=0.1, loss_coefficient=1000, opened=True, name="grid_v1")

    def _create_controllers(self):
        v = self.net.valve['name'].to_list()

        # create supply flow control
        CtrlValve(net=self.net, valve_id=v.index('tank_v1'), gain=-3000,
                  # data_source=data_source, profile_name='tank',
                  level=0, order=1, tol=0.25, name='tank_ctrl')

        CtrlValve(net=self.net, valve_id=v.index('grid_v1'), gain=-3000,
                  # data_source=data_source, profile_name='tank',
                  level=0, order=2, tol=0.25, name='grid_ctrl')

        # create load flow control
        CtrlValve(net=self.net, valve_id=v.index('bypass'), gain=-2000,
                  # data_source=data_source, profile_name='bypass',
                  level=1, order=1, tol=0.25, name='bypass_ctrl')
        CtrlValve(net=self.net, valve_id=v.index('sub_v1'), gain=-100,
                  # data_source=data_source, profile_name='hex1',
                  level=1, order=2, tol=0.1, name='hex1_ctrl')
        CtrlValve(net=self.net, valve_id=v.index('sub_v2'), gain=-100,
                  # data_source=data_source, profile_name='hex2',
                  level=1, order=3, tol=0.1, name='hex2_ctrl')

    def _create_substations(self):
        net = self.net
        j = self.net.junction['name'].to_list()
        q_hex1 = 500 * 1000
        q_hex2 = 500 * 1000

        # create control valves
        pp.create_valve(net, j.index('n5sv'), j.index('n5s'), diameter_m=0.1, opened=True, loss_coefficient=1000, name="sub_v1")
        pp.create_valve(net, j.index('n7sv'), j.index('n7s'), diameter_m=0.1, opened=True, loss_coefficient=1000, name="sub_v2")

        # create heat exchanger
        pp.create_heat_exchanger(net, from_junction=j.index('n5s'), to_junction=j.index('n5r'), diameter_m=0.1,
                                 qext_w=q_hex1, name="hex1")
        pp.create_heat_exchanger(net, from_junction=j.index('n7s'), to_junction=j.index('n7r'), diameter_m=0.1,
                                 qext_w=q_hex2, name="hex2")

    def _create_heatpump(self):
        net = self.net
        j = self.net.junction['name'].to_list()
        mdot_tank_init = 0
        t_supply_tank_k = 70 + 273.15
        p_bar_set = 6.0
        q_hp_evap = 0

        # create hp evaporator
        pp.create_heat_exchanger(net, from_junction=j.index('n3r'), to_junction=j.index('n2r'), diameter_m=0.1,
                                 qext_w=q_hp_evap, name="hp_evap")

        # create tank supply
        pp.create_ext_grid(net, junction=j.index('n3s_tank'), p_bar=p_bar_set, t_k=t_supply_tank_k, name="supply_tank", type="pt")

        # create tank mass flow sink
        pp.create_sink(net, junction=j.index('n3r_tank'), mdot_kg_per_s=mdot_tank_init, name="sink_tank")

        # create valves
        pp.create_valve(net, j.index('n3s_tank'), j.index('n3sv'), diameter_m=0.1, opened=True, loss_coefficient=1000, name="tank_v1")

    def _create_bypass(self):
        net = self.net
        j = self.net.junction['name'].to_list()

        # create bypass valve
        pp.create_valve(net, j.index('n8s'), j.index('n8r'), diameter_m=0.1, opened=True, loss_coefficient=1000, name="bypass")

