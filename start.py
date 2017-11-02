from insurancefirm import InsuranceFirm
from riskmodel import RiskModel
from reinsurancefirm import ReinsuranceFirm
#from reinriskmodel import ReinriskModel
import numpy as np
import scipy.stats
import math
import sys, pdb
import numba as nb
#import abce
from insurancesimulation import InsuranceSimulation
#from abce import gui

use_abce = False
if (len(sys.argv) > 1):
    if "--abce" in sys.argv:
        abce_argument_idx = sys.argv.index("--abce")
        assert len(sys.argv) > abce_argument_idx + 1
        use_abce = True if int(sys.argv[abce_argument_idx + 1]) == 1 else False 

if use_abce:
    print("Importing abce")
    import abce
    from abce import gui

replic_ID=None
override_no_riskmodels=False
simulation_parameters={"no_categories": 2,
                       "no_insurancefirms": 20,
                       "no_reinsurancefirms": 2,
                       "no_riskmodels": 2,
                       "norm_profit_markup": 0.15,
                       "rein_norm_profit_markup": 0.15,
                       "mean_contract_runtime": 30,
                       "contract_runtime_halfspread": 10,
                       "max_time": 600,
                       "money_supply": 2000000000,
                       "event_time_mean_separation": 100 / 3.,
                       "expire_immediately": True,
                       "risk_factors_present": False,
                       "risk_factor_lower_bound": 0.4,
                       "risk_factor_upper_bound": 0.6,
                       "initial_acceptance_threshold": 0.5,
                       "acceptance_threshold_friction": 0.9,
                       "initial_agent_cash": 10000,
                       "initial_reinagent_cash": 50000,
                       "interest_rate": 0,
                       "reinsurance_limit": 0.1,
                       "upper_price_limit": 1.2,
                       "lower_price_limit": 0.85,
                       "no_risks": 20000}

@gui(simulation_parameters, serve=True)
def main(simulation_parameters, othervariable = None):
    if use_abce:
        simulation = abce.Simulation(processes=1)
    
    simulation_parameters['simulation'] = world = InsuranceSimulation(override_no_riskmodels, replic_ID, simulation_parameters)

    if not use_abce:
        simulation = world

    # set up insurance firms
    agent_parameters = []

    for i in range(simulation_parameters["no_insurancefirms"]):
        riskmodel = world.riskmodels[i % len(world.riskmodels)]
        #print(riskmodel)
        agent_parameters.append({'id': i, 'initial_cash': simulation_parameters["initial_agent_cash"],
                                 'riskmodel': riskmodel, 'norm_premium': world.norm_premium,
                                 'profit_target': simulation_parameters["norm_profit_markup"],
                                 'initial_acceptance_threshold': simulation_parameters["initial_acceptance_threshold"],
                                 'acceptance_threshold_friction': simulation_parameters["acceptance_threshold_friction"],
                                 'reinsurance_limit': simulation_parameters["reinsurance_limit"],
                                 'interest_rate': simulation_parameters["interest_rate"]})
    world.insurancefirms = insurancefirms = simulation.build_agents(InsuranceFirm,
                                                       'insurancefirm',
                                                       parameters=simulation_parameters,
                                                       agent_parameters=agent_parameters)

    world._insurancefirm_weights = np.asarray([1 for _ in range(len(agent_parameters))])
    world._insurancefirm_new_weights = np.asarray([0 for _ in range(len(agent_parameters))])



    #
    ## set up reinsurance risk models
    #self.reinriskmodels = [ReinriskModel(self.damage_distribution, self.simulation_parameters["expire_immediately"], \
    #                                     self.cat_separation_distribution, self.norm_premium,
    #                                     self.simulation_parameters["no_categories"], \
    #                                     risk_value_mean, \
    #                                     self.simulation_parameters["rein_norm_profit_markup"]) \
    #                       for i in range(self.simulation_parameters["no_reinriskmodels"])]
    #

    # set up reinsurance firms
    agent_parameters = []
    for i in range(simulation_parameters["no_reinsurancefirms"]):
        riskmodel = world.riskmodels[i % len(world.riskmodels)]
        agent_parameters.append({'id': i, 'initial_cash': simulation_parameters["initial_reinagent_cash"],
                            'riskmodel': riskmodel, 'norm_premium': world.norm_premium,
                            'profit_target': simulation_parameters["norm_profit_markup"],
                            'initial_acceptance_threshold': simulation_parameters["initial_acceptance_threshold"],
                            'acceptance_threshold_friction': simulation_parameters["acceptance_threshold_friction"],
                            'reinsurance_limit': simulation_parameters["reinsurance_limit"],
                            'interest_rate': simulation_parameters["interest_rate"]})
    world.reinsurancefirms = reinsurancefirms = simulation.build_agents(ReinsuranceFirm,
                                                                       'reinsurance',
                                                                       parameters=simulation_parameters,
                                                                       agent_parameters=agent_parameters)

    world.reinsurancefirm_weights = np.asarray([1 for _ in range(len(agent_parameters))])
    world._reinsurancefirm_new_weights = np.asarray([simulation_parameters["initial_reinagent_cash"] for _ in range(len(agent_parameters))])

    for t in range(simulation_parameters["max_time"]):
        simulation.advance_round(t)
        print()
        print(t, ": ", len(world.risks))

        # adjust market premiums
        world.adjust_market_premium(capital=sum(insurancefirms.get_cash()))

        # pay obligations
        world.effect_payments(t)

        # identify perils and effect claims
        for categ_id in range(len(world.rc_event_schedule)):
            try:
                if len(world.rc_event_schedule[categ_id]) > 0:
                    assert world.rc_event_schedule[categ_id][0] >= t
            except:
                print("Something wrong; past events not deleted")
            if len(world.rc_event_schedule[categ_id]) > 0 and world.rc_event_schedule[categ_id][0] == t:
                world.rc_event_schedule[categ_id] = world.rc_event_schedule[categ_id][1:]

                # TODO: consider splitting the following lines from this method and running it with nb.jit
                affected_contracts = [contract
                                      for sublist in insurancefirms.get_underwritten_contracts()
                                      for contract in sublist
                                      if contract.category == categ_id]
                no_affected = len(affected_contracts)
                damage = world.damage_distribution.rvs()
                print("**** PERIL ", damage)
                damagevalues = np.random.beta(1, 1./damage -1, size=no_affected)
                uniformvalues = np.random.uniform(0, 1, size=no_affected)
                for i, contract in enumerate(affected_contracts):
                    contract.explode(simulation_parameters["expire_immediately"], t, uniformvalues[i], damagevalues[i])
            else:
                print("Next peril ", world.rc_event_schedule[categ_id])

        # shuffle risks (insurance and reinsurance risks)
        world.shuffle_risks()

        # reset reinweights
        world.reset_reinsurance_weights(reinsurancefirms.zeros())

        # iterate reinsurnace firm agents
        world.reinsurancefirms.iterate(time=t)
        # remove all non-accepted reinsurance risks
        world.reinrisks = []

        # reset weights
        world.reset_insurance_weights(insurancefirms.zeros())

        # iterate insurance firm agents
        world.insurancefirms.iterate(time=t)

        if use_abce:
            #insurancefirms.logme()
            #reinsurancefirms.logme()
            insurancefirms.agg_log(variables=['cash', 'operational'], len=['underwritten_contracts'])
            #reinsurancefirms.agg_log(variables=['cash'])
        
        print("here")
    simulation.finalize()



# main entry point
if __name__ == "__main__":
    main(simulation_parameters, 77)
