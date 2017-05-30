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
            print("IF quote")
            self.message(request.sender_group, request.sender_id, 'insurancequotes', self.acceptInsuranceContract(request.content))

    def acceptInsuranceContract(self, request):
        return self.riskmodel.evaluate(request['runtime'], request['excess'] , request['deductible'])

    def add_contract(self):
        for contract in self.get_messages('addcontract'):
            self.contracts.append(InsuranceContract.generated(contract.content))

    def filobl(self):
        for contract in self.contracts:
            self.log('insurancepayouts', contract.get_obligation('insurer','money'))

            if contract.get_obligation('insurer', 'money') > 0:
                contract.fulfill_obligation(self,
                                            von='insurer',
                                            to='policyholder',
                                            delivery={'money': contract.get_obligation('insurer','money')})
        self.log('money', self.possession('money'))
        self.log('num_contracts', len(self.contracts))

