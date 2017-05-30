"""
 * Created by Torsten Heinrich
Translated to python by Davoud Taghawi-Nejad
"""
import abce
import random
from insurablerisk import InsurableRisk
from insurancecontract import InsuranceContract

class InsuranceCustomer(abce.Agent):
    def init(self, simulation_parameters, agent_parameters):
        self.num_insurers = simulation_parameters['numberOfInsurers']
        self.create('money', simulation_parameters['start_cash_customer'])
        self.contracts = []
        self.risks = []

    def randomAddRisk(self):
        if random.random() > .9:
            risk = InsurableRisk();
            self.risks.append(risk);
            self.requestInsuranceCoverage(risk)
            return risk.getTimeToNextEvent() + self.round, risk
        else:
            return None, None

    def requestInsuranceCoverage(self, risk):
        for i in range(self.num_insurers):
            self.message('insurancefirm', i, 'request_insurancequote', {'risk': risk,
                                                                         'runtime': risk.runtime,
                                                                         'excess': risk.value,
                                                                         'deductible': 0.0})

    def subscribe_coverage(self):
        messages = self.get_messages('insurancequotes')
        if len(messages) > 0:
            print("ICC quote")
            cc = min(messages, key=lambda x: x.content)
            if cc.content < self.possession('money'):
                print("... should accept")
                risk = self.risks[-1]
                new_contract = InsuranceContract({'policyholder': self.name,
                                                  'insurer':  (cc.sender_group, cc.sender_id)},
                                                 runtime=risk.runtime,
                                                 premium=cc.content,
                                                 excess=risk.value,
                                                 deductible=0.0)
                self.message(cc.sender_group, cc.sender_id, 'addcontract', new_contract.__dict__)
                self.contracts.append(new_contract)
            else:
                print("not accepted, money: {0:8f}, content {1:8f}".format(self.possession('money'), cc.content))

    def filobl(self):
        for contract in self.contracts:
            self.log('obligations', contract.get_obligation('policyholder','money'))
            if contract.get_obligations('policyholder')['money'] > 0:
                contract.fulfill_obligation(self,
                                            von='policyholder',
                                            to='insurer',
                                            delivery={'money': contract.get_obligations('policyholder')['money']})
        self.log('money', self.possession('money'))
        self.log('num_contracts', len(self.contracts))


    def check_risk(self):
        for risk in self.risks:
            if risk.damage > 0:
                insurance_contact = self.insurance_contacts[risk]
                insurance_contact.execute(risk.damage)
