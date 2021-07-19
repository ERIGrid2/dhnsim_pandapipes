import pytest
import pandapipes as pp
from pandas._testing import assert_frame_equal
from dh_network_simulator.io import import_network_components
from dh_network_simulator.io import export_network_components
from dh_network_simulator.component_models.valve_control import CtrlValve


def test_import_default():
    # create test network
    test_net = _create_test_network()

    # import network from json file
    net = pp.create_empty_network("net", add_stdtypes=False)
    pp.create_fluid_from_lib(net, "water", overwrite=True)
    net = import_network_components(net, path='../resources/import/', format='json_default')

    # assert
    assert_frame_equal(net.controller.loc[:, net.controller.columns != 'object'],
                       test_net.controller.loc[:, test_net.controller.columns != 'object'])
    assert_frame_equal(net.junction, test_net.junction)
    assert_frame_equal(net.pipe, test_net.pipe)
    assert_frame_equal(net.ext_grid, test_net.ext_grid)
    assert_frame_equal(net.heat_exchanger, test_net.heat_exchanger)

def test_import_json_readable():
    # create test network
    test_net = _create_test_network()

    # import network from json file
    net = pp.create_empty_network("net", add_stdtypes=False)
    pp.create_fluid_from_lib(net, "water", overwrite=True)
    net = import_network_components(net, path='../resources/import/', format='json_readable')

    # assert
    assert_frame_equal(net.controller.loc[:, net.controller.columns != 'object'],
                       test_net.controller.loc[:, test_net.controller.columns != 'object'])
    assert_frame_equal(net.junction, test_net.junction)
    assert_frame_equal(net.pipe, test_net.pipe)
    assert_frame_equal(net.ext_grid, test_net.ext_grid)
    assert_frame_equal(net.heat_exchanger, test_net.heat_exchanger)

#### create pandapipes network ####
def _create_test_network():
    net = pp.create_empty_network("net", add_stdtypes=False)
    pp.create_fluid_from_lib(net, "water", overwrite=True)

    _create_junctions(net)
    _create_pipes(net)
    _create_external_grid(net)
    _create_substations(net)
    _create_bypass(net)
    _create_heatpump(net)
    _create_controllers(net)

    return net

def _create_junctions(net):
    # create nodes (with initial pressure and temperature)
    pn_init = 6
    tfluid_init = 273.15 + 75
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n1s", geodata=(0, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n1r", geodata=(0, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n2s", geodata=(3, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n2r", geodata=(3, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3s", geodata=(6, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3s_tank", geodata=(6, 3))  # create hp+tank injection point
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3sv", geodata=(6, 1.4))  # create tank valve
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3r", geodata=(6, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3r_tank", geodata=(6, -4.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n4s", geodata=(10, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n4r", geodata=(11, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n5sv", geodata=(10, 1.5))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n5s", geodata=(10, 4))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n5r", geodata=(11, 4))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n6s", geodata=(15, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n6r", geodata=(16, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n7sv", geodata=(15, 1.5))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n7s", geodata=(15, 4))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n7r", geodata=(16, 4))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n8s", geodata=(19, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n8r", geodata=(19, -2.1))

def _create_external_grid(net):
    j = net.junction['name'].to_list()
    t_supply_grid_k = 273.15 + 75
    mdot_init = 7.5

    # create external grid
    pp.create_ext_grid(net, junction=j.index('n1s'), p_bar=6.0, t_k=t_supply_grid_k, name="ext_grid", type="pt")

    # create sink and source
    pp.create_sink(net, junction=j.index('n1r'), mdot_kg_per_s=mdot_init, name="sink_grid")
    pp.create_source(net, junction=j.index('n1r'), mdot_kg_per_s=0, name='source_grid')

