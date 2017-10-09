import numpy as np

class ReinsuranceContract():
    def __init__(self, reinsurer, reinrisk, time, premium, deductible = 0, excess = None):
        self.reinsurer = reinsurer
        self.properties = reinrisk
        print(reinrisk["firm"])
        self.property_holder = reinrisk["firm"]
        self.value = reinrisk["value"]
        self.category = reinrisk["category"]
        self.runtime = reinrisk["runtime"]
        self.expiration = reinrisk["contract"].expiration
        self.contract = reinrisk["contract"]
        self.deductible = deductible
        self.excess = excess if excess != None else self.value
        self.property_holder.receive_obligation(premium * (self.excess - self.deductible), self.reinsurer, time)
        if(len(self.property_holder.underwritten_contracts)>0):
            for contract in self.property_holder.underwritten_contracts:
                if contract.reinrisk!= None:
                    if contract.reinrisk==reinrisk["identifier"]:
                        contract.reinsurer = self.reinsurer



    def explode(self, expire_immediately, time):
        if expire_immediately:
            self.expiration = time
    

