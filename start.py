"""
 * Created by Torsten Heinrich
 */
Translated to python by Davoud Taghawi-Nejad
"""

from __future__ import division
from insurancefirm import InsuranceFirm
from insurancecustomer import InsuranceCustomer
from riskcategory import RiskCategory
from abce import Simulation, gui
from collections import defaultdict

import math
import scipy
import pdb

simulation_parameters = {'name': 'name',
                         'scheduledEndTime': 200,
                         'numberOfInsurers': 5,
                         'numberOfRiskholders': 100,
                         'start_cash_insurer': 100000.0,
                         'start_cash_customer': 100000.0,
                         'defaultContractRuntime': 10,
                         'defaultContractExcess': 100,
                         'numberOfRiskCategories': 5#,
                         }

#@gui(simulation_parameters)
def main(simulation_parameters):
        simulation = Simulation(rounds=simulation_parameters['scheduledEndTime'], processes=1)

        insurancefirms = simulation.build_agents(InsuranceFirm, 'insurancefirm',
                       number=simulation_parameters['numberOfInsurers'],
                       parameters=simulation_parameters)
        insurancecustomers = simulation.build_agents(InsuranceCustomer, 'insurancecustomer',
                       number=simulation_parameters['numberOfRiskholders'],
                       parameters=simulation_parameters)
        allagents = insurancefirms + insurancecustomers
        ic_objects = insurancecustomers.do('get_object')
        #print(type(insurancecustomers))
        #pdb.set_trace()
        
        riskcategories = [RiskCategory(0, simulation_parameters['scheduledEndTime']) for i in range(simulation_parameters['numberOfRiskCategories'])]
        
        events = defaultdict(list)
        
        for round in simulation.next_round():
            
            #new_events = insurancecustomers.do('randomAddRisk')
            new_events = []
            
            if round == 0:
                #workaround (for agent methods with arguments), will not work multi-threaded because of pointer/object reference space mismatch
                new_events = [ic.startAddRisk(15, simulation_parameters['scheduledEndTime'], riskcategories) for ic in ic_objects]
                new_events = [event for agent_events in new_events for event in agent_events]
                #pdb.set_trace()
            for risk in events[round]:
                new_events += [risk.explode(round)]		#TODO: does this work with multiprocessing?
            for event_time, risk in new_events:
                if event_time is not None:
                    event_time = math.ceil(event_time)
                    events[event_time].append(risk)
                    assert isinstance(event_time, int)
                    assert risk is not None
                    try:
                        assert event_time >= round
                    except:
                        pdb.set_trace()
            insurancecustomers.do('get_mean_coverage')
            (insurancefirms + insurancecustomers).do('mature_contracts')
            insurancecustomers.do('randomAddCoverage')
            insurancefirms.do('quote')
            insurancecustomers.do('subscribe_coverage')
            insurancefirms.do('add_contract')
            allagents.do('filobl')
            insurancecustomers.do('check_risk')
            print("\nDEBUG start mean cover: ", scipy.mean(insurancecustomers.do('get_mean_coverage')))

        simulation.graphs()

if __name__ == '__main__':
    main(simulation_parameters)
