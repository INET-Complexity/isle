import numpy as np
import scipy.stats
import math
import sys, pdb
import numba as nb
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
        # allow overriding the number of riskmodels from standard config
        isleconfig.oneriskmodel = True
        override_no_riskmodels = True         
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
        np.random.seed(randomseed)
    if "--foreground" in sys.argv:
        # force foreground runs even if replication ID is given (which defaults to background runs)
        isleconfig.force_foreground = True

if isleconfig.use_abce:
    #print("Importing abce")
    import abce
    from abce import gui

from insurancesimulation import InsuranceSimulation

from insurancefirm import InsuranceFirm
from riskmodel import RiskModel
from reinsurancefirm import ReinsuranceFirm

#@gui(simulation_parameters, serve=True)
def main(simulation_parameters):
    if isleconfig.use_abce:
        simulation = abce.Simulation(processes=1)
    
    simulation_parameters['simulation'] = world = InsuranceSimulation(override_no_riskmodels, replic_ID, simulation_parameters)

    if not isleconfig.use_abce:
        simulation = world

    insurancefirms = simulation.build_agents(InsuranceFirm,
                                             'insurancefirm',
                                             parameters=simulation_parameters,
                                             agent_parameters=world.agent_parameters["insurancefirm"])
    
    if isleconfig.use_abce:
        insurancefirm_pointers = insurancefirms.get_pointer()
    else:
        insurancefirm_pointers = insurancefirms
    world.accept_agents("insurancefirm", insurancefirm_pointers)

    reinsurancefirms = simulation.build_agents(ReinsuranceFirm,
                                               'reinsurance',
                                               parameters=simulation_parameters,
                                               agent_parameters=world.agent_parameters["reinsurance"])
    if isleconfig.use_abce:
        reinsurancefirm_pointers = reinsurancefirms.get_pointer()
    else:
        reinsurancefirm_pointers = reinsurancefirms
    world.accept_agents("reinsurance", reinsurancefirm_pointers)

    for t in range(simulation_parameters["max_time"]):
        simulation.advance_round(t)
        world.iterate(t)
        
        if isleconfig.use_abce:
            #insurancefirms.logme()
            #reinsurancefirms.logme()
            insurancefirms.agg_log(variables=['cash', 'operational'], len=['underwritten_contracts'])
            #reinsurancefirms.agg_log(variables=['cash'])
        else:
            world.save_data()
        
        #print("here")
    simulation.finalize()

# main entry point
if __name__ == "__main__":
    main(simulation_parameters)
