
from insurancecontract import InsuranceContract 

class ReinsuranceContract(InsuranceContract):
    """ReinsuranceContract class.
        Inherits from InsuranceContract.
        Constructor is not currently required but may be used in the future to distinguish InsuranceContract
            and ReinsuranceContract objects.
        The signature of this class' constructor is the same as that of the InsuranceContract constructor.
        The class has two methods (explode, mature) that overwrite methods in InsuranceContract."""
    def __init__(self, insurer, properties, time, premium, runtime, payment_period, insurancetype="proportional", deductible=0, excess=None, reinsurance=0):
        super(ReinsuranceContract, self).__init__(insurer, properties, time, premium, runtime, payment_period, insurancetype, deductible, excess, reinsurance)
        #self.is_reinsurancecontract = True
        
        if self.insurancetype == "excess-of-loss":
            self.property_holder.add_reinsurance(category=self.category, excess=self.excess, deductible=self.deductible, contract=self)
        else:
            assert self.contract is not None
        
    def explode(self, expire_immediately, time, uniform_value=None, damage_extent=None):
        """Explode method.
               Accepts agruments
                   expire_immediately: Type boolean. True if the contract expires with the first risk event. False
                                       if multiple risk events are covered.
                   time: Type integer. The current time.
                   uniform_value: Not used
                   damage_extent: Type float. The absolute damage in excess-of-loss reinsurance (not relative as in 
                                       proportional contracts. 
               No return value.
           Method marks the contract for termination.
            """
        if self.insurancetype == "excess-of-loss" and damage_extent > self.deductible:
            claim = min(self.excess, damage_extent) - self.deductible
            if (self.reincontract != None):
                self.reinsurer.receive_obligation(claim, self.insurer, time)
                self.reincontract.explode(True, time)
            
            self.insurer.receive_obligation(claim, self.property_holder, time + 1)
            # Reinsurer pays as soon as possible.
        if expire_immediately:
            self.current_claim += self.contract.claim   # TODO: should proportional reinsurance claims be subject to excess_of_loss retrocession? If so, reorganize more straightforwardly
            
            self.expiration = time
            #self.terminating = True
            
    def mature(self, time):
        """Mature method. 
               Accepts arguments
                    time: Tyoe integer. The current time.
               No return value.
           Removes any reinsurance functions this contract has and terminates any reinsurance contracts for this contract."""
        #self.terminating = True
        self.terminate_reinsurance(time)
        
        if self.insurancetype == "excess-of-loss":
            self.property_holder.delete_reinsurance(category=self.category, excess=self.excess, deductible=self.deductible, contract=self)
        else: #TODO: ? Instead: if self.insurancetype == "proportional":
            self.contract.unreinsure()

    def check_if_liable(self, time, claim):
        self.explode(False, time, damage_extent=claim)
