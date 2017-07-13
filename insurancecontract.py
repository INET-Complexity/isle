"""
 Insurance contract class for ISLE.
 
 Created by Torsten Heinrich, Davoud Taghawi-Nejad.
"""

# import general python modules
import pdb

# import ISLE modules
from contract import Contract

# InsuranceContract class (inheriting from (ISLE).contract.Contract)
class InsuranceContract(Contract):
    #def __init__(self, contract_partner, endtime, premium, excess, deductible=0.0):
    def __init__(self, contract_partner, endtime, risk, riskcat, premium, excess, deductible=0.0):
        """Constructor method. Positional arguments:
             contract_partner (dict):       contract partners keys: "policyholder", "insurer" 
             endtime (float):               expiration time (= runtime + present time)
             risk (InsurableRisk object):   insured risk
             riskcat (nested list):         risk category affiliations of the insured risk
             premium (float):               insurance premium
             excess (float):                excess
           Optional argument:
             deductible (float):            deductible
           Returns self."""
        # Call to parent constructor
        Contract.__init__(self, contract_partner, endtime)
        # Record properties 
        assert isinstance(contract_partner, dict)
        self.policyholder = contract_partner['policyholder']
        self.insurer = contract_partner['insurer']
        self.excess = excess
        self.deductible = deductible
        self.insured_risk = risk
        self.risk_category = riskcat
        #pdb.set_trace()
        self.terminated = False
        self.premium = premium
        #self.endtime = endtime			#is in superclass
        
        # Set initial obligations (premium payment to insurer, nothing to policyholder)
        self.obligations['policyholder'] = {'money': premium}
        self.obligations['insurer'] = {'money': 0}
        
    def execute(self, claim):
        """Method for handling claims. Positional argument:
             claim (float): claim
           Returns None. Sends obligation/message effecting payment."""
        covered_claim = min(claim, self.excess)
        self.obligations['insurer']['money'] += max(0, covered_claim - self.deductible)
        #print("DEBUG Claim: {0:f} from insurance firm {1:d}".format(covered_claim - self.deductible, self.insurer[1]), end="")
    
    def terminate(self):
        """Method to terminate the contract. Currently only call to parent. Any further code
           to be executed on termination but specific to InsuranceContracts should go here."""
        super(InsuranceContract, self).terminate()
        
