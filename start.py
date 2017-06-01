"""
 * Created by Torsten Heinrich
 */
Translated to python by Davoud Taghawi-Nejad
"""

from __future__ import division
from insurancefirm import InsuranceFirm
from insurancecustomer import InsuranceCustomer
from abce import Simulation, gui
from collections import defaultdict

import math
#import pdb

simulation_parameters = {'name': 'name',
                         'scheduledEndTime': 200,
                         'numberOfInsurers': 1, #5,
                         'numberOfRiskholders': 1, #100,
                         'start_cash_insurer': 100000.0,
                         'start_cash_customer': 100000.0}

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
        #pdb.set_trace()

        events = defaultdict(list)


        for round in simulation.next_round():
            new_events = insurancecustomers.do('randomAddRisk')
            for risk in events[round]:
                new_events += [risk.explode(round)]
            for event_time, risk in new_events:
                if event_time is not None:
                    event_time = math.ceil(event_time)
                    events[event_time].append(risk)
                    assert isinstance(event_time, int)
                    assert risk is not None
                    assert event_time >= round
            (insurancefirms + insurancecustomers).do('mature_contracts')
            insurancefirms.do('quote')
            insurancecustomers.do('subscribe_coverage')
            insurancefirms.do('add_contract')
            allagents.do('filobl')
            insurancecustomers.do('check_risk')

        simulation.graphs()

if __name__ == '__main__':
    main(simulation_parameters)
