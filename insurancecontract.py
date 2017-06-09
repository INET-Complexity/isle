"""
 * Created by Torsten Heinrich
 */
Translated by Davoud Taghawi-Nejad
"""
from contract import Contract


class InsuranceContract(Contract):
    def __init__(self, contract_partner, endtime, risk, premium, excess, deductible=0.0):
        Contract.__init__(self, contract_partner, endtime)
        assert isinstance(contract_partner, dict)
        self.policyholder = contract_partner['policyholder']
        self.insurer = contract_partner['insurer']
        self.obligations['policyholder'] = {'money': premium}
        self.obligations['insurer'] = {'money': 0}
        self.excess = excess
        self.deductible = deductible
        self.insured_risk = risk
        self.insured_risk.set_coverage(True)
        self.terminated = False
        #self.endtime = endtime			#is in superclass

    def execute(self, claim):
        covered_claim = min(claim, self.excess)
        self.obligations['insurer']['money'] += max(0, covered_claim - self.deductible)
        #print("DEBUG Claim: {0:f} from insurance firm {1:d}".format(covered_claim - self.deductible, self.insurer[1]), end="")
    
    def terminate(self):
        if self.valid:
            self.insured_risk.set_coverage(False)
        super(InsuranceContract, self).terminate()
        
