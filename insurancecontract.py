"""
 * Created by Torsten Heinrich
 */
Translated by Davoud Taghawi-Nejad
"""
from contract import Contract


class InsuranceContract(Contract):
    def __init__(self, contract_partner, runtime, premium, excess, deductible=0.0):
        Contract.__init__(self, contract_partner)
        assert isinstance(contract_partner, dict)
        self.policyholder = contract_partner['policyholder'];
        self.insurer = contract_partner['insurer'];
        self.obliations['policyholder'] = {'money': premium}
        self.excess = excess;
        self.deductible = deductible;
        print("contract", premium)

    def execute(self, claim):
        covered_claim = min(claim, self.excess)
        self.obliations['insurer']['money'] += max(0, covered_claim - self.deductible)

