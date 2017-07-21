"""
Main script of ISLE (Insurance model for the Economic Simulation Library in Environment).
The script uses the ABCE framework for agent-based computational economics. 
start.py serves 3 purposes:
  - handling arguments and parameter definition file
  - provide the main function for the agent-based simulation, which defines object creation, 
    simulation iteration, and data collection.

Two positional terminal arguments may be supplied:
    - first (string): parameter definition file in CWD
    - second (int: 0, 1): whether or not to suppress graphical output 

Created by Torsten Heinrich, Davoud Taghawi-Nejad.
"""

# import general python modules
from __future__ import division
from collections import defaultdict
#import os
import sys
import yaml
import math
import scipy
import scipy.stats
import pdb

# import ABCE modules
from abce import Simulation, gui

# import ISLE modules
from insurancefirm import InsuranceFirm
from insurancecustomer import InsuranceCustomer
from riskcategory import RiskCategory

# main function
def main(simulation_parameters):
    """Main function. Accepts one positional argument (dict): parameter setting for the simulation"""
    
    # Create simulation, supply number of iterations, number of parallel threads to be used.
    simulation = Simulation(processes=1)
    
    # Create agent objects
    insurancefirms = simulation.build_agents(InsuranceFirm, 'insurancefirm',
                   number=simulation_parameters['numberOfInsurers'],
                   parameters=simulation_parameters)
    insurancecustomers = simulation.build_agents(InsuranceCustomer, 'insurancecustomer',
                   number=simulation_parameters['numberOfRiskholders'],
                   parameters=simulation_parameters)
    allagents = insurancefirms + insurancecustomers
    simulation.advance_round(0)

    
    # Workaround: collect pointers to agent objects, to be removed with future version of ABCE.
    ic_objects = list(insurancecustomers.do('get_object'))
    if_objects = list(insurancefirms.do('get_object'))

    # 0. Before first iteration: prepare risk categories and event schedules for risk categories and individual risks
    """0.1 Define globally identical time separation and damage size distributions as well as bernoulli 
                                                          distributions for event schedule mixing"""
    #eventDist = None#scipy.stats.expon(0, 100./3.)
    #eventSizeDist = None#scipy.stats.pareto(2., 0., 10.)
    eventDist = scipy.stats.expon(0, 100./3.)
    eventSizeDist = scipy.stats.pareto(2., 0., 10.)
    bernoulliDistCategory = scipy.stats.bernoulli(simulation_parameters['shareOfCorrelatedRisk'] \
                                                   * 1./simulation_parameters['numberOfRiskCategoryDimensions'])
    bernoulliDistIndividual = scipy.stats.bernoulli(1-simulation_parameters['shareOfCorrelatedRisk'])
    
    # 0.2 Create risk categories
    riskcategories = []
    for i in range(simulation_parameters['numberOfRiskCategoryDimensions']):
        riskcategories.append([RiskCategory(0, simulation_parameters['scheduledEndTime'], \
                                        share_selection_bernoulli_dist = bernoulliDistCategory) \
                                        for i in range(simulation_parameters['numberOfRiskCategories'])])
    
    # Some debugging output, to be removed in future version
    for rc in riskcategories:
        for rc2 in rc:
            print(rc2.eventTimeList)

    # 0.3 Prepare event schedules for all risks for all agents, collect events
    #Workaround (for agent methods with arguments), will not work multi-threaded because of pointer/object reference space mismatch
    new_events = [ic.startAddRisk(15, simulation_parameters['scheduledEndTime'], riskcategories, eventDist, \
                                              eventSizeDist, bernoulliDistIndividual=bernoulliDistIndividual, \
                                              bernoulliDistCategory=bernoulliDistCategory) for ic in ic_objects]
    #new_events = insurancecustomers.do("startAddRisk", 15, simulation_parameters['scheduledEndTime'], riskcategories, eventDist, \
    #                                          eventSizeDist, bernoulliDistIndividual=bernoulliDistIndividual, \
    #                                          bernoulliDistCategory=bernoulliDistCategory)
    
    
    # 0.4 Flatten new_events list
    new_events = [event for agent_events in new_events for event in agent_events]
    
    try:
        # 0.5 Apply risk category awareness setting for insurance firms
        roSetting = simulation_parameters['riskObliviousSetting']           #parameter riskObliviousSetting:
                                                                            #     if 0: all firms aware of all categories 
                                                                            #     if 1: all firms unaware of first category, 
                                                                            #     if 2: half the firms unaware of first category, the other half of the second category
        if roSetting == 1:
            [ifirm.set_oblivious(0) for ifirm in if_objects]
        elif roSetting == 2:
            assert simulation_parameters['numberOfRiskCategoryDimensions'] > 1
            noi = simulation_parameters['numberOfInsurers']
            middle = int(noi/2.)                               #round does not work as round is redefined as int
            [ifirm.set_oblivious(0) for ifirm in if_objects[:middle]]
            [ifirm.set_oblivious(1) for ifirm in if_objects[middle:]]
    except: 
        #pdb.set_trace()
        pass

    # 0.6 prepare list of events and event-times (dict)
    events = defaultdict(list)
    
    # Commence time iteration
    for time in range(simulation_parameters['scheduledEndTime']):
        simulation.advance_round(time)
        
        # Prepare new_events list -> No, was prepared before first iteration!
        #new_events = insurancecustomers.do('randomAddRisk')
        
        # 1. Apply all events scheduled for the current iteration (and collect next events, if any)
        for risk in events[time]:
            new_events += [risk.explode(time)]		#TODO: does this work with multiprocessing?
        
        # (1.b) Sort any new events into events list      #TODO: does this cause events for period zero not to be handled? (There should be no events in period zero (time separation >=1)
        for event_time, risk in new_events:
            if event_time is not None:
                event_time = math.ceil(event_time)
                events[event_time].append(risk)
                assert isinstance(event_time, int)
                assert risk is not None
                try:
                    assert event_time >= time
                except:
                    pdb.set_trace()

        # Some debugging output, to be removed in future version
        insurancecustomers.do('get_mean_coverage')
        # 2. Increment contract age and remove expired contracts
        (insurancefirms + insurancecustomers).do('mature_contracts')
        # 3. Insurance customers solicit insurance contract offers
        insurancecustomers.do('randomAddCoverage')
        # 4. Insurance firms make offers (for contracts the underwriting of which is consistent with their risk model)
        insurancefirms.do('quote')
        # 5. Insurance customers accept best offers
        insurancecustomers.do('subscribe_coverage')
        # 6. Insurance firms record accepted contracts, disregard others
        insurancefirms.do('add_contract')
        # 7. All agents make payments that are due (premiums and claims)
        allagents.do('filobl')
        # 8. Insurance customers file claims for current risk events
        insurancecustomers.do('check_risk')
        # 9. Record data about current iteration
        #(insurancefirms + insurancecustomers).do('logging')    # insurance firms and insurance customers
        (insurancefirms).do('logging')                          # insurance firms only
        ## Some debugging output, to be removed in future version
        #print(sum(list(insurancefirms.do('is_bankrupt'))))
        #print("\nDEBUG start mean cover: ", scipy.mean(insurancecustomers.do('get_mean_coverage')))
        
        # Reset new_events list
        new_events = []
    
    # Some debugging output, to be removed in future version
    for rc in riskcategories:
        for rc2 in rc:
            print(rc2.eventTimeList)
    
    # Graphical output
    if not direct_output_suppressed:    # TODO: make into function parameter?
        simulation.graphs()

