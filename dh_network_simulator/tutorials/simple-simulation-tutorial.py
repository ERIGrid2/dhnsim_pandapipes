import logging
from dh_network_simulator import DHNetworkSimulator
from dh_network_simulator.test import test_dir

'''
This is a simple tutorial showing how to use the dh_network_simulator class to run static and dynamic dhn simulations.
'''

# Initialize logger
logging.basicConfig(filename='dhn_sim_logging.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('Initialized logger.')

# Create DHNetworkSimulator instance.
dhn_sim = DHNetworkSimulator()

# Load data either by an existing pandapipes network or via file import.
dhn_sim.load_network(from_file=True, path='./network/', format='json_readable')

# Plot network topology
dhn_sim.plot_network_topology()

# Run static dhn simulation for a time step t
dhn_sim.run_simulation(t=0, sim_mode='static')

# OR: Run dynamic dhn simulation for a time step t
# dhn_sim.run_simulation(t=0, sim_mode='dynamic')

# Get results from Simulator instance by component and parameter
mdot_grid = dhn_sim.get_value_of_network_component(name='grid_v1',
                                                   type='valve',
                                                   parameter='mdot_from_kg_per_s')
