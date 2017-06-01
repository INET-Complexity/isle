"""
 * Created by Torsten Heinrich
 */
Translated to python by Davoud Taghawi-Nejad
"""

from __future__ import division
import abce
from riskmodel import RiskModel
from insurancecontract import InsuranceContract


class InsuranceFirm(abce.Agent):
    def init(self, simulation_parameters, agent_parameters):
        # your agent initialization goes here, not in __init__
        self.riskmodel = RiskModel()
        self.create('money', simulation_parameters['start_cash_insurer'])
        self.contracts = []


    def quote(self):
        for request in self.get_messages('request_insurancequote'):
            self.message(request.sender_group, request.sender_id, 'insurancequotes', self.acceptInsuranceContract(request.content))

    def acceptInsuranceContract(self, request):
        return self.riskmodel.evaluate(request['runtime'], request['excess'] , request['deductible'])

    def add_contract(self):
        for contract in self.get_messages('addcontract'):
            self.contracts.append(InsuranceContract.generated(contract.content))

    def filobl(self):
        insurance_payouts = 0 
        for contract in self.contracts:
            
            current_payout = contract.get_obligation('insurer', 'money')
            
            if current_payout > 0:
                contract.fulfill_obligation(self,
                                            von='insurer',
                                            to='policyholder',
                                            delivery={'money': current_payout})
                insurance_payouts += current_payout
                #print("DEBUG: Booked claim payout ", current_payout)
        
        self.log('insurancepayouts', insurance_payouts)
        self.log('money', self.possession('money'))
        self.log('num_contracts', len(self.contracts))

    def mature_contracts(self):
        #for contract in self.contracts:
        #    print(type(contract), contract)
        #    #contract.is_valid()
        
        #[contract.terminate() for contract in self.contracts if (contract.end_time < self.round)]
        #self.contracts = [contract for contract in self.contracts if (contract.end_time >= self.round)]
        
        [contract.terminate() for contract in self.contracts if (contract.get_endtime() < self.round)]
        self.contracts = [contract for contract in self.contracts if (contract.is_valid())]

    def printmoney(self):
        print("DEBUG **IF ", self.possession('money'))
