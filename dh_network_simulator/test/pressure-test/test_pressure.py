import pandas as pd
import pytest
from matplotlib import pyplot as plt
import logging
from dh_network_simulator import DHNetworkSimulator
from dh_network_simulator.test import test_dir


def test_pressure_drop_at_valves(plot_pressure_results_enabled=False,
                                 valves=['grid_v1', 'tank_v1', 'sub_v1', 'sub_v2'],
                                 controllers=['grid_ctrl', 'tank_ctrl', 'hex1_ctrl', 'hex2_ctrl']):
    # Set simulation time
    sim_period = range(0, 60*60*6, 60)

    # Load simulator with network data
    dhn_sim = DHNetworkSimulator()
    dhn_sim.load_network(from_file=True, path=test_dir+'/resources/pressure-test/', format='json_readable')
    # dhn_sim.plot_network_topology()

    # Load network control setpoints
    inputs = pd.read_csv(test_dir+'/resources/pressure-test/static-pipeflow-results.csv', index_col=[0])

    # Init output data
    df_pressures = pd.DataFrame(columns=valves, index=sim_period)
    df_losscoeff = pd.DataFrame(columns=controllers, index=sim_period)
    df_reynolds = pd.DataFrame(columns=valves, index=sim_period)
    df_mass_flows = pd.DataFrame(columns=valves, index=sim_period)

    for t in sim_period:
        # init controls
        _init_network_controls(dhn_sim, inputs, t)
        # run simulation
        dhn_sim.run_simulation(t, sim_mode='static')
        # collect outputs for pressures, loss coefficients and reynolds numbers
        for valve in valves:
            df_pressures[valve].loc[t] = dhn_sim.get_value_of_network_component(name=valve,
                                                                        type='valve',
                                                                        parameter='p_from_bar')

            df_mass_flows[valve].loc[t] = dhn_sim.get_value_of_network_component(name=valve,
                                                                        type='valve',
                                                                        parameter='mdot_from_kg_per_s')

            df_reynolds[valve].loc[t] = dhn_sim.get_value_of_network_component(name=valve,
                                                                        type='valve',
                                                                        parameter='reynolds')

        for controller in controllers:
            df_losscoeff[controller].loc[t] = dhn_sim.get_value_of_network_component(name=controller,
                                                                            type='controller',
                                                                            parameter='loss_coeff')

    # Plot results
    if plot_pressure_results_enabled == True:
        df_pressures.plot(xlabel='Time (s)', ylabel='Pressure (bar)', title='Pressure flow at network valves')
        df_losscoeff.plot(xlabel='Time (s)', ylabel='Loss coefficient', title='Loss coefficients at network valves')
        df_reynolds.plot(xlabel='Time (s)', ylabel='Reynolds', title='Reynolds number at network valves')
        df_mass_flows.plot(xlabel='Time (s)', ylabel='mdot (kg/s)', title='Mass flows at network valves')

    # assert if pressures at network valves are greater than the allowed minimum of 1.5bar
    # p_min = 1.5
    # assert df_pressures > p_min  TODO: Assert all pressures in the network!

def _init_network_controls(dhn_sim, inputs, t):
    # Inputs
    Qdot_evap = inputs['Qdot_evap'].loc[t]  # Heat consumption of heat pump evaporator [kW]
    Qdot_cons1 = inputs['Qdot_cons1'].loc[t]  # Heat consumption of consumer 1 [kW]
    Qdot_cons2 = inputs['Qdot_cons2'].loc[t]  # Heat consumption of consumer 2 [kW]
    T_tank_forward = inputs['T_tank_forward'].loc[t]  # Supply temp of storage unit [degC]
    mdot_cons1_set = inputs['mdot_cons1_set'].loc[t]  # Mass flow at consumer 1 [kg/s]
    mdot_cons2_set = inputs['mdot_cons2_set'].loc[t]  # Mass flow at consumer 2 [kg/s]
    mdot_tank_in_set = inputs['mdot_tank_in_set'].loc[t]  # Mass flow injected in the tank [kg/s]
    mdot_tank_out_set = - mdot_tank_in_set  # Mass flow supplied by the tank [kg/s]
    mdot_grid_set = inputs['mdot_grid_set'].loc[t]

    # # Update grid mass flow
    dhn_sim.set_value_of_network_component(name='sink_grid',
                                           type='sink',
                                           parameter='mdot_kg_per_s',
                                           value=mdot_grid_set)

    # # Update controller(s)
    dhn_sim.set_value_of_network_component(name='hex1_ctrl',
                                           type='controller',
                                           parameter='mdot_set_kg_per_s',
                                           value=mdot_cons1_set)
    dhn_sim.set_value_of_network_component(name='hex2_ctrl',
                                           type='controller',
                                           parameter='mdot_set_kg_per_s',
                                           value=mdot_cons2_set)

    dhn_sim.set_value_of_network_component(name='grid_ctrl',
                                           type='controller',
                                           parameter='mdot_set_kg_per_s',
                                           value=mdot_grid_set)
    # # Update tank
    dhn_sim.set_value_of_network_component(name='sink_tank',
                                           type='sink',
                                           parameter='mdot_kg_per_s',
                                           value=mdot_tank_out_set)

    dhn_sim.set_value_of_network_component(name='supply_tank',
                                           type='ext_grid',
                                           parameter='t_k',
                                           value=T_tank_forward + 273.15)

    dhn_sim.set_value_of_network_component(name='tank_ctrl',
                                           type='controller',
                                           parameter='mdot_set_kg_per_s',
                                           value=mdot_tank_out_set)
    # Update heat consumptions
    dhn_sim.set_value_of_network_component(name='hex1',
                                           type='heat_exchanger',
                                           parameter='qext_w',
                                           value=Qdot_cons1 * 1000)

    dhn_sim.set_value_of_network_component(name='hex2',
                                           type='heat_exchanger',
                                           parameter='qext_w',
                                           value=Qdot_cons2 * 1000)

    dhn_sim.set_value_of_network_component(name='hp_evap',
                                           type='heat_exchanger',
                                           parameter='qext_w',
                                           value=0)

if __name__ == '__main__':
    # init logging
    logging.basicConfig(filename='dhn_sim_logging.log', filemode='w', level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('Initialized logger.')

    # run tests
    pytest.main(["test_pressure.py"])
    plt.show()
