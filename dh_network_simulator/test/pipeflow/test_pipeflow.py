import pandas as pd
import pytest
import logging
from dh_network_simulator import DHNetworkSimulator
from dh_network_simulator.test import test_dir


def test_static_pipeflow():
    dhn_sim = DHNetworkSimulator()
    dhn_sim.load_network(from_file=True, path=test_dir+'/resources/import/', format='json_readable')
    inputs = outputs = pd.read_csv(test_dir+'/resources/pipeflow/static-pipeflow-results.csv', index_col=[0])
    for t in range(0, 60*60*3, 60):
        # init
        _init_network_controls(dhn_sim, inputs, t)
        # run simulation
        dhn_sim.run_simulation(t, sim_mode='static')
        # compare results with expected
        _assert_mass_flows(dhn_sim, outputs, t)
        # _assert_temperatures(dhn_sim, outputs, t) TODO: Assert temperatures

def test_dynamic_pipeflow():
    dhn_sim = DHNetworkSimulator()
    dhn_sim.load_network(from_file=True, path=test_dir+'/resources/import/', format='json_readable')
    inputs = outputs = pd.read_csv(test_dir+'/resources/pipeflow/dynamic-pipeflow-results.csv', index_col=[0])
    for t in range(0, 60*60*3, 60):
        # init
        _init_network_controls(dhn_sim, inputs, t)
        # run simulation
        dhn_sim.run_simulation(t, sim_mode='dynamic')
        # compare results with expected
        _assert_mass_flows(dhn_sim, outputs, t)
        # _assert_temperatures(dhn_sim, outputs, t) TODO: Assert temperatures


def _init_network_controls(dhn_sim, inputs, t):
    # Inputs
    Qdot_evap = inputs['Qdot_evap'].loc[t]  # Heat consumption of heat pump evaporator [kW]
    Qdot_cons1 = inputs['Qdot_cons1'].loc[t]  # Heat consumption of consumer 1 [kW]
    Qdot_cons2 = inputs['Qdot_cons2'].loc[t]  # Heat consumption of consumer 2 [kW]
    T_tank_forward = inputs['T_tank_forward'].loc[t]  # Supply temp of storage unit [degC]
    mdot_cons1_set = inputs['mdot_cons1_set'].loc[t]  # Mass flow at consumer 1 [kg/s]
    mdot_cons2_set = inputs['mdot_cons2_set'].loc[t]  # Mass flow at consumer 2 [kg/s]
    mdot_bypass_set = 0.5  # Mass flow through bypass (const.) [kg/s]
    mdot_tank_in_set = inputs['mdot_tank_in_set'].loc[t]  # Mass flow injected in the tank [kg/s]
    mdot_tank_out_set = - mdot_tank_in_set  # Mass flow supplied by the tank [kg/s]
    mdot_grid_set = inputs['mdot_grid_set'].loc[t]

    # # Update grid mass flow
    dhn_sim.set_value_of_network_component(name='sink_grid',
                                           type='sink',
                                           parameter='mdot_kg_per_s',
                                           value=mdot_grid_set)

    # # Update controller(s)
    dhn_sim.set_value_of_network_component(name='bypass_ctrl',
                                           type='controller',
                                           parameter='mdot_set_kg_per_s',
                                           value=mdot_bypass_set)

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
                                           value=Qdot_evap * 1000)

def _assert_temperatures(dhn_sim, outputs, t):
    # Supply temperature at substation 1
    t_supply_hex1 = dhn_sim.get_value_of_network_component(name='n5s',
                                                           type='junction',
                                                           parameter='t_k')
    assert t_supply_hex1 == pytest.approx(outputs['T_supply_cons1'].loc[t] + 273.15, abs=0.5)

    # Return temperature at substation 1
    t_supply_hex2 = dhn_sim.get_value_of_network_component(name='n7s',
                                                           type='junction',
                                                           parameter='t_k')
    assert t_supply_hex2 == pytest.approx(outputs['T_supply_cons2'].loc[t] + 273.15, abs=0.5)

    # Return temperature at substation 1
    t_return_hex1 = dhn_sim.get_value_of_network_component(name='n5r',
                                                           type='junction',
                                                           parameter='t_k')
    assert t_return_hex1 == pytest.approx(outputs['T_return_cons1'].loc[t] + 273.15, abs=0.5)

    # Return temperature at substation 2
    t_return_hex2 = dhn_sim.get_value_of_network_component(name='n7r',
                                                           type='junction',
                                                           parameter='t_k')
    assert t_return_hex2 == pytest.approx(outputs['T_return_cons2'].loc[t] + 273.15, abs=0.5)

    # Return temperature at the storage tank
    t_return_tank = dhn_sim.get_value_of_network_component(name='n3r',
                                                      type='junction',
                                                      parameter='t_k')
    assert t_return_tank == pytest.approx(outputs['T_return_tank'].loc[t] + 273.15, abs=0.5)

    # Return temperature at the supply grid node
    t_return_grid = dhn_sim.get_value_of_network_component(name='n1r',
                                                           type='junction',
                                                           parameter='t_k')
    assert t_return_grid == pytest.approx(outputs['T_return_grid'].loc[t] + 273.15, abs=0.5)

def _assert_mass_flows(dhn_sim, outputs, t):
    # Incoming mass flow at grid supply side node
    mdot_grid = dhn_sim.get_value_of_network_component(name='grid_v1',
                                                       type='valve',
                                                       parameter='mdot_from_kg_per_s')
    assert mdot_grid == pytest.approx(outputs['mdot_grid_set'].loc[t], abs=dhn_sim.get_value_of_network_component(type='controller', name='grid_ctrl', parameter='tol'))

    # Mass flow of storage tank unit
    mdot_tank = -dhn_sim.get_value_of_network_component(name='tank_v1',
                                                       type='valve',
                                                       parameter='mdot_from_kg_per_s')
    assert mdot_tank == pytest.approx(outputs['mdot_tank_in_set'].loc[t], abs=dhn_sim.get_value_of_network_component(type='controller', name='tank_ctrl', parameter='tol'))

    # Mass flow at consumer substation 1
    mdot_cons1 = dhn_sim.get_value_of_network_component(name='sub_v1',
                                                        type='valve',
                                                        parameter='mdot_from_kg_per_s')
    assert mdot_cons1 == pytest.approx(outputs['mdot_cons1_set'].loc[t], abs=dhn_sim.get_value_of_network_component(type='controller', name='hex1_ctrl', parameter='tol'))

    # Mass flow at consumer substation 2
    mdot_cons2 = dhn_sim.get_value_of_network_component(name='sub_v2',
                                                        type='valve',
                                                        parameter='mdot_from_kg_per_s')
    assert mdot_cons2 == pytest.approx(outputs['mdot_cons2_set'].loc[t], abs=dhn_sim.get_value_of_network_component(type='controller', name='hex2_ctrl', parameter='tol'))

    # Bypass flow
    mdot_bypass = dhn_sim.get_value_of_network_component(name='bypass',
                                                         type='valve',
                                                         parameter='mdot_from_kg_per_s')


if __name__ == '__main__':
    # init logging
    logging.basicConfig(filename='dhn_sim_logging.log', filemode='w', level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('Initialized logger.')

    pytest.main(["test_pipeflow.py"])
