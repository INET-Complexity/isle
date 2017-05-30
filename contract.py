"""
Created by Davoud Taghawi-Nejad
"""
from abce import NotEnoughGoods
from collections import defaultdict


class Contract:
    def __init__(self, contract_partners, endtime = None):
        self.contract_partners = contract_partners
        self.obliations = {}
        self.endtime = endtime
        self.valid = True 


    @staticmethod
    def generated(contract_dict):
        contract = Contract(None)
        for key in contract_dict:
            contract.__dict__[key] = contract_dict[key]
        return contract

    def get_obligations(self, side):
        try:
            return self.obliations[side]
        except KeyError:
            return {}

    def get_obligation(self, side, good):
        try:
            return self.obliations[side][good]
        except KeyError:
            return 0.0

    def add_obligation(self, side, good, amount):
        self.obliations[side][good] += amount

    def substract_obligation(self, side, good, amount):
        """ no negative obligations, quietly """
        self.obliations[side][good] = min(0, self.obliations[side][good] - amount)

    def fulfill_obligation(self, me, von, to, delivery):
        """ over delivery is handled quietly """
        for good, amount in delivery.items():
            try:
                me.destroy(good, amount)
                me.give(self.contract_partners[to][0], self.contract_partners[to][1], good, amount)
                self.obliations[von][good] = max(0, self.obliations[von][good] - amount)
            except NotEnoughGoods:
                raise

    def terminate(self):
        self.valid = False
        
    def is_valid(self):
        return self.valid
        
    def get_endtime(self):
        return self.endtime
