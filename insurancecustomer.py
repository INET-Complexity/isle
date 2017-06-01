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
        self.insurance_contract_dict = {}

    def randomAddRisk(self):
        if random.random() > .9:
            risk = InsurableRisk(self.round)
            self.risks.append(risk)
            self.requestInsuranceCoverage(risk)
            #risk.set_coverage()	#risk does not need this information
            retv =  risk.schedule_next_event(self.round)
            #print(retv)
            return retv
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
            cc = min(messages, key=lambda x: x.content)
            if cc.content < self.possession('money'):
                risk = self.risks[-1]
                new_contract = InsuranceContract({'policyholder': self.name,
                                                  'insurer':  (cc.sender_group, cc.sender_id)},
                                                 endtime=risk.runtime + self.round,
                                                 premium=cc.content,
                                                 excess=risk.value,
                                                 deductible=0.0)
                #print(type(new_contract), new_contract)
                self.message(cc.sender_group, cc.sender_id, 'addcontract', new_contract.__dict__)
                self.contracts.append(new_contract)
                self.insurance_contract_dict[risk] = new_contract
            #else:
            #    print("not accepted, money: {0:8f}, content {1:8f}".format(self.possession('money'), cc.content))

    def filobl(self):
        for contract in self.contracts:
            self.log('obligations', contract.get_obligation('policyholder','money'))
            if contract.get_obligations('policyholder')['money'] > 0:
                #print("DEBUG", contract.obligations)
                contract.fulfill_obligation(self,
                                            von='policyholder',
                                            to='insurer',
                                            delivery={'money': contract.get_obligations('policyholder')['money']})
        
        #print("DEBUG", self.possession('money'))
        
        self.log('money', self.possession('money'))
        self.log('num_contracts', len(self.contracts))


    def check_risk(self):
        for risk in self.risks:
            if risk.damage > 0:
                insurance_contact = self.insurance_contract_dict[risk]
                insurance_contact.execute(risk.damage)
                #print(" risk ", risk)
                risk.set_damage(0)

    def mature_contracts(self):
        #for contract in self.contracts:
        #    print(type(contract), contract)
        #    #contract.is_valid()
        #    
        [contract.terminate() for contract in self.contracts if (contract.get_endtime() < self.round)]
        self.contracts = [contract for contract in self.contracts if (contract.is_valid())]

        #for contract in self.contracts:
        #    if time > contract.get_endtime():
        #        contract.terminate()

    def printmoney(self):
        print("DEBUG **IC ", self.possession('money'))