# main entry point
if __name__ == '__main__':
    
    # default parameters
    simulation_parameters = {'name': 'name',                       # name of simulation run
                             'scheduledEndTime': 100,              # number of iterations
                             'numberOfInsurers': 10,               # number of insurers
                             'numberOfRiskholders': 1000,          # number of insurance customers
                             'start_cash_insurer': 3000.0,         # initial liquidity per insurer
                             'start_cash_customer': 10000.0,       # initial liquidity per insurance customer
                             'defaultContractRuntime': 10,         # default contract runtime
                             'defaultContractExcess': 100,         # default contract excess
                             'numberOfRiskCategories': 5,          # number of risk categories
                             'shareOfCorrelatedRisk': 0.25,         # default share of correlated risks
                             'numberOfRiskCategoryDimensions': 2,  # number of risk category dimensions
                             'riskObliviousSetting': 2,            # setting of risk category visibility for risk models
                             'series': 'testing'#,                  # series of simulation run
                             }
    
    # Read in arguments
    direct_output_suppressed = False
    if len(sys.argv) > 1:   # Test whether first positional argument (parameter definition file) is supplied.
        
        # If parameter definition file is supplied, read in parameters.
        yamlfilename = sys.argv[1]
        yamlfile = open(yamlfilename, "r")
        spconf = yaml.load(yamlfile)
        simulation_parameters = spconf['simulation_parameters']
        
        if len(sys.argv) > 2:   # Test for second positional argument (suppression of graphical output)
            if int(sys.argv[2]) == 1:
                direct_output_suppressed = True
                print("Graphical output will be suppressed")
    
    ## Comment in to start graphical interface before simulation run.
    #@gui(simulation_parameters)
    
    # Call main function to execute simulation.
    main(simulation_parameters)
