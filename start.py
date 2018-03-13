# import common packages
import numpy as np
import scipy.stats
import math
import sys, pdb
from insurancesimulation import InsuranceSimulation
from insurancefirm import InsuranceFirm
from riskmodel import RiskModel
from reinsurancefirm import ReinsuranceFirm
import isleconfig
import random

def model(simulation_parameters,seed):

    replic_ID = None
    override_no_riskmodels = False

    # create simulation and world objects (identical in non-abce mode)
    if isleconfig.use_abce:
        simulation = abce.Simulation(processes=1,randon_seed = seed)

    simulation_parameters['simulation'] = world = InsuranceSimulation(override_no_riskmodels, replic_ID, simulation_parameters, seed)

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
    return simulation.history_total_cash

# main entry point
if __name__ == "__main__":

    simulation_parameters = isleconfig.simulation_parameters
    seed = random.randint(0, 2 ** 32 - 1)
    model(simulation_parameters, seed)
