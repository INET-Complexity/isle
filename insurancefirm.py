from metainsuranceorg import MetaInsuranceOrg
from catbond import CatBond
import numba as nb
import numpy as np
from reinsurancecontract import ReinsuranceContract
import isleconfig

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

    def adjust_dividends(self, time, actual_capacity):
        #TODO: Implement algorithm from flowchart
        profits = self.get_profitslosses()
        self.per_period_dividend = max(0, self.dividend_share_of_profits * profits) # max function ensures that no negative dividends are paid
        #if profits < 0:                                                             # no dividends when losses are written
        #    self.per_period_dividend = 0
        if actual_capacity < self.capacity_target:                                  # no dividends if firm misses capital target
            self.per_period_dividend = 0
        
    def get_profitslosses(self):
        return self.cash_last_periods[0] - self.cash_last_periods[1]
    
    #@nb.jit    
    def get_reinsurance_VaR_estimate(self, max_var):
        reinsurance_factor_estimate = (sum([ 1 for categ_id in range(self.simulation_no_risk_categories) \
                                if (self.category_reinsurance[categ_id] is None)]) \
                                        * 1. / self.simulation_no_risk_categories) \
                                        * (1. - self.np_reinsurance_deductible_fraction)
        reinsurance_VaR_estimate = max_var * (1. + reinsurance_factor_estimate)
        return reinsurance_VaR_estimate
    
    def adjust_capacity_target(self, max_var):
        reinsurance_VaR_estimate = self.get_reinsurance_VaR_estimate(max_var)
        capacity_target_var_ratio_estimate = (self.capacity_target + reinsurance_VaR_estimate) * 1. / (max_var + reinsurance_VaR_estimate)
        if capacity_target_var_ratio_estimate > self.capacity_target_increment_threshold:
            self.capacity_target *= self.capacity_target_increment_factor
        elif capacity_target_var_ratio_estimate < self.capacity_target_decrement_threshold:
            self.capacity_target *= self.capacity_target_decrement_factor
        return 

    def get_capacity(self, max_var):
        if max_var < self.cash:     # ensure presence of sufficiently much cash to cover VaR
            reinsurance_VaR_estimate = self.get_reinsurance_VaR_estimate(max_var)
            return self.cash + reinsurance_VaR_estimate
        # else: # (This point is only reached when insurer is in severe financial difficulty. Ensure insurer recovers complete coverage.)
        return self.cash
        
    def increase_capacity(self, time, max_var):
        '''This is implemented for non-proportional reinsurance only. Otherwise the price comparison is not meaningful. Assert non-proportional mode.'''
        assert self.simulation_reinsurance_type == 'non-proportional'
        '''get prices'''
        reinsurance_price = self.simulation.get_reinsurance_premium(self.np_reinsurance_deductible_fraction)
        cat_bond_price = self.simulation.get_cat_bond_price(self.np_reinsurance_deductible_fraction)
        capacity = None
        if not reinsurance_price == cat_bond_price == float('inf'):
            categ_ids = [ categ_id for categ_id in range(self.simulation_no_risk_categories) if (self.category_reinsurance[categ_id] is None)]
            if len(categ_ids) > 1:
                np.random.shuffle(categ_ids)
            while len(categ_ids) >= 1:       
                categ_id = categ_ids.pop()
                capacity = self.get_capacity(max_var)
                if self.capacity_target < capacity: # just one per iteration, unless capital target is unmatched
                    if self.increase_capacity_by_category(time, categ_id, reinsurance_price=reinsurance_price, cat_bond_price=cat_bond_price, force=False):
                        categ_ids = []
                else:
                    self.increase_capacity_by_category(time, categ_id, reinsurance_price=reinsurance_price, cat_bond_price=cat_bond_price, force=True)
        # capacity is returned in order not to recompute more often than necessary
        if capacity is None: 
            capacity = self.get_capacity(max_var)
        return capacity 

    def increase_capacity_by_category(self, time, categ_id, reinsurance_price, cat_bond_price, force=False):
        if isleconfig.verbose:
            print("IF {0:d} increasing capacity in period {1:d}, cat bond price: {2:f}, reinsurance premium {3:f}".format(self.id, time, cat_bond_price, reinsurance_price))
        if not force:
            actual_premium = self.get_average_premium(categ_id)
            possible_premium = self.simulation.get_market_premium()
            if actual_premium >= possible_premium:
                return False
        '''on the basis of prices decide for obtaining reinsurance or for issuing cat bond'''
        if reinsurance_price > cat_bond_price:
            if isleconfig.verbose:
                print("IF {0:d} issuing Cat bond in period {1:d}".format(self.id, time))
            self.issue_cat_bond(time, categ_id)
        else:
            if isleconfig.verbose:
                print("IF {0:d} getting reinsurance in period {1:d}".format(self.id, time))
            self.ask_reinsurance_non_proportional_by_category(time, categ_id)
        return True
    
    @nb.jit
    def get_average_premium(self, categ_id):
        weighted_premium_sum = 0
        total_weight = 0
        for contract in self.underwritten_contracts:
            if contract.category == categ_id:
                total_weight += contract.value
                contract_premium = contract.periodized_premium * contract.runtime
                weighted_premium_sum += contract_premium
        if total_weight == 0:
            return 0    # will prevent any attempt to reinsure empty categories
        return weighted_premium_sum * 1.0 / total_weight
    
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
            if (self.category_reinsurance[categ_id] is None):
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
        if number_risks > 0:
            risk = {"value": total_value, "category": categ_id, "owner": self,
                            #"identifier": uuid.uuid1(),
                            "insurancetype": 'excess-of-loss', "number_risks": number_risks, 
                            "deductible_fraction": self.np_reinsurance_deductible_fraction, 
                            "excess_fraction": self.np_reinsurance_excess_fraction,
                            "periodized_total_premium": 0, "runtime": 12,
                            "expiration": time + 12, "risk_factor": avg_risk_factor}    # TODO: make runtime into a parameter
            _, var_this_risk, _ = self.riskmodel.evaluate([], self.cash, risk)
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

    def get_excess_of_loss_reinsurance(self):
        reinsurance = []
        for categ_id in range(self.simulation_no_risk_categories):
            if self.category_reinsurance[categ_id] is not None:
               reinsurance_contract = {}
               reinsurance_contract["reinsurer"] = self.category_reinsurance[categ_id].insurer
               reinsurance_contract["value"] = self.category_reinsurance[categ_id].value
               reinsurance_contract["category"] = categ_id
               reinsurance.append(reinsurance_contract)
        return reinsurance
