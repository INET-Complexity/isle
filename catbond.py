
import isleconfig
import numpy as np
import scipy.stats
from insurancecontract import InsuranceContract
from reinsurancecontract import ReinsuranceContract
from metainsuranceorg import MetaInsuranceOrg
from riskmodel import RiskModel
import sys, pdb
import uuid
import numba as nb

class CatBond(MetaInsuranceOrg):
    def init(self, simulation, per_period_premium, owner, interest_rate = 0):   # do we need simulation parameters
        self.simulation = simulation
        self.id = 0
        self.underwritten_contracts = []
        self.cash = 0
        self.obligations = []
        self.operational = True
        self.owner = owner
        self.per_period_dividend = per_period_premium
        self.interest_rate = interest_rate  # TODO: shift obtain_yield method to insurancesimulation, thereby making it unnecessary to drag parameters like self.interest_rate from instance to instance and from class to class
        #self.simulation_no_risk_categories = self.simulation.simulation_parameters["no_categories"]
    
    # TODO: change start and InsuranceSimulation so that it iterates CatBonds
    
    def iterate(self, time):
        """obtain investments yield"""
        self.obtain_yield(time)

        """realize due payments"""
        self.effect_payments(time)
        print(time, ":", self.id, len(self.underwritten_contracts), self.cash, self.operational)

        """mature contracts"""
        print("Number of underwritten contracts ", len(self.underwritten_contracts))
        maturing = [contract for contract in self.underwritten_contracts if contract.expiration <= time]
        for contract in maturing:
            self.underwritten_contracts.remove(contract)
            contract.mature(time)
        contracts_dissolved = len(maturing)

        """effect payments from contracts"""
        [contract.check_payment_due(time) for contract in self.underwritten_contracts]
        
        if self.underwritten_contracts == []:
            self.mature_bond()  #TODO: mature_bond method should check if operational
            
        else:   #TODO: dividend should only be payed according to pre-arranged schedule, and only if no risk events have materialized so far
            if self.operational:
                self.pay_dividends(time)

        #self.estimated_var()   # cannot compute VaR for catbond as catbond does not have a riskmodel
        
    def set_owner(self, owner):
        self.owner = owner
        print("SOLD")
        #pdb.set_trace()
    
    def set_contract(self, contract):
        self.underwritten_contracts.append(contract)
    
    def mature_bond(self):
        self.pay(self.cash, self.simulation)
        self.simulation.delete_agents("catbond", [self])
        self.operational = False
