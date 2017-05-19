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


simulation_parameters = {'name': 'name',
                         'scheduledEndTime': 200,
                         'numberOfInsurers': 5,
                         'numberOfRiskholders': 100,
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

        events = defaultdict(list)


        for round in simulation.next_round():
            new_events = insurancecustomers.do('randomAddRisk')
            for event_time, risk in new_events:
                events[event_time].append(risk)
            for risk in events[round]:
                risk.explode()
            insurancefirms.do('quote')
            insurancecustomers.do('subscribe_coverage')
            insurancefirms.do('add_contract')
            allagents.do('filobl')
            insurancecustomers.do('check_risk')

        simulation.graphs()

if __name__ == '__main__':
    main(simulation_parameters)
