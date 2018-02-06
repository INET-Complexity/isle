import numpy as np
import sys, pdb

class MetaInsuranceContract():
    def __init__(self, insurer, properties, time, premium, runtime, payment_period, expire_immediately, initial_VaR=0., \
                       insurancetype="proportional", deductible_fraction=None, excess_fraction=None, reinsurance=0):
        """Constructor method.
               Accepts arguments
                    insurer: Type InsuranceFirm. 
                    properties: Type dict. 
                    time: Type integer. The current time.
                    premium: Type float.
                    runtime: Type integer.
                    payment_period: Type integer.
                    expire_immediately: Type boolean. True if the contract expires with the first risk event. False
                                       if multiple risk events are covered.
                    initial_VaR: Type float. Initial value at risk. Used only to compute true and estimated value at risk. 
                optional:
                    insurancetype: Type string. The type of this contract, especially "proportional" vs "excess_of_loss"
                    deductible: Type float (or int)
                    excess: Type float (or int or None)
                    reinsurance: Type float (or int). The value that is being reinsured.
               Returns InsuranceContract.
           Creates InsuranceContract, saves parameters. Creates obligation for premium payment. Includes contract
           in reinsurance network if applicable (e.g. if this is a ReinsuranceContract)."""
        # TODO: argument reinsurance seems senseless; remove?
        
        # Save parameters
        self.insurer = insurer
        self.risk_factor = properties["risk_factor"]
        self.category = properties["category"]
        self.property_holder = properties["owner"]
        self.value = properties["value"]
        self.contract = properties.get("contract")  # will assign None if key does not exist
        self.insurancetype = properties.get("insurancetype") if insurancetype is None else insurancetype
        self.runtime = runtime
        self.starttime = time
        self.expiration = runtime + time
        self.expire_immediately = expire_immediately
        self.terminating = False
        self.current_claim = 0
        self.initial_VaR = initial_VaR
        
        # set deductible from argument, risk property or default value, whichever first is not None 
        default_deductible_fraction = 0.0
        deductible_fraction_generator = (item for item in [deductible_fraction, properties.get("deductible_fraction"), \
                                                          default_deductible_fraction] if item is not None)
        self.deductible_fraction = next(deductible_fraction_generator)
        self.deductible = self.deductible_fraction * self.value
                
        # set excess from argument, risk property or default value, whichever first is not None 
        default_excess_fraction = 1.0
        excess_fraction_generator = (item for item in [excess_fraction, properties.get("excess_fraction"), \
                                                          default_excess_fraction] if item is not None)
        self.excess_fraction = next(excess_fraction_generator)
        self.excess = self.excess_fraction * self.value
        
        self.reinsurance = reinsurance
        self.reinsurer = None
        self.reincontract = None
        self.reinsurance_share = None
        #self.is_reinsurancecontract = False

        # setup payment schedule
        #total_premium = premium * (self.excess - self.deductible)   # TODO: excess and deductible should not be considered linearily in premium computation; this should be shifted to the (re)insurer who supplies the premium as argument to the contract's constructor method
        total_premium = premium * self.value 
        self.periodized_premium = total_premium / self.runtime
        self.payment_times = [time + i for i in range(runtime) if i % payment_period == 0]
        self.payment_values = total_premium * (np.ones(len(self.payment_times)) / len(self.payment_times))
        
        ## Create obligation for premium payment
        #self.property_holder.receive_obligation(premium * (self.excess - self.deductible), self.insurer, time)
 
        # Embed contract in reinsurance network, if applicable
        if self.contract is not None:
            self.contract.reinsure(reinsurer=self.insurer, reinsurance_share=properties["reinsurance_share"], \
                                   reincontract=self)

    def check_payment_due(self, time):
        if len(self.payment_times) > 0 and time >= self.payment_times[0]:
            # Create obligation for premium payment
            #self.property_holder.receive_obligation(premium * (self.excess - self.deductible), self.insurer, time)
            self.property_holder.receive_obligation(self.payment_values[0], self.insurer, time)
            
            # Remove current payment from payment schedule
            self.payment_times = self.payment_times[1:]
            self.payment_values = self.payment_values[1:]
    
    def get_and_reset_current_claim(self):
        current_claim = self.current_claim
        self.current_claim = 0
        return self.category, current_claim, (self.insurancetype == "proportional")

    
    def terminate_reinsurance(self, time):
        """Terminate reinsurance method.
               Accepts arguments
                    time: Type integer. The current time.
               No return value.
           Causes any reinsurance contracts to be dissolved as the present contract terminates."""
        if self.reincontract is not None:
            self.reincontract.dissolve(time)
    
    def dissolve(self, time):
        """Dissolve method.
               Accepts arguments
                    time: Type integer. The current time.
               No return value.
            Marks the contract as terminating (to avoid new ReinsuranceContracts for this contract)."""
        self.expiration = time

    def reinsure(self, reinsurer, reinsurance_share, reincontract):
        """Reinsure Method.
               Accepts arguments:
                   reinsurer: Type ReinsuranceFirm. The reinsurer.
                   reinsurance_share: Type float. Share of the value that is proportionally reinsured.
                   reincontract: Type ReinsuranceContract. The reinsurance contract.
               No return value.
           Adds parameters for reinsurance of the current contract."""
        self.reinsurer = reinsurer
        self.reinsurance = self.value * reinsurance_share
        self.reinsurance_share = reinsurance_share
        self.reincontract = reincontract
        assert self.reinsurance_share in [None, 0.0, 1.0] 
        
    def unreinsure(self): 
        """Unreinsurance Method.
               Accepts no arguments:
               No return value.
           Removes parameters for reinsurance of the current contract. To be called when reinsurance has terminated."""
        self.reinsurer = None
        self.reincontract = None
        self.reinsurance = 0
        self.reinsurance_share = None
