import numpy as np

class InsuranceContract():
    def __init__(self, insurer, properties, time, premium, runtime, deductible = 0, excess = None):
        self.insurer = insurer
        self.risk_factor = properties["risk_factor"]
        self.category = properties["category"]
        self.property_holder = properties["owner"]
        self.value = properties["value"]
        self.runtime = runtime
        self.properties = properties
        self.expiration = runtime + time
        self.deductible = deductible
        self.excess = excess if excess != None else self.value
        self.property_holder.receive_obligation(premium * (self.excess - self.deductible), self.insurer, time + 1)
        
    
    def explode(self, expire_immediately, time, uniform_value, damage_extent):
        #np.mean(np.random.beta(1, 1./mu -1, size=90000))
        #if np.random.uniform(0, 1) < self.risk_factor:
        #if uniform_value < self.risk_factor:
        if True:
            claim = damage_extent * self.excess - self.deductible
            self.insurer.receive_obligation(claim, self.property_holder, time + 1)
            if expire_immediately:
                self.expiration = time
    
    def mature(self):
        self.property_holder.return_risks([self.properties])

