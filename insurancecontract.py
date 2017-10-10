import numpy as np

class InsuranceContract():
    def __init__(self, insurer, properties, time, premium, runtime, deductible=0, excess=None, reinsurance=0,
                 reinrisk=None):
        self.insurer = insurer
        self.risk_factor = properties["risk_factor"]
        self.category = properties["category"]
        self.property_holder = properties["owner"]
        self.value = properties["value"]
        self.contract = properties.get("contract")  # will assign None if key does not exist
        if self.contract is not None:
            self.contract.reinsurer = self.insurer  #TODO: do not write into other object's attributes!
        
        self.properties = properties
        self.runtime = runtime
        self.expiration = runtime + time
        
        ##In the future should be able to accept deductible from properties:
        #self.deductible = properties.get("deductible")
        #if self.deductible is None:
        #    self.deductible = deductible if deductible is not None else 0
        self.deductible = deductible
        
        self.excess = excess if excess is not None else self.value
        self.reinsurance = reinsurance
        self.reinrisk = reinrisk
        self.reinsurer = None
        self.reincontract = None
        self.reinsurance_share = None
        self.property_holder.receive_obligation(premium * (self.excess - self.deductible), self.insurer, time)


    def explode(self, expire_immediately, time, uniform_value, damage_extent):
        # np.mean(np.random.beta(1, 1./mu -1, size=90000))
        # if np.random.uniform(0, 1) < self.risk_factor:
        if uniform_value < self.risk_factor:
            # if True:
            claim = damage_extent * self.excess - self.deductible
            if (self.reincontract != None):
                self.reinsurer.reinsurer_receive_obligation(claim, self.insurer, time)
                self.reincontract.explode(True, time)
            self.insurer.receive_obligation(claim, self.property_holder, time + 2)
            if expire_immediately:
                self.expiration = time
    
    def mature(self):
        self.property_holder.return_risks([self.properties])

    def reinsure(self, reinsurance_share):
        self.reinsurance = self.value * reinsurance_share
        self.reinsurance_share = reinsurance_share
        
        # Values other than 0.0 and 1.0 are not implemented (will break the risk model.
        # Assert that it breaks if other values are found.
        assert self.reinsurance_share in [None, 0.0, 1.0] 

