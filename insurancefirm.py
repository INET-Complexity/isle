"""
 * Created by Torsten Heinrich
 */
Translated to python by Davoud Taghawi-Nejad
"""

from __future__ import division
import abce
#from riskmodel import RiskModel
#from riskmodel_grouped import RiskModelGrouped
from riskmodel_grouped_iterationstatic import RiskModelGroupedS
from insurancecontract import InsuranceContract
import pdb
import scipy.stats

class InsuranceFirm(abce.Agent):
    def init(self, simulation_parameters, agent_parameters):
        # your agent initialization goes here, not in __init__
        self.riskmodel = RiskModelGroupedS(riskDistribution=scipy.stats.pareto(2., 0., 10.), riskPeriod=scipy.stats.expon(0, 100./1.))
        self.create('money', simulation_parameters['start_cash_insurer'])
        self.contracts = []
        self.underwritten_by_cat = [[0 for i in range(simulation_parameters['numberOfRiskCategories'])] \
                                          for j in range(simulation_parameters['numberOfRiskCategoryDimensions'])]
        self.alive = True
        self.defaulted_numeric = 0.	# This is 0 if self.alive is True, 1 otherwise. We need this to make logging of the number of defaulted firms possible. Once simulation-level logging is implemented, this variable will become unnecessary.

    def set_oblivious(risk_cat_dim):
        self.underwritten_by_cat[risk_cat_dim] = None

    def quote(self):
        for request in self.get_messages('request_insurancequote'):
            quote = self.acceptInsuranceContract(request.content)
            if quote is not None:
                self.message(request.sender_group, request.sender_id, 'insurancequotes', quote)

    def acceptInsuranceContract(self, request):
        if self.alive:
            return self.riskmodel.evaluate(request['risk'], request['riskcat'], request['runtime'], request['excess'] , request['deductible'],  request['time_correlation_weight'], self.underwritten_by_cat, self.possession('money'), time=self.round)
            #return self.riskmodel.evaluate(request['runtime'], request['excess'] , request['deductible'])
        else:
            return None

    def add_contract(self):
        #revenue_sum = 0
        for contract in self.get_messages('addcontract'):
            self.contracts.append(InsuranceContract.generated(contract.content))
            for i in range(len(self.underwritten_by_cat)):
                if self.underwritten_by_cat[i] is not None:
                    risk_cat_current_contract = self.contracts[-1].risk_category[i]
                    self.underwritten_by_cat[i][risk_cat_current_contract] += 1
            ##try:
            ##    print("DEBUG IF {0:d} money in: {1:f}".format(self.id,contract.content["premium"]))
            ##except:
            ##    pdb.set_trace()
            #revenue_sum += contract.content["premium"]
        #try:
        #    print("DEBUG IF {0:d} money in: {1:f}".format(self.id, revenue_sum))
        #except:
        #    pdb.set_trace()
        

    def filobl(self):
        #print("DEBUG IF {0:d} money: {1:f}".format(self.id,self.possession('money')))
        insurance_payouts = 0 
        for contract in self.contracts:
            
            current_payout = contract.get_obligation('insurer', 'money')
            
            if current_payout > 0:
                try:
                    contract.fulfill_obligation(self,
                                            von='insurer',
                                            to='policyholder',
                                            delivery={'money': current_payout})
                    insurance_payouts += current_payout
                except abce.NotEnoughGoods:
                    self.bankrupt()
                #print("DEBUG: Booked claim payout ", current_payout)
        
        self.log('insurancepayouts', insurance_payouts)
        self.log('money', self.possession('money'))
        self.log('num_contracts', len(self.contracts))
        self.log('defaulted', int(self.defaulted_numeric))	
        """ TODO: this data does not produce aggregated statistics 
               -> but logging works fine (csv file has correct data)
               -> it seems unrelated to data type (float or int) or how it is created"""

    def bankrupt(self):
        self.alive = False
        self.defaulted_numeric = 1.
    
    def is_bankrupt(self):		#not used
        return not self.alive

    def mature_contracts(self):
        #for contract in self.contracts:
        #    print(type(contract), contract)
        #    #contract.is_valid()
        #self.contracts = [contract for contract in self.contracts if (contract.get_endtime() < self.round)]
        
        # TODO: does this work with multiprocessing?
        #       -> should work, but it may be good to check that firm and customer agree on contract ending time
        for contract in self.contracts: 
            if (contract.get_endtime() < self.round):
                contract.terminate() 
                for i in range(len(self.underwritten_by_cat)):
                    if self.underwritten_by_cat[i] is not None:
                        self.underwritten_by_cat[i][contract.risk_category[i]] -= 1
        self.contracts = [contract for contract in self.contracts if (contract.is_valid())]

    def printmoney(self):
        print("DEBUG **IF ", self.possession('money'))
