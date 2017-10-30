
from insurancecontract import InsuranceContract 

class ReinsuranceContract(InsuranceContract):
    """ReinsuranceContract class.
        Inherits from InsuranceContract.
        Constructor is not currently required but may be used in the future to distinguish InsuranceContract
            and ReinsuranceContract objects.
        The signature of this class' constructor is the same as that of the InsuranceContract constructor.
        The class has two methods (explode, mature) that overwrite methods in InsuranceContract."""
    #def __init__(self, insurer, properties, time, premium, runtime, deductible=0, excess=None, reinsurance=0,
    #             reinrisk=None):
    #    super(ReinsuranceContract, self).__init__(insurer, properties, time, premium, runtime, deductible, excess, reinsurance, reinrisk)
    #    self.is_reinsurancecontract = True
        
    def explode(self, expire_immediately, time, uniform_value=None, damage_extent=None):
        """Explode method.
               Accepts agruments
                   expire_immediately: Type boolean. True if the contract expires with the first risk event. False
                                       if multiple risk events are covered.
                   time: Tyoe integer. The current time.
               No return value.
           Method marks the contract for termination.
            """
        if expire_immediately:
            self.expiration = time
            #self.terminating = True
            
    def mature(self, time):
        """Mature method. 
               Accepts arguments
                    time: Tyoe integer. The current time.
               No return value.
           Removes any reinsurance functions this contract has and terminates any reinsurance contracts for this contract."""
        #self.terminating = True
        self.contract.unreinsure()
        self.terminate_reinsurance(time)
        

