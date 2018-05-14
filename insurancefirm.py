from metainsuranceorg import MetaInsuranceOrg
from catbond import CatBond
import numba as nb
import numpy as np
from reinsurancecontract import ReinsuranceContract

class InsuranceFirm(MetaInsuranceOrg):
    """ReinsuranceFirm class.
       Inherits from InsuranceFirm."""
    def init(self, simulation_parameters, agent_parameters):
        """Constructor method.
               Accepts arguments
                   Signature is identical to constructor method of parent class.
           Constructor calls parent constructor and only overwrites boolean indicators of insurer and reinsurer role of
           the object."""
        super(InsuranceFirm, self).init(simulation_parameters, agent_parameters)
        self.is_insurer = True
        self.is_reinsurer = False

    def adjust_dividends(self, time):
        #TODO: Implement algorithm from flowchart (capital target missing
        self.per_period_dividend = max(0, 0.005 * self.cash)
        if self.cash_last_periods[0] - self.cash_last_periods[1] < 0:     # no dividends if firm made losses
            self.per_period_dividend = 0
        #if :                                                   # no dividends if firm misses capital target
        #    self.per_period_dividend = 0
            

    def increase_capacity(self, time):
        '''This is implemented for non-proportional reinsurance only. Otherwise the price comparison is not meaningful. Assert non-proportional mode.'''
        assert self.simulation_reinsurance_type == 'non-proportional'
        '''get prices'''
        reinsurance_price = self.simulation.get_reinsurance_premium(self.np_reinsurance_deductible_fraction )
        cat_bond_price = self.simulation.get_cat_bond_price(self.np_reinsurance_deductible_fraction)
        '''on this basis decide for obtaining reinsurance or for issuing cat bond'''
        categ_ids = [ categ_id for categ_id in range(self.simulation_no_risk_categories) if (self.category_reinsurance[categ_id] is None)]
        if len(categ_ids) > 1:
            np.random.shuffle(categ_ids)
        while len(categ_ids) > 1:       # and ...
            categ_id = categ_ids.pop()
            print("IF {0:d} increasing capacity in period {1:d}, cat bond price: {2:f}, reinsurance premium {3:f}".format(self.id, time, cat_bond_price, reinsurance_price))
            if reinsurance_price > cat_bond_price:
                print("IF {0:d} issuing Cat bond in period {1:d}".format(self.id, time))
                self.issue_cat_bond(time, categ_id)
            else:
                print("IF {0:d} getting reinsurance in period {1:d}".format(self.id, time))
                self.ask_reinsurance_non_proportional_by_category(time, categ_id)
            if True:                    # just one per iteration, unless capital target is unmatched
                categ_ids = []
    
    def ask_reinsurance(self, time):
        if self.simulation_reinsurance_type == 'proportional':
            self.ask_reinsurance_proportional()
        elif self.simulation_reinsurance_type == 'non-proportional':
            self.ask_reinsurance_non_proportional(time)
        else:
            assert False, "Undefined reinsurance type"

    @nb.jit
    def ask_reinsurance_non_proportional(self, time):
        """ Method for requesting excess of loss reinsurance for all underwritten contracts by category.
            The method calculates the combined valur at risk. With a probability it then creates a combined 
            reinsurance risk that may then be underwritten by a reinsurance firm.
            Arguments: 
                time: integer
            Returns None.
            
        """
        """Evaluate by risk category"""
        for categ_id in range(self.simulation_no_risk_categories):
            """Seek reinsurance only with probability 10% if not already reinsured"""  # TODO: find a more generic way to decide whether to request reinsurance for category in this period
            if (self.category_reinsurance[categ_id] is None) and np.random.random() < 0.1:
                self.ask_reinsurance_non_proportional_by_category(time, categ_id)

    @nb.jit 
    def characterize_underwritten_risks_by_category(self, time, categ_id):
        total_value = 0
        avg_risk_factor = 0
        number_risks = 0
        periodized_total_premium = 0
        for contract in self.underwritten_contracts:
            if contract.category == categ_id:
                total_value += contract.value
                avg_risk_factor += contract.risk_factor
                number_risks += 1
                periodized_total_premium += contract.periodized_premium
        if number_risks > 0:    
            avg_risk_factor /= number_risks
        return total_value, avg_risk_factor, number_risks, periodized_total_premium


    @nb.jit
    def ask_reinsurance_non_proportional_by_category(self, time, categ_id):
        """Proceed with creation of reinsurance risk only if category is not empty."""
        total_value, avg_risk_factor, number_risks, periodized_total_premium = self.characterize_underwritten_risks_by_category(time, categ_id)
        if number_risks > 0:    
            risk = {"value": total_value, "category": categ_id, "owner": self,
                        #"identifier": uuid.uuid1(),
                        "insurancetype": 'excess-of-loss', "number_risks": number_risks, 
                        "deductible_fraction": self.np_reinsurance_deductible_fraction, 
                        "excess_fraction": self.np_reinsurance_excess_fraction,
                        "periodized_total_premium": periodized_total_premium, "runtime": 12,
                        "expiration": time + 12, "risk_factor": avg_risk_factor}    # TODO: make runtime into a parameter

            self.simulation.append_reinrisks(risk)

    @nb.jit
    def ask_reinsurance_proportional(self):
        nonreinsured = []
        for contract in self.underwritten_contracts:
            if contract.reincontract == None:
                nonreinsured.append(contract)

        #nonreinsured_b = [contract
        #                for contract in self.underwritten_contracts
        #                if contract.reincontract == None]
        #
        #try:
        #    assert nonreinsured == nonreinsured_b
        #except:
        #    pdb.set_trace()

        nonreinsured.reverse()

        if len(nonreinsured) >= (1 - self.reinsurance_limit) * len(self.underwritten_contracts):
            counter = 0
            limitrein = len(nonreinsured) - (1 - self.reinsurance_limit) * len(self.underwritten_contracts)
            for contract in nonreinsured:
                if counter < limitrein:
                    risk = {"value": contract.value, "category": contract.category, "owner": self,
                            #"identifier": uuid.uuid1(),
                            "reinsurance_share": 1.,
                            "expiration": contract.expiration, "contract": contract,
                            "risk_factor": contract.risk_factor}

                    #print("CREATING", risk["expiration"], contract.expiration, risk["contract"].expiration, risk["identifier"])
                    self.simulation.append_reinrisks(risk)
                    counter += 1
                else:
                    break

    def add_reinsurance(self, category, excess_fraction, deductible_fraction, contract):
        self.riskmodel.add_reinsurance(category, excess_fraction, deductible_fraction, contract)
        self.category_reinsurance[category] = contract
        #pass

    def delete_reinsurance(self, category, excess_fraction, deductible_fraction, contract):
        self.riskmodel.delete_reinsurance(category, excess_fraction, deductible_fraction, contract)
        self.category_reinsurance[category] = None
        #pass
    
    def issue_cat_bond(self, time, categ_id, per_value_per_period_premium = 0):
        # premium is for usual reinsurance contracts paid using per value market premium
        # for the quasi-contract for the cat bond, nothing is paid, everything is already paid at the beginning.
        #per_value_reinsurance_premium = self.np_reinsurance_premium_share * risk["periodized_total_premium"] * risk["runtime"] / risk["value"]            #TODO: rename this to per_value_premium in insurancecontract.py to avoid confusion
        """ create catbond """
        total_value, avg_risk_factor, number_risks, periodized_total_premium = self.characterize_underwritten_risks_by_category(time, categ_id)
        risk = {"value": total_value, "category": categ_id, "owner": self,
                        #"identifier": uuid.uuid1(),
                        "insurancetype": 'excess-of-loss', "number_risks": number_risks, 
                        "deductible_fraction": self.np_reinsurance_deductible_fraction, 
                        "excess_fraction": self.np_reinsurance_excess_fraction,
                        "periodized_total_premium": 0, "runtime": 12,
                        "expiration": time + 12, "risk_factor": avg_risk_factor}    # TODO: make runtime into a parameter
        _, var_this_risk = self.riskmodel.evaluate([], self.cash, risk)
        per_period_premium = per_value_per_period_premium * risk["value"]
        total_premium = sum([per_period_premium * ((1/(1+self.interest_rate))**i) for i in range(risk["runtime"])])                # TODO: or is it range(1, risk["runtime"]+1)?
        #catbond = CatBond(self.simulation, per_period_premium)
        catbond = CatBond(self.simulation, per_period_premium, self.interest_rate)  # TODO: shift obtain_yield method to insurancesimulation, thereby making it unnecessary to drag parameters like self.interest_rate from instance to instance and from class to class

        """add contract; contract is a quasi-reinsurance contract"""
        contract = ReinsuranceContract(catbond, risk, time, 0, risk["runtime"], \
                                                  self.default_contract_payment_period, \
                                                  expire_immediately=self.simulation_parameters["expire_immediately"], \
                                                  initial_VaR=var_this_risk, \
                                                  insurancetype=risk["insurancetype"])
        # per_value_reinsurance_premium = 0 because the insurance firm does not continue to make payments to the cat bond. Only once.
        
        catbond.set_contract(contract)
        """sell cat bond (to self.simulation)"""
        self.simulation.receive_obligation(var_this_risk, self, time)
        catbond.set_owner(self.simulation)
        """hand cash over to cat bond such that var_this_risk is covered"""
        self.pay(var_this_risk + total_premium, catbond)    #TODO: is var_this_risk the correct amount?
        """register catbond"""
        self.simulation.accept_agents("catbond", [catbond], time=time)

    def make_reinsurance_claims(self,time):
        """collect and effect reinsurance claims"""
        # TODO: reorganize this with risk category ledgers
        # TODO: Put facultative insurance claims here
        claims_this_turn = np.zeros(self.simulation_no_risk_categories)
        for contract in self.underwritten_contracts:
            categ_id, claims, is_proportional = contract.get_and_reset_current_claim()
            if is_proportional:
                claims_this_turn[categ_id] += claims
            if (contract.reincontract != None):
                contract.reincontract.explode(time, claims)

        for categ_id in range(self.simulation_no_risk_categories):
            if claims_this_turn[categ_id] > 0 and self.category_reinsurance[categ_id] is not None:
                self.category_reinsurance[categ_id].explode(time, claims_this_turn[categ_id])
