# import common packages
import numpy as np
import scipy.stats
import math
import sys, pdb
import numba as nb
import argparse
import pickle
import hashlib
import random 

# import config file and apply configuration
import isleconfig

simulation_parameters = isleconfig.simulation_parameters
replic_ID = None
override_no_riskmodels = False

# use argparse to handle command line arguments
parser = argparse.ArgumentParser(description='Model the Insurance sector')
parser.add_argument("--abce", action="store_true", help="use abce")
parser.add_argument("--oneriskmodel", action="store_true", help="allow overriding the number of riskmodels from the standard config (with 1)")
parser.add_argument("--riskmodels", type=int, choices=[1,2,3,4], help="allow overriding the number of riskmodels from standard config (with 1 or other numbers)")
parser.add_argument("--replicid", type=int, help="if replication ID is given, pass this to the simulation so that the risk profile can be restored")
parser.add_argument("--replicating", action="store_true", help="if this is a simulation run designed to replicate another, override the config file parameter")
parser.add_argument("--randomseed", type=float, help="allow setting of numpy random seed")
parser.add_argument("--foreground", action="store_true", help="force foreground runs even if replication ID is given (which defaults to background runs)")
parser.add_argument("-p", "--showprogress", action="store_true", help="show timesteps")
parser.add_argument("-v", "--verbose", action="store_true", help="more detailed output")
args = parser.parse_args()

if args.abce:
    isleconfig.use_abce = True
if args.oneriskmodel:
    isleconfig.oneriskmodel = True
    override_no_riskmodels = 1
if args.riskmodels:
    override_no_riskmodels = args.riskmodels
if args.replicid is not None:
    replic_ID = args.replicid
if args.replicating:
    isleconfig.replicating = True
    assert replic_ID is not None, "Error: Replication requires a replication ID to identify run to be replicated"
if args.randomseed:
    randomseed = args.randomseed
    seed = int(randomseed)
else:
    np.random.seed()
    seed = np.random.randint(0, 2 ** 31 - 1)
if args.foreground:
    isleconfig.force_foreground = True
if args.showprogress:
    isleconfig.showprogress = True
if args.verbose:
    isleconfig.verbose = True

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
def main():
    
    with open("data/simulation_save.pkl", "br") as rfile:
        d = pickle.load(rfile)
        simulation = d["simulation"]
        world = simulation
        np_seed = d["np_seed"]
        random_seed = d["random_seed"]
        time = d["time"]
        simulation_parameters = d["simulation_parameters"]
    
    insurancefirms_group = list(simulation.insurancefirms)
    reinsurancefirms_group = list(simulation.reinsurancefirms)
    
    #np.random.seed(seed)
    np.random.set_state(np_seed)
    random.setstate(random_seed)
    
    assert not isleconfig.use_abce, "Resuming will not work with abce"
    ## create simulation and world objects (identical in non-abce mode)
    #if isleconfig.use_abce:
    #    simulation = abce.Simulation(processes=1,random_seed = seed)
    #
        
    #simulation_parameters['simulation'] = world = InsuranceSimulation(override_no_riskmodels, replic_ID, simulation_parameters)
    #
    #if not isleconfig.use_abce:
    #    simulation = world
    #
    # create agents: insurance firms 
    #insurancefirms_group = simulation.build_agents(InsuranceFirm,
    #                                         'insurancefirm',
    #                                         parameters=simulation_parameters,
    #                                         agent_parameters=world.agent_parameters["insurancefirm"])
    #
    #if isleconfig.use_abce:
    #    insurancefirm_pointers = insurancefirms_group.get_pointer()
    #else:
    #    insurancefirm_pointers = insurancefirms_group
    #world.accept_agents("insurancefirm", insurancefirm_pointers, insurancefirms_group)
    #
    # create agents: reinsurance firms 
    #reinsurancefirms_group = simulation.build_agents(ReinsuranceFirm,
    #                                           'reinsurance',
    #                                           parameters=simulation_parameters,
    #                                           agent_parameters=world.agent_parameters["reinsurance"])
    #if isleconfig.use_abce:
    #    reinsurancefirm_pointers = reinsurancefirms_group.get_pointer()
    #else:
    #    reinsurancefirm_pointers = reinsurancefirms_group
    #world.accept_agents("reinsurance", reinsurancefirm_pointers, reinsurancefirms_group)
    #
    
    # time iteration
    for t in range(time, simulation_parameters["max_time"]):
        
        # abce time step
        simulation.advance_round(t)
        
        # create new agents             # TODO: write method for this; this code block is executed almost identically 4 times
        if world.insurance_firm_market_entry(agent_type="InsuranceFirm"):
            parameters = [np.random.choice(world.agent_parameters["insurancefirm"])]
            parameters[0]["id"] = world.get_unique_insurer_id()
            new_insurance_firm = simulation.build_agents(InsuranceFirm,
                                             'insurancefirm',
                                             parameters=simulation_parameters,
                                             agent_parameters=parameters)
            insurancefirms_group += new_insurance_firm
            if isleconfig.use_abce:
                # TODO: fix abce
                # may fail in abce because addressing individual agents may not be allowed
                # may also fail because agent methods may not be callable directly
                new_insurancefirm_pointer = [new_insurance_firm[0].get_pointer()]        # index 0 because this is a list with just 1 object
            else:
                new_insurancefirm_pointer = new_insurance_firm
            world.accept_agents("insurancefirm", new_insurancefirm_pointer, new_insurance_firm, time=t)
        
        if world.insurance_firm_market_entry(agent_type="ReinsuranceFirm"):
            parameters = [np.random.choice(world.agent_parameters["reinsurance"])]
            parameters[0]["id"] = world.get_unique_reinsurer_id()
            new_reinsurance_firm = simulation.build_agents(ReinsuranceFirm,
                                             'reinsurance',
                                             parameters=simulation_parameters,
                                             agent_parameters=parameters)
            reinsurancefirms_group += new_reinsurance_firm
            if isleconfig.use_abce:
                # TODO: fix abce
                # may fail in abce because addressing individual agents may not be allowed
                # may also fail because agent methods may not be callable directly
                new_reinsurancefirm_pointer = [new_reinsurance_firm[0].get_pointer()]        # index 0 because this is a list with just 1 object
            else:
                new_reinsurancefirm_pointer = new_reinsurance_firm
            world.accept_agents("reinsurance", new_reinsurancefirm_pointer, new_reinsurance_firm, time=t)
        
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
        
        if t > 0 and t//50 == t/50:
            save_simulation(t, simulation, simulation_parameters, exit_now=False)
        #print("here")
    
    # finish simulation, write logs
    simulation.finalize()


# save function
def save_simulation(t, sim, sim_param, exit_now=False):
    d = {}
    d["np_seed"] = np.random.get_state()
    d["random_seed"] = random.getstate()
    d["time"] = t
    d["simulation"] = sim
    d["simulation_parameters"] = sim_param
    with open("data/simulation_resave.pkl", "bw") as wfile:
        pickle.dump(d, wfile, protocol=pickle.HIGHEST_PROTOCOL)
    with open("data/simulation_resave.pkl", "br") as rfile:
        file_contents = rfile.read()
    #print("\nSimulation hashes: ", hashlib.sha512(str(d).encode()).hexdigest(), "; ",  hashlib.sha512(str(file_contents).encode()).hexdigest())
    # note that the hash over the dict is for some reason not identical between runs. The hash over the state saved to the file is. 
    print("\nSimulation hash: ",  hashlib.sha512(str(file_contents).encode()).hexdigest())    
    if exit_now:
        exit(0)
    
# main entry point
if __name__ == "__main__":
    main()
