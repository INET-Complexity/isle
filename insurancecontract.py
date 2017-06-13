"""
 * Created by Torsten Heinrich
 */
Translated by Davoud Taghawi-Nejad
"""
from contract import Contract
import pdb

class InsuranceContract(Contract):
    #def __init__(self, contract_partner, endtime, premium, excess, deductible=0.0):
    def __init__(self, contract_partner, endtime, risk, riskcat, premium, excess, deductible=0.0):
        Contract.__init__(self, contract_partner, endtime)
        assert isinstance(contract_partner, dict)
        self.policyholder = contract_partner['policyholder']
        self.insurer = contract_partner['insurer']
        self.obligations['policyholder'] = {'money': premium}
        self.obligations['insurer'] = {'money': 0}
        self.excess = excess
        self.deductible = deductible
        self.insured_risk = risk
        self. risk_category = riskcat
        #pdb.set_trace()
        self.terminated = False
        self.premium = premium
        #self.endtime = endtime			#is in superclass

    def execute(self, claim):
        covered_claim = min(claim, self.excess)
        self.obligations['insurer']['money'] += max(0, covered_claim - self.deductible)
        print("DEBUG Claim: {0:f} from insurance firm {1:d}".format(covered_claim - self.deductible, self.insurer[1]), end="")
    
    def terminate(self):
        
        # NOTE: Risk should never be handled from the contract object, strictly only from the customer object.
        #       -> will also not work any more, self.insured_risk is only a unique ID
        #if self.valid:
        #    self.insured_risk.set_coverage(False)
        
        super(InsuranceContract, self).terminate()
        
