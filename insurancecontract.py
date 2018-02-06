from metainsurancecontract import MetaInsuranceContract


class InsuranceContract(MetaInsuranceContract):
    """ReinsuranceContract class.
        Inherits from InsuranceContract.
        Constructor is not currently required but may be used in the future to distinguish InsuranceContract
            and ReinsuranceContract objects.
        The signature of this class' constructor is the same as that of the InsuranceContract constructor.
        The class has two methods (explode, mature) that overwrite methods in InsuranceContract."""

    def __init__(self, insurer, properties, time, premium, runtime, payment_period, expire_immediately, initial_VaR=0.,\
                 insurancetype="proportional", deductible_fraction=None, excess_fraction=None, reinsurance=0):
        super(InsuranceContract, self).__init__(insurer, properties, time, premium, runtime, payment_period, \
                                                  expire_immediately, initial_VaR, insurancetype, deductible_fraction,
                                                  excess_fraction, reinsurance)

        self.risk_data = properties

    def explode(self, time, uniform_value, damage_extent):
        """Explode method.
               Accepts arguments
                   time: Type integer. The current time.
                   uniform_value: Type float. Random value drawn in InsuranceSimulation. To determine if this risk
                                  is affected by peril.
                   damage_extent: Type float. Random value drawn in InsuranceSimulation. To determine the extent of
                                  damage caused in the risk insured by this contract.
               No return value.
        For registering damage and creating resulting claims (and payment obligations)."""
        # np.mean(np.random.beta(1, 1./mu -1, size=90000))
        # if np.random.uniform(0, 1) < self.risk_factor:
        if uniform_value < self.risk_factor:
            # if True:
            claim = min(self.excess, damage_extent * self.value) - self.deductible

            self.current_claim += claim
            self.insurer.receive_obligation(claim, self.property_holder, time + 2)
            # Insurer pays one time step after reinsurer to avoid bankruptcy.
            # TODO: Is this realistic? Change this?
            if self.expire_immediately:
                self.expiration = time
                # self.terminating = True

    def mature(self, time):
        """Mature method.
               Accepts arguments
                    time: Type integer. The current time.
               No return value.
           Returns risk to simulation as contract terminates. Calls terminate_reinsurance to dissolve any reinsurance
           contracts."""
        #self.terminating = True
        self.property_holder.return_risks([self.risk_data])
        self.terminate_reinsurance(time)
