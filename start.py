# import common packages
import numpy as np
import scipy.stats
import math
import sys, pdb
import numba as nb

# import config file and apply configuration
import isleconfig

simulation_parameters = isleconfig.simulation_parameters
replic_ID = None
override_no_riskmodels = False

# handle command line arguments
if (len(sys.argv) > 1):
    if "--abce" in sys.argv:
        # if command line argument --abce is given, override use_abce from config file
        argument_idx = sys.argv.index("--abce")
        assert len(sys.argv) > argument_idx + 1, "Error: No argument given for keyword --abce"
        isleconfig.use_abce = True if int(sys.argv[argument_idx + 1]) == 1 else False
    if "--oneriskmodel" in sys.argv:
        # allow overriding the number of riskmodels from standard config (with 1)
        isleconfig.oneriskmodel = True
        override_no_riskmodels = 1
    if "--riskmodels" in sys.argv:
        # allow overriding the number of riskmodels from standard config (with 1 or other numbers)
        argument_idx = sys.argv.index("--riskmodels")
        assert len(sys.argv) > argument_idx + 1, "Error: No argument given for keyword --riskmodels"
        override_no_riskmodels = int(sys.argv[argument_idx + 1])
    if "--replicid" in sys.argv:
        # if replication ID is given, pass this to the simulation so that the risk profile can be restored
        argument_idx = sys.argv.index("--replicid")
        assert len(sys.argv) > argument_idx + 1, "Error: No argument given for keyword --replicid"
        replic_ID = int(sys.argv[argument_idx + 1])
    if "--replicating" in sys.argv:
        # if this is a simulation run designed to replicate another, override the config filr parameter
        isleconfig.replicating = True
        assert replic_ID is not None, "Error: Replication requires a replication ID to identify run to be replicated"
    if "--randomseed" in sys.argv:
        # allow setting of numpy random seed
        argument_idx = sys.argv.index("--randomseed")
        assert len(sys.argv) > argument_idx + 1, "Error: No argument given for keyword --randomseed"
        randomseed = float(sys.argv[argument_idx + 1])
        seed = int(randomseed)
    else:
        # allow setting of numpy random seed
        np.random.seed()
        seed = np.random.randint(0, 2 ** 31 - 1)
    if "--foreground" in sys.argv:
        # force foreground runs even if replication ID is given (which defaults to background runs)
        isleconfig.force_foreground = True
else:
    # allow setting of numpy random seed
    np.random.seed()
    seed = np.random.randint(0, 2 ** 31 - 1)


# import isle and abce modules
if isleconfig.use_abce:
    #print("Importing abce")
    import abce
    from abce import gui

from insurancesimulation import InsuranceSimulation
from insurancefirm import InsuranceFirm
from riskmodel import RiskModel
from reinsurancefirm import ReinsuranceFirm

# create conditional decorator
def conditionally(decorator_function, condition):
    def wrapper(target_function):
        if not condition:
            return target_function
        return decorator_function(target_function)
    return wrapper

# create non-abce placeholder gui decorator
# TODO: replace this with more elegant solution if possible. Currently required since script will otherwise crash at the conditional decorator below since gui is then undefined
if not isleconfig.use_abce:
    def gui(*args, **kwargs):
        pass


# main function

#@gui(simulation_parameters, serve=True)
@conditionally(gui(simulation_parameters, serve=False), isleconfig.use_abce)
def main(simulation_parameters,seed):

    np.random.seed(seed)

    # create simulation and world objects (identical in non-abce mode)
    if isleconfig.use_abce:
        simulation = abce.Simulation(processes=1,random_seed = seed)

    simulation_parameters['simulation'] = world = InsuranceSimulation(override_no_riskmodels, replic_ID, simulation_parameters)

    if not isleconfig.use_abce:
        simulation = world
    
    # create agents: insurance firms 
    insurancefirms_group = simulation.build_agents(InsuranceFirm,
                                             'insurancefirm',
                                             parameters=simulation_parameters,
                                             agent_parameters=world.agent_parameters["insurancefirm"])
    
    if isleconfig.use_abce:
        insurancefirm_pointers = insurancefirms_group.get_pointer()
    else:
        insurancefirm_pointers = insurancefirms_group
    world.accept_agents("insurancefirm", insurancefirm_pointers, insurancefirms_group)

    # create agents: reinsurance firms 
    reinsurancefirms_group = simulation.build_agents(ReinsuranceFirm,
                                               'reinsurance',
                                               parameters=simulation_parameters,
                                               agent_parameters=world.agent_parameters["reinsurance"])
    if isleconfig.use_abce:
        reinsurancefirm_pointers = reinsurancefirms_group.get_pointer()
    else:
        reinsurancefirm_pointers = reinsurancefirms_group
    world.accept_agents("reinsurance", reinsurancefirm_pointers, reinsurancefirms_group)
    
    # time iteration
    for t in range(simulation_parameters["max_time"]):
        
        # abce time step
        simulation.advance_round(t)
        
        # iterate simulation
        world.iterate(t)
        
        # log data
        if isleconfig.use_abce:
            #insurancefirms.logme()
            #reinsurancefirms.logme()
            insurancefirms_group.agg_log(variables=['cash', 'operational'], len=['underwritten_contracts'])
            #reinsurancefirms_group.agg_log(variables=['cash'])
        else:
            world.save_data()
        
        #print("here")
    
    # finish simulation, write logs
    simulation.finalize()

# main entry point
if __name__ == "__main__":
    main(simulation_parameters, seed)
