"""
 Contract class for ISLE/ABCE.
 
 Created by Torsten Heinrich, Davoud Taghawi-Nejad.
"""

# import general python modules
from collections import defaultdict

# import ABCE modules
from abce import NotEnoughGoods

# Contract class
class Contract:
    def __init__(self, contract_partners, endtime = None):
        """Constructor method. 
           Arguments:
             contract_parameters (dict): contract parameters
             endtime (float of None): endtime #TODO: should go into contract_parameters
           Returns self."""
        self.contract_partners = contract_partners
        self.obligations = {}
        self.endtime = endtime
        self.valid = True 

    @staticmethod
    def generated(contract_dict):
        """(Quasi-constructor) Method for regenerating existing contracts (e.g., from other threads). 
           Arguments:
             contract_dict (dict): contract attributes and values
           Returns copied Contract object."""
        contract = Contract(None)
        for key in contract_dict:
            contract.__dict__[key] = contract_dict[key]
        return contract

    def get_obligations(self, side):
        """Method for collecting obligations by role/side. 
           Arguments:
             side (any valid dict key): role/side for which obligations following from contract are to be returned
           Returns list of obligations."""
        try:
            return self.obligations[side]
        except KeyError:
            return {}

    def get_obligation(self, side, good):
        """Method for getting single obligation by side and good.
           Arguments:
             side (any valid dict key): role/side for which obligations following from contract are to be returned
             good (string):             type of good in which the obligation to be returned is denominated
           Returns size of obligation."""
        try:
            return self.obligations[side][good]
        except KeyError:
            return 0.0

    def add_obligation(self, side, good, amount):
        """Method for adding obligations.
           Arguments:
             side (any valid dict key): role/side for which obligations following from contract are to be added
             good (string):             type of good in which the obligation to be returned is denominated
             amount (int, float?):      additional amount owed
           Returns None."""
        self.obligations[side][good] += amount

    def substract_obligation(self, side, good, amount):
        """Method for removing obligations.
           Arguments:
             side (valid dict key): role/side for which obligations following from contract are to be removed
             good (string):             type of good in which the obligation to be returned is denominated
             amount (int, float?):      amount by which the total obligation is to be reduced
           Returns None.
           """
        """ no negative obligations, quietly """
        self.obligations[side][good] = min(0, self.obligations[side][good] - amount)

    def fulfill_obligation(self, me, von, to, delivery):
        """Method to record payment of obligation. 
           Arguments:
             me (ABCE.agent.Agent):  agent the possessions of which are modified.
             von (valid dict key):   paying agent side/role
             to (valid dict key):    recipient side/role
             delivery (dict (string, float)): delivery good type and amount"""
        """ over delivery is handled quietly """
        for good, amount in delivery.items():
            try:
                #me.destroy(good, amount)
                me.give(self.contract_partners[to][0], self.contract_partners[to][1], good, amount)
                self.obligations[von][good] = max(0, self.obligations[von][good] - amount)
            except NotEnoughGoods:
                ## cause agent to default
                raise
                #pass

    def terminate(self):
        """Method to set contract to terminated status. No arguments, returns None."""
        self.valid = False
        
    def is_valid(self):
        """Getter method on valid status of contract. No arguments. 
           Returns (boolean): whether the contract is still valid (not defaulted or terminated)"""
        return self.valid
        
    def get_endtime(self):
        """Getter methof dor contract end time. No arguments.
           Returns (int or float): contract end time"""
        return self.endtime
