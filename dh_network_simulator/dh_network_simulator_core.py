import pandas as pd
import numpy as np
import math
import pandapipes as pp
import pandapipes.control.run_control as run_control
import sys
from collections import deque
from .io.import_export import *
from .constants import *

# Do not print python UserWarnings
if not sys.warnoptions:
    import warnings

def run_hydraulic_control(net, **kwargs):
    """
        Run hydraulic control step (mass flows and pressures) of the dhs by considering the controller setpoints and hierarchy.
    """
    # run pandapipes hydraulic control
    run_control(net, max_iter=100, **kwargs)


def run_static_pipeflow(net):
    """
        Run the static temperature flow simulation step of the dhs.
    """
    pp.pipeflow(net, transient=False, mode="all", max_iter=100, run_control=True, heat_transfer=True)

def run_dynamic_pipeflow(net, t, historical_data, collector_connections):
    """
        Run the dynamic temperature flow simulation step of the dhs.
    """
    # Dynamic heat flow distribution
    _dynamic_temp_flow_sim(net=net,
                           historical_data=historical_data,
                           t=t)

    # Store historic values
    enqueue_results(net=net,
                    queue=historical_data,
                    collector_connections=collector_connections,
                    cur_t=t)

def _dynamic_temp_flow_sim(net, historical_data, t):
    """
        Dynamic temperature flow simulation step considering the thermal inertia in the network.
    """
    # Get pipe stream according to the temperature flow in the network
    pipe_stream = _get_pipe_stream_of(net=net)

    # Simulate temperature flow according to determined pipe stream
    _dynamic_temp_flow_sim_of(net=net,
                              pipe_stream=pipe_stream,
                              historical_data=historical_data,
                              t=t)

def _dynamic_temp_flow_sim_of(net, pipe_stream, historical_data, t):
    """
        Successive temperature flow calculation for a given pipe stream (from heat injection towards the consumers).
    """
    for pipe in pipe_stream:
        inlet_junction = _get_inlet_junction_of_pipe(net=net,
                                                     pipe=pipe)

        _dynamic_temp_flow_calc_of(net=net,
                                   pipe=pipe,
                                   historical_data=historical_data['junction'][inlet_junction],
                                   inlet_junction=inlet_junction,
                                   t=t)

        _update_temperatures_of_connected_junctions_to(net=net,
                                                       pipe=pipe)

        _update_temperatures_of_connected_hex_to(net=net,
                                                 pipe=pipe)

def _get_inlet_junction_of_pipe(net, pipe):
    """
        Get network junction connected to the inlet of the pipe.
    """
    # Get list of pipes and junction of the network
    p = net.pipe['name'].to_list()
    j = net.junction['name'].to_list()

    # Get index of connected junction to pipe inlet
    index = net.pipe.at[p.index(pipe), 'from_junction']

    return j[index]

def _calc_consumer_return_temperature(net, hex):
    """
        Get network junction connected to the inlet of the pipe.
    """
    h = net.heat_exchanger['name'].to_list()
    p = net.pipe['name'].to_list()

    from_j_id = net.heat_exchanger.at[h.index(hex), 'from_junction']
    to_j_id = net.heat_exchanger.at[h.index(hex), 'to_junction']
    qext_w = net.heat_exchanger.at[h.index(hex), 'qext_w']
    forward_temp = net.res_junction.at[from_j_id, 't_k']
    mdot = net.res_heat_exchanger.at[h.index(hex), 'mdot_from_kg_per_s']
    Cp_w = ISOBARIC_SPECIFIC_HEAT_WATER

    # Set forward temperature to hex component
    net.res_heat_exchanger.at[h.index(hex), 't_from_k'] = forward_temp

    # Calc return temperature at hex component
    return_temp = forward_temp - qext_w / (Cp_w * mdot)

    # Set return temperature at hex component and connected junctions and pipes
    net.res_heat_exchanger.at[h.index(hex), 't_to_k'] = return_temp
    net.res_junction.at[to_j_id, 't_k'] = return_temp

    conn_p_name = net.pipe['name'].loc[net.pipe['from_junction'] == to_j_id].values.tolist()
    for pipe in conn_p_name:
        net.res_pipe.at[p.index(pipe), 't_from_k'] = return_temp

def _get_pipe_stream_of(net, type='pipe'):
    """
        Get the pipe stream in the network from heat injection towards the consumers.
    """
    # Get subset of pipes based on 'type' (deprecated!)
    # pipe_index = net.pipe['name'].loc[net.pipe['type'] == type].index.tolist()

    # Sort pipes by pressure drop along the network
    pipe_stream = _get_pipe_flow_by_pressures(net=net,
                                              pipe_index=net.pipe['name'].index.tolist())

    if not pipe_stream.size:
        # Throw RuntimeError
        raise RuntimeError(f'EmptyPipeStream: No network components of type "{type}" detected.')

    return (pipe_stream)

def _get_pipe_flow_by_pressures(net, pipe_index):
    """
        Get the pipe flow direction in the network from heat injection towards the consumers by analyzing the calculated pressure drops in the system.
    """
    # Get pipe results by index and sort pipes according to their pressures
    index = net.res_pipe.iloc[pipe_index, :].sort_values('p_from_bar', ascending=False).index

    # Re-index pipes according to pressure drop
    pipenames = net.pipe['name'].reindex(index.values).values

    return pipenames

def _dynamic_temp_flow_calc_of(net, pipe, historical_data, inlet_junction, t):
    """
        Dynamic temperature flow calculation for a given pipe based on the mass flow, pipe length and ambient temperature.
    """
    # Set list of network junctions and pipes
    p = net.pipe['name'].to_list()
    j = net.junction['name'].to_list()

    # Get required input parameters
    Cp_w = ISOBARIC_SPECIFIC_HEAT_WATER
    mf = net.res_pipe.at[p.index(pipe), 'mdot_from_kg_per_s']
    dx = net.pipe.at[p.index(pipe), 'length_km'] * 1000
    v_mean = net.res_pipe.at[p.index(pipe), 'v_mean_m_per_s']
    alpha = net.pipe.at[p.index(pipe), 'alpha_w_per_m2k']
    dia = net.pipe.at[p.index(pipe), 'diameter_m']
    loss_coeff = alpha * math.pi * dia  # Heat loss coefficient in [W/mK]
    Ta = net.pipe.at[p.index(pipe), 'text_k']

    # Get historic inlet temperature
    if historical_data['t_k']:
        df = pd.DataFrame().from_records(historical_data['t_k'], columns=['ts', 't_k'], index=['ts'])
        dt = dx / v_mean
        delay_t = t - dt
        Tin = np.interp(delay_t, df.index, df['t_k'])
    else:
        Tin = net.res_junction.at[j.index(inlet_junction), 't_k']

    # Set current inlet temperature of pipe
    net.res_pipe.at[p.index(pipe), 't_from_k'] = Tin

    # Dynamic temperature drop along a pipe
    exp = - (loss_coeff * dx) / (Cp_w * mf)
    Tout = Ta + (Tin - Ta) * math.exp(exp)

    # Set pipe outlet temperature
    net.res_pipe.at[p.index(pipe), 't_to_k'] = Tout

def _get_connected_junctions_id(net, pipe):
    """
        Dynamic temperature flow calculation for a given pipe based on the mass flow, pipe length and ambient temperature.
    """
    p = net.pipe['name'].to_list()
    v = net.valve['name'].to_list()

    # Get connected junctions (direct and indirect)
    # Check direct connection via junction
    j_ids = []
    j_ids.append(net.pipe.at[p.index(pipe), 'to_junction'])

    # Check connection via valve
    valve_names = net.valve['name'].loc[net.valve['from_junction'].isin(j_ids)].values.tolist()
    for valve in valve_names:
        opened = net.valve.at[v.index(valve), 'opened']
        if opened:
            j_ids.append(net.valve.at[v.index(valve), 'to_junction'])

    # Get connected junction names
    j_names = net.junction['name'].iloc[j_ids].values.tolist()

    return j_ids, j_names


def _update_temperatures_of_connected_junctions_to(net, pipe):
    """
        Overwrite the temperatures of the junction(s) connected to the end of a pipe.
    """
    # Get connected junctions to the pipe end
    j_ids, j_names = _get_connected_junctions_id(net=net,
                                                 pipe=pipe)

    # Set temperature at connected junctions
    for junction in j_names:
        _update_pipe_inlet_temperature_at_junction(net=net,
                                                junction=junction)

def _update_temperatures_of_connected_hex_to(net, pipe):
    """
        Overwrite the temperatures of the connected heat exchangers connected to the end of a pipe.
    """
    # Get connected junctions to the pipe end
    j_ids, j_names = _get_connected_junctions_id(net=net,
                                                 pipe=pipe)

    # Set hex consumer return temperature
    hex_name = net.heat_exchanger['name'].loc[net.heat_exchanger['from_junction'].isin(j_ids)].values.tolist()
    for hex in hex_name:
        # Set temperature at the return side of each hex consumer
        _calc_consumer_return_temperature(net=net,
                                          hex=hex)

def _update_pipe_inlet_temperature_at_junction(net, junction):
    """
        Overwrites the inlet temperature of all pipes connected to a junction.
        If a valve is connected to the junction, it also overwrites the inlet temperature of pipes connected to the outlet of the valve.
    """
    j = net.junction['name'].to_list()
    p = net.pipe['name'].to_list()
    v = net.valve['name'].to_list()

    conn_j_id = [j.index(junction)]
    # Get number of incoming pipes
    # Check connection via valve
    conn_v_name = net.valve['name'].loc[net.valve['to_junction'].isin(conn_j_id)].values.tolist()
    for valve in conn_v_name:
        opened = net.valve.at[v.index(valve), 'opened']
        if opened:
            conn_j_id.append(net.valve.at[v.index(valve), 'from_junction'])
    pipes_in = net.pipe['name'].loc[net.pipe['to_junction'].isin(conn_j_id)].values.tolist()

    mfsum = []
    mtsum = []
    if pipes_in:
        for name in pipes_in:
            # Do temperature mix weighted by share of incoming mass flow
            mdot = net.res_pipe.at[p.index(name), 'mdot_from_kg_per_s']
            t_in = net.res_pipe.at[p.index(name), 't_to_k']
            mfsum.append(mdot)
            mtsum.append(mdot * t_in)
        Tset = (1 / sum(mfsum)) * sum(mtsum)
    else:
        raise AttributeError(f"Junction '{junction}' not connected to a network pipe.")

    net.res_junction.at[j.index(junction), 't_k'] = Tset

def set_value_of(component, name, type, parameter, value):
    """
        Public setter for the pandapipes network component parameters and attributes.
    """
    # Call controller object and set attribute by name (str)
    if type == 'controller':
        index = [c.name for c in component['object']].index(name)
        c = component['object'].iloc[index]
        setattr(c, parameter, value)

    # Get parameter from component dataframe
    else:
        index = component.name.to_list().index(name)
        component.at[index, parameter] = value

def get_value_of(component, name, type, parameter, result):
    """
        Public getter for the pandapipes network component parameters and attributes.
    """
    if type == 'controller':
        index = [c.name for c in component['object']].index(name)
        c = component['object'].iloc[index]
        value = getattr(c, parameter)

    else:
        # Search for component index by name
        index = component.name.to_list().index(name)
        value = result.at[index, parameter]

    return value

def enqueue_results(net, cur_t, queue, collector_connections):
    """
        Enqueue simulation results of defined connections to a data storage queue.
    """
    for key, param_list in collector_connections.items():
        component = getattr(net, key)
        result = getattr(net, 'res_'+key)

        for i in component.name:
            for param in param_list:
                index = component['name'].to_list().index(i)
                val = round(result.at[index, param], 2)
                queue[key][i][param].append((cur_t, val))

    return queue

def dequeue_results(t, queue, collector_connections, auto_sizing_enabled='False'):
    """
        Dequeue simulation results of defined connections from a data storage queue.
    """
    if isinstance(queue, list):
        if auto_sizing_enabled == 'True':
            val = queue.pop()
        else:
            val = queue.index()


    elif isinstance(queue, deque):
        if auto_sizing_enabled == 'True':
            val = queue.pop()
        else:
            val = queue.index()

    return val