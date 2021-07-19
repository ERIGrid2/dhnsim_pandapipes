import pandapipes as pp
import json
from ..component_models.valve_control import CtrlValve
import pandapower.control as control
import pandapipes.plotting as plot

def export_network_components(net, path='', format=''):
    # Default pandapipes json output
    if format is 'json_default':
        pp.to_json(net, path + 'network.json')

    # Readable component-wise json export
    elif format is 'json_readable':
        # Create components list from network
        components_dict = {'junctions': net.junction,
                           'pipes': net.pipe,
                           'heat_exchangers': net.heat_exchanger,
                           'sinks': net.sink,
                           'dh_network_simulator': net.source,
                           'valves': net.valve,
                           'controllers': net.controller
        }

        # Create new network.json file
        for component in components_dict:

            # Setup customized json export for controller components
            if component == 'controllers':
                json_object = [c.to_json() for c in components_dict.get(component)['object']]

            # Default df export for other components
            else:
                json_string = components_dict.get(component).to_json(orient='records')
                json_object = json.loads(json_string)

            # Write json to file
            with open(path + component + '.json', "w") as fout:
                json.dump(json_object, fout, indent=4, sort_keys=True)


def import_network_components(net, format='json_default', path=''):
    # Default pandapipes json import
    if format is 'json_default':
        # Default pandapipes json output
        net = pp.from_json(path + 'network.json')

    # Component-wise import from Readable json files
    elif format is 'json_readable':
        # import components
        _import_junctions_to(net, path)
        _import_pipes_to(net, path)
        _import_sinks_to(net, path)
        _import_sources_to(net, path)
        _import_valves_to(net, path)
        _import_external_grids_to(net, path)
        _import_heat_exchangers_to(net, path)
        _import_controllers_to(net, path)
        # _import_pumps_to(net, path)  # TODO: Import inline pummps (check support of pandapipes)

    return net


def _import_heat_exchangers_to(net, path):
    # Load JSON from file
    f = open(path+'heat_exchangers.json')
    heat_exchangers = json.load(f)

    # add heat exchangers to pandapipes network
    for hex in heat_exchangers:
        pp.create_heat_exchanger(net,
                                 diameter_m=hex.get('diameter_m'),
                                 from_junction=hex.get('from_junction'),
                                 in_service=hex.get('in_service'),
                                 loss_coefficient=hex.get('loss_coefficient'),
                                 name=hex.get('name'),
                                 qext_w=hex.get('qext_w'),
                                 to_junction=hex.get('to_junction'),
                                 type='heat_exchanger')

    return heat_exchangers

def _import_junctions_to(net, path):
    # Load JSON from file
    f = open(path+'junctions.json')
    junctions = json.load(f)

    # add junctions to pandapipes network
    for j in junctions:
        pp.create_junction(net, height_m=j.get('height_m'),
                           pn_bar=j.get('pn_bar'),
                           tfluid_k=j.get('tfluid_k'),
                           name=j.get('name'),
                           in_service=j.get('in_service'),
                           type='junction',
                           geodata=j.get('geodata'))

    return junctions

def _import_pipes_to(net, path):
    # Load JSON from file
    f = open(path+'pipes.json')
    pipes = json.load(f)

    # add pipes to pandapipes network
    for p in pipes:
        pp.create_pipe_from_parameters(net,
                                       from_junction=p.get('from_junction'),
                                       to_junction=p.get('to_junction'),
                                       length_km=p.get('length_km'),
                                       diameter_m=p.get('diameter_m'),
                                       k_mm=p.get('k_mm'),
                                       loss_coefficient=p.get('loss_coefficient'),
                                       sections=p.get('sections'),
                                       alpha_w_per_m2k=p.get('alpha_w_per_m2k'),
                                       text_k=p.get('text_k'),
                                       qext_w=p.get('qext_w'),
                                       name=p.get('name'),
                                       geodata=None,
                                       in_service=p.get('in_service'),
                                       type=p.get('type'))

    return pipes


def _import_sinks_to(net, path):
    # Load JSON from file
    f = open(path+'sinks.json')
    sinks = json.load(f)

    # add sinks to pandapipes network
    for s in sinks:
        pp.create_sink(net,
                       junction=s.get('junction'),
                       mdot_kg_per_s=s.get('mdot_kg_per_s'),
                       scaling=s.get('scaling'),
                       name=s.get('name'),
                       in_service=s.get('in_service'),
                       type='sink')

    return sinks

def _import_sources_to(net, path):
    # Load JSON from file
    f = open(path+'dh_network_simulator.json')
    sources = json.load(f)

    # add dh_network_simulator to pandapipes network
    for s in sources:
        pp.create_source(net,
                       junction=s.get('junction'),
                       mdot_kg_per_s=s.get('mdot_kg_per_s'),
                       scaling=s.get('scaling'),
                       name=s.get('name'),
                       in_service=s.get('in_service'),
                       type='source')

    return sources

def _import_valves_to(net, path):
    # Load JSON from file
    f = open(path+'valves.json')
    valves = json.load(f)

    # add valves to pandapipes network
    for v in valves:
        pp.create_valve(net,
                        from_junction=v.get('from_junction'),
                        to_junction=v.get('to_junction'),
                        diameter_m=v.get('diameter_m'),
                        opened=v.get('opened'),
                        loss_coefficient=v.get('loss_coefficient'),
                        name=v.get('name'),
                        type='valve')

    return valves

def _import_controllers_to(net, path):
    # Load JSON from file
    f = open(path + 'controllers.json')
    controllers = json.load(f)

    # add valves to pandapipes network
    for c in controllers:
        if c.get('type') == 'CtrlValve':
            # create supply flow control
            CtrlValve(net=net,
                      in_service=c.get('in_service'),
                      initial_run=c.get('initial_run'),
                      level=c.get('level'),
                      order=c.get('order'),
                      data_source=c.get('object').get('data_source'),
                      profile_name=c.get('object').get('profile_name'),
                      valve_id=c.get('object').get('valve_id'),
                      mdot_set_kg_per_s=c.get('object').get('mdot_set_kg_per_s'),
                      gain=c.get('object').get('gain'),
                      tol=c.get('object').get('tol'),
                      name=c.get('name')
                      )

        elif c.get('type') == 'ConstControl':
            control.ConstControl(net=net,
                                 in_service=c.get('in_service'),
                                 initial_run=c.get('initial_run'),
                                 level=c.get('level'),
                                 order=c.get('order'),
                                 profile_name=c.get('object').get('profile_name'),
                                 data_source=c.get('object').get('data_source'),
                                 element=c.get('element'),
                                 variable=c.get('variable'),
                                 element_index=c.get('element_index'),
                                 )

    return controllers

def _import_external_grids_to(net, path):
    # Load JSON from file
    f = open(path+'ext_grids.json')
    ext_grids = json.load(f)

    # add valves to pandapipes network
    for g in ext_grids:
        pp.create_ext_grid(net,
                           junction=g.get('junction'),
                           p_bar=g.get('p_bar'),
                           t_k=g.get('t_k'),
                           name=g.get('name'),
                           in_service=g.get('in_service'),
                           type=g.get('type'))

    return ext_grids

def _import_pumps_to(net, path):
    # TODO: Implement import function of pumps
    pumps = []
    return pumps
