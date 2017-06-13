"""
 * Created by Torsten Heinrich
Translated to python by Davoud Taghawi-Nejad
"""
import abce
import random
#from insurablerisk import InsurableRisk
from categorizedinsurablerisk import CategorizedInsurableRisk
from insurancecontract import InsuranceContract

import pdb

class InsuranceCustomer(abce.Agent):
    def init(self, simulation_parameters, agent_parameters):
        self.num_insurers = simulation_parameters['numberOfInsurers']
        self.create('money', simulation_parameters['start_cash_customer'])
        self.contracts = []
        self.risks = []
        self.insurance_contract_dict = {}
        self.risk_dict = {}
        self.default_contract_runtime = simulation_parameters['defaultContractRuntime']
        self.default_contract_excess = simulation_parameters['defaultContractExcess']
    
    def get_object(self):
        return self

    def startAddRisk(self, number, max_runtime, risk_category_list):
        events = []
        for i in range(number):
            risk = CategorizedInsurableRisk(self.round, max_runtime, risk_category_list)
            self.risks.append(risk)
            events.append(risk.schedule_next_event(self.round))
            self.risk_dict[risk.uuid] = risk
        return events

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

    def randomAddCoverage(self):
        random.shuffle(self.risks)
        for risk in self.risks:
            if self.id==0: print("DEBUG IC randomaddcoverage: ", risk.get_coverage(), risk.uuid)
            if not risk.get_coverage() and random.random() < .8:
                if self.id==0: print("DEBUG IC randomaddcoverage: Coverage requested")
                self.requestInsuranceCoverage(risk, self.default_contract_runtime, self.default_contract_excess)

    def requestInsuranceCoverage(self, risk, runtime = None, excess = None):
        if runtime is None:
            assert risk.runtime is not None
            runtime = risk.runtime
        if excess is None:
            assert risk.value is not None
            runtime = risk.value
        for i in range(self.num_insurers):
            self.message('insurancefirm', i, 'request_insurancequote', { 'risk': risk.uuid,
                                                                         'riskcat': risk.category_id,
                                                                         'runtime': runtime,
                                                                         'excess': excess,
                                                                         'deductible': 0.0,
                                                                         'time_correlation_weight': risk.time_correlation_weight})

    def subscribe_coverage(self):
        messages = self.get_messages('insurancequotes')
        if len(messages) > 0:
            riskuuids = set([message.content[4] for message in messages])
            for riskuuid in riskuuids:
                #pdb.set_trace()
                filtered_messages = [message for message in messages if message.content[4]==riskuuid]
                cc = min(filtered_messages, key=lambda x: x.content)
                if cc.content[0] < self.possession('money'):
                    #risk = cc.content[4]
                    risk = self.risk_dict[riskuuid]
                    new_contract = InsuranceContract({'policyholder': self.name,
                                                      'insurer':  (cc.sender_group, cc.sender_id)},
                                                     endtime=cc.content[1] + self.round,
                                                     risk=riskuuid,
                                                     riskcat=risk.category_id,
                                                     premium=cc.content[0],
                                                     excess=cc.content[2],
                                                     deductible=cc.content[3])
                    #print(type(new_contract), new_contract)
                    self.message(cc.sender_group, cc.sender_id, 'addcontract', new_contract.__dict__)
                    self.contracts.append(new_contract)
                    self.insurance_contract_dict[risk] = new_contract
                    risk.set_coverage(True)
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
        #print("DEBUG check_risk: ", end="")
        for risk in self.risks:
            #print("{0:f}".format(risk.damage), end="")
            if risk.damage > 0:
                #print(" ... DAMAGE".format(risk.damage))
                insurance_contract = self.insurance_contract_dict.get(risk)
                #insurance_contract = self.insurance_contract_dict[risk]
                if insurance_contract is not None:
                    insurance_contract.execute(risk.damage)
                #print(" risk ", risk)
                risk.set_damage(0)
                # TODO: reduce insurancecustomer's money to reflect damage paid

    def mature_contracts(self):
        #for contract in self.contracts:
        #    print(type(contract), contract)
        #    #contract.is_valid()
        #    
        [contract.terminate() for contract in self.contracts if (contract.get_endtime() < self.round)]
        self.contracts = [contract for contract in self.contracts if (contract.is_valid())]
        #print(type(self.insurance_contract_dict), len(self.insurance_contract_dict))
        #self.insurance_contract_dict = {risk: self.insurance_contract_dict[risk] for risk in self.insurance_contract_dict if not self.insurance_contract_dict[risk].is_valid()}
        new_insurance_contract_dict = {}
        for risk in self.insurance_contract_dict:
            contract = self.insurance_contract_dict[risk]
            if contract.is_valid():
                new_insurance_contract_dict[risk] = contract
            else:
                risk.set_coverage(False)
        self.insurance_contract_dict = new_insurance_contract_dict
        #for contract in self.contracts:
        #    if time > contract.get_endtime():
        #        contract.terminate()

    def printmoney(self):
        print("DEBUG **IC ", self.possession('money'))

    def get_mean_coverage(self):
        #if self.id==0: print([1 for risk in self.risks if risk.get_coverage()])
        return sum([1 for risk in self.risks if risk.get_coverage()]) * 1. / len(self.risks) 