def _create_pipes(net):
    j = net.junction['name'].to_list()

    # supply pipes
    pp.create_pipe_from_parameters(net, from_junction=j.index('n1s'), to_junction=j.index('n2s'), length_km=0.5,
                                   diameter_m=0.1, k_mm=0.01, sections=5, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l1s", type='supplypipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n3sv'), to_junction=j.index('n3s'), length_km=0.01,
                                   diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l1s_tank", type='supplypipe')  # create tank pipe connection
    pp.create_pipe_from_parameters(net, from_junction=j.index('n3s'), to_junction=j.index('n4s'), length_km=0.5,
                                   diameter_m=0.1, k_mm=0.01, sections=5, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l2s", type='supplypipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n4s'), to_junction=j.index('n5sv'), length_km=0.01,
                                   diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l3s", type='supplypipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n4s'), to_junction=j.index('n6s'), length_km=0.5,
                                   diameter_m=0.1, k_mm=0.01, sections=5, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l4s", type='supplypipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n6s'), to_junction=j.index('n7sv'), length_km=0.01,
                                   diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l5s", type='supplypipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n6s'), to_junction=j.index('n8s'), length_km=0.01,
                                   diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l6s", type='supplypipe')

    # return pipes
    pp.create_pipe_from_parameters(net, from_junction=j.index('n2r'), to_junction=j.index('n1r'), length_km=0.5,
                                   diameter_m=0.1, k_mm=0.01, sections=5, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l1r", type='returnpipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n3r'), to_junction=j.index('n3r_tank'), length_km=0.01,
                                   diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l1r_tank", type='returnpipe')  # create tank pipe connection
    pp.create_pipe_from_parameters(net, from_junction=j.index('n4r'), to_junction=j.index('n3r'), length_km=0.5,
                                   diameter_m=0.1, k_mm=0.01, sections=5, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l2r", type='returnpipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n5r'), to_junction=j.index('n4r'), length_km=0.01,
                                   diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l3r", type='returnpipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n6r'), to_junction=j.index('n4r'), length_km=0.5,
                                   diameter_m=0.1, k_mm=0.01, sections=5, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l4r", type='returnpipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n7r'), to_junction=j.index('n6r'), length_km=0.01,
                                   diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l5r", type='returnpipe')
    pp.create_pipe_from_parameters(net, from_junction=j.index('n8r'), to_junction=j.index('n6r'), length_km=0.01,
                                   diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                   text_k=273.15 + 8, name="l6r", type='returnpipe')

    # create grid connector valves
    pp.create_valve(net, j.index('n2s'), j.index('n3s'), diameter_m=0.1, loss_coefficient=1000, opened=True, name="grid_v1")

def _create_controllers(net):
    v = net.valve['name'].to_list()

    # create supply flow control
    CtrlValve(net=net, valve_id=v.index('tank_v1'), gain=-3000,
              # data_source=data_source, profile_name='tank',
              level=0, order=1, tol=0.25, name='tank_ctrl')

    CtrlValve(net=net, valve_id=v.index('grid_v1'), gain=-3000,
              # data_source=data_source, profile_name='tank',
              level=0, order=2, tol=0.25, name='grid_ctrl')

    # create load flow control
    CtrlValve(net=net, valve_id=v.index('bypass'), gain=-2000,
              # data_source=data_source, profile_name='bypass',
              level=1, order=1, tol=0.25, name='bypass_ctrl')
    CtrlValve(net=net, valve_id=v.index('sub_v1'), gain=-100,
              # data_source=data_source, profile_name='hex1',
              level=1, order=2, tol=0.1, name='hex1_ctrl')
    CtrlValve(net=net, valve_id=v.index('sub_v2'), gain=-100,
              # data_source=data_source, profile_name='hex2',
              level=1, order=3, tol=0.1, name='hex2_ctrl')

def _create_substations(net):
    j = net.junction['name'].to_list()
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

def _create_heatpump(net):
    j = net.junction['name'].to_list()
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

def _create_bypass(net):
    j = net.junction['name'].to_list()

    # create bypass valve
    pp.create_valve(net, j.index('n8s'), j.index('n8r'), diameter_m=0.1, opened=True, loss_coefficient=1000, name="bypass")

if __name__ == '__main__':
    pytest.main(["test_import_export.py"])