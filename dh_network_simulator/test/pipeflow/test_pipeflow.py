import pytest
from dh_network_simulator import DHNetworkSimulator


def test_static_pipeflow():
    dhn_sim = DHNetworkSimulator()
    dhn_sim.load_network(from_file=True, path='../resources/import/', format='json_default')
    for t in range(0, 60, 60):
        dhn_sim.run_simulation(t, sim_mode='static')

def test_dynamic_pipeflow():
    dhn_sim = DHNetworkSimulator()
    dhn_sim.load_network(from_file=True, path='../resources/import/', format='json_readable')
    _init_network_control(dhn_sim)
    for t in range(0, 60, 60):
        dhn_sim.run_simulation(t, sim_mode='dynamic')


def _init_network_control(dhn_sim):
    # Inputs
    Qdot_evap: float = 0  # Heat consumption of heat pump evaporator [kW]
    Qdot_cons1: float = 500  # Heat consumption of consumer 1 [kW]
    Qdot_cons2: float = 500  # Heat consumption of consumer 2 [kW]
    T_tank_forward: float = 70  # Supply temp of storage unit [degC]
    mdot_cons1_set = 4  # Mass flow at consumer 1 [kg/s]
    mdot_cons2_set = 4  # Mass flow at consumer 2 [kg/s]
    mdot_bypass_set = 0.5  # Mass flow through bypass (const.) [kg/s]
    mdot_tank_in_set = 0  # Mass flow injected in the tank [kg/s]
    mdot_tank_out_set = - mdot_tank_in_set  # Mass flow supplied by the tank [kg/s]
    mdot_grid_set = mdot_cons1_set + mdot_cons2_set + mdot_bypass_set - mdot_tank_out_set

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
    # # Update load
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


if __name__ == '__main__':
    pytest.main(["test_pipeflow.py"])
