
import isleconfig
import numpy as np
import scipy.stats
from insurancecontract import InsuranceContract
from reinsurancecontract import ReinsuranceContract
from riskmodel import RiskModel
import sys, pdb
import uuid
import numba as nb

if isleconfig.use_abce:
    from genericagentabce import GenericAgent
    #print("abce imported")
else:
    from genericagent import GenericAgent
    #print("abce not imported")

class MetaInsuranceOrg(GenericAgent):
    def init(self, simulation_parameters, agent_parameters):
        self.simulation = simulation_parameters['simulation']
        self.simulation_parameters = simulation_parameters
        self.contract_runtime_dist = scipy.stats.randint(simulation_parameters["mean_contract_runtime"] - \
                  simulation_parameters["contract_runtime_halfspread"], simulation_parameters["mean_contract_runtime"] \
                  + simulation_parameters["contract_runtime_halfspread"] + 1)
        self.default_contract_payment_period = simulation_parameters["default_contract_payment_period"]
        self.id = agent_parameters['id']
        self.cash = agent_parameters['initial_cash']
        self.capacity_target = self.cash * 0.9
        self.capacity_target_decrement_threshold = agent_parameters['capacity_target_decrement_threshold']
        self.capacity_target_increment_threshold = agent_parameters['capacity_target_increment_threshold']
        self.capacity_target_decrement_factor = agent_parameters['capacity_target_decrement_factor']
        self.capacity_target_increment_factor = agent_parameters['capacity_target_increment_factor']
        self.excess_capital = self.cash
        self.premium = agent_parameters["norm_premium"]
        self.profit_target = agent_parameters['profit_target']
        self.acceptance_threshold = agent_parameters['initial_acceptance_threshold']  # 0.5
        self.acceptance_threshold_friction = agent_parameters['acceptance_threshold_friction']  # 0.9 #1.0 to switch off
        self.interest_rate = agent_parameters["interest_rate"]
        self.reinsurance_limit = agent_parameters["reinsurance_limit"]
        self.simulation_no_risk_categories = simulation_parameters["no_categories"]
        self.simulation_reinsurance_type = simulation_parameters["simulation_reinsurance_type"]
        self.dividend_share_of_profits = simulation_parameters["dividend_share_of_profits"]
        
        self.owner = self.simulation # TODO: Make this into agent_parameter value?
        self.per_period_dividend = 0
        self.cash_last_periods = list(np.zeros(4, dtype=int)*self.cash)
        
        rm_config = agent_parameters['riskmodel_config']
        self.riskmodel = RiskModel(damage_distribution=rm_config["damage_distribution"], \
                                     expire_immediately=rm_config["expire_immediately"], \
                                     cat_separation_distribution=rm_config["cat_separation_distribution"], \
                                     norm_premium=rm_config["norm_premium"], \
                                     category_number=rm_config["no_categories"], \
                                     init_average_exposure=rm_config["risk_value_mean"], \
                                     init_average_risk_factor=rm_config["risk_factor_mean"], \
                                     init_profit_estimate=rm_config["norm_profit_markup"], \
                                     margin_of_safety=rm_config["margin_of_safety"], \
                                     var_tail_prob=rm_config["var_tail_prob"], \
                                     inaccuracy=rm_config["inaccuracy_by_categ"])
        
        self.category_reinsurance = [None for i in range(self.simulation_no_risk_categories)]
        if self.simulation_reinsurance_type == 'non-proportional':
            if agent_parameters['non-proportional_reinsurance_level'] is not None:
                self.np_reinsurance_deductible_fraction = agent_parameters['non-proportional_reinsurance_level']
            else:
                self.np_reinsurance_deductible_fraction = simulation_parameters["default_non-proportional_reinsurance_deductible"]
            self.np_reinsurance_excess_fraction = simulation_parameters["default_non-proportional_reinsurance_excess"]
            self.np_reinsurance_premium_share = simulation_parameters["default_non-proportional_reinsurance_premium_share"]
        self.obligations = []
        self.underwritten_contracts = []
        #self.reinsurance_contracts = []
        self.operational = True
        self.is_insurer = True
        self.is_reinsurer = False
        
        """set up risk value estimate variables"""
        self.var_counter = 0                # sum over risk model inaccuracies for all contracts
        self.var_counter_per_risk = 0       # average risk model inaccuracy across contracts
        self.var_sum = 0                    # sum over initial VaR for all contracts
        self.counter_category = np.zeros(self.simulation_no_risk_categories)    # var_counter disaggregated by category
        self.var_category = np.zeros(self.simulation_no_risk_categories)        # var_sum disaggregated by category

    def iterate(self, time):        # TODO: split function so that only the sequence of events remains here and everything else is in separate methods
        """obtain investments yield"""
        self.obtain_yield(time)

        """realize due payments"""
        self.effect_payments(time)
        if isleconfig.verbose:
            print(time, ":", self.id, len(self.underwritten_contracts), self.cash, self.operational)

        self.make_reinsurance_claims(time)

        """mature contracts"""
        if isleconfig.verbose:
            print("Number of underwritten contracts ", len(self.underwritten_contracts))
        maturing = [contract for contract in self.underwritten_contracts if contract.expiration <= time]
        for contract in maturing:
            self.underwritten_contracts.remove(contract)
            contract.mature(time)
        contracts_dissolved = len(maturing)

        """effect payments from contracts"""
        [contract.check_payment_due(time) for contract in self.underwritten_contracts]

        if self.operational:

            """request risks to be considered for underwriting in the next period and collect those for this period"""
            new_risks = []
            if self.is_insurer:
                new_risks += self.simulation.solicit_insurance_requests(self.id, self.cash)
            if self.is_reinsurer:
                new_risks += self.simulation.solicit_reinsurance_requests(self.id, self.cash)
            contracts_offered = len(new_risks)
            if isleconfig.verbose and contracts_offered < 2 * contracts_dissolved:
                print("Something wrong; agent {0:d} receives too few new contracts {1:d} <= {2:d}".format(
                                                                self.id, contracts_offered, 2*contracts_dissolved))
            
            new_nonproportional_risks = [risk for risk in new_risks if risk.get("insurancetype")=='excess-of-loss' and risk["owner"] is not self]
            new_risks = [risk for risk in new_risks if risk.get("insurancetype") in ['proportional', None] and risk["owner"] is not self]

            underwritten_risks = [{"value": contract.value, "category": contract.category, \
                            "risk_factor": contract.risk_factor, "deductible": contract.deductible, \
                            "excess": contract.excess, "insurancetype": contract.insurancetype, \
                            "runtime": contract.runtime} for contract in self.underwritten_contracts if contract.reinsurance_share != 1.0]
            
            """deal with non-proportional risks first as they must evaluate each request separatly, then with proportional ones"""
            for risk in new_nonproportional_risks:
                accept, var_this_risk, self.excess_capital = self.riskmodel.evaluate(underwritten_risks, self.cash, risk)       # TODO: change riskmodel.evaluate() to accept new risk to be evaluated and to account for existing non-proportional risks correctly -> DONE.
                if accept:
                    per_value_reinsurance_premium = self.np_reinsurance_premium_share * risk["periodized_total_premium"] * risk["runtime"] / risk["value"]            #TODO: rename this to per_value_premium in insurancecontract.py to avoid confusion
                    contract = ReinsuranceContract(self, risk, time, per_value_reinsurance_premium, risk["runtime"], \
                                                  self.default_contract_payment_period, \
                                                  expire_immediately=self.simulation_parameters["expire_immediately"], \
                                                  initial_VaR=var_this_risk, \
                                                  insurancetype=risk["insurancetype"])        # TODO: implement excess of loss for reinsurance contracts
                    self.underwritten_contracts.append(contract)
                #pass    # TODO: write this nonproportional risk acceptance decision section based on commented code in the lines above this -> DONE.
            
            """obtain risk model evaluation (VaR) for underwriting decisions and for capacity specific decisions"""
            # TODO: Enable reinsurance shares other tan 0.0 and 1.0
            expected_profit, acceptable_by_category, var_per_risk_per_categ, self.excess_capital = self.riskmodel.evaluate(underwritten_risks, self.cash)
            
            # TODO: resolve insurance reinsurance inconsistency (insurer underwrite after capacity decisions, reinsurers before). 
            #                        This is currently so because it minimizes the number of times we need to run self.riskmodel.evaluate().
            #                        It would also be more consistent if excess capital would be updated at the end of the iteration.
            """handle adjusting capacity target and capacity"""
            max_var_by_categ = self.cash - self.excess_capital
            self.adjust_capacity_target(max_var_by_categ)
            actual_capacity = self.increase_capacity(time, max_var_by_categ)
            # seek reinsurance
            #if self.is_insurer:
            #    # TODO: Why should only insurers be able to get reinsurance (not reinsurers)? (Technically, it should work) --> OBSOLETE
            #    self.ask_reinsurance(time)
            #    # TODO: make independent of insurer/reinsurer, but change this to different deductable values
            """handle capital market interactions: capital history, dividends"""
            self.cash_last_periods = [self.cash] + self.cash_last_periods[:3]
            self.adjust_dividends(time, actual_capacity)
            self.pay_dividends(time)

            """make underwriting decisions, category-wise"""
            #if expected_profit * 1./self.cash < self.profit_target:
            #    self.acceptance_threshold = ((self.acceptance_threshold - .4) * 5. * self.acceptance_threshold_friction) / 5. + .4
            #else:
            #    self.acceptance_threshold = (1 - self.acceptance_threshold_friction * (1 - (self.acceptance_threshold - .4) * 5.)) / 5. + .4

            growth_limit = max(50, 2 * len(self.underwritten_contracts) + contracts_dissolved)
            if sum(acceptable_by_category) > growth_limit:
                acceptable_by_category = np.asarray(acceptable_by_category).astype(np.double)
                acceptable_by_category = acceptable_by_category * growth_limit / sum(acceptable_by_category)
                acceptable_by_category = np.int64(np.round(acceptable_by_category))

            not_accepted_risks = []
            for categ_id in range(len(acceptable_by_category)):
                categ_risks = [risk for risk in new_risks if risk["category"] == categ_id]
                new_risks = [risk for risk in new_risks if risk["category"] != categ_id]
                categ_risks = sorted(categ_risks, key = lambda risk: risk["risk_factor"])
                i = 0
                if isleconfig.verbose:
                    print("InsuranceFirm underwrote: ", len(self.underwritten_contracts), " will accept: ", acceptable_by_category[categ_id], " out of ", len(categ_risks), "acceptance threshold: ", self.acceptance_threshold)
                while (acceptable_by_category[categ_id] > 0 and len(categ_risks) > i): #\
                    #and categ_risks[i]["risk_factor"] < self.acceptance_threshold):
                    if categ_risks[i].get("contract") is not None: #categ_risks[i]["reinsurance"]:
                        if categ_risks[i]["contract"].expiration > time:    # required to rule out contracts that have exploded in the meantime
                            #print("ACCEPTING", categ_risks[i]["contract"].expiration, categ_risks[i]["expiration"], categ_risks[i]["identifier"], categ_risks[i].get("contract").terminating)
                            contract = ReinsuranceContract(self, categ_risks[i], time, \
                                          self.simulation.get_market_premium(), categ_risks[i]["expiration"] - time, \
                                          self.default_contract_payment_period, \
                                          expire_immediately=self.simulation_parameters["expire_immediately"], )  
                            self.underwritten_contracts.append(contract)
                            #categ_risks[i]["contract"].reincontract = contract
                            # TODO: move this to insurancecontract (ca. line 14) -> DONE
                            # TODO: do not write into other object's properties, use setter -> DONE

                            assert categ_risks[i]["contract"].expiration >= contract.expiration, "Reinsurancecontract lasts longer than insurancecontract: {0:d}>{1:d} (EXPIRATION2: {2:d} Time: {3:d})".format(contract.expiration, categ_risks[i]["contract"].expiration, categ_risks[i]["expiration"], time)
                        #else:
                        #    pass
                    else:
                        contract = InsuranceContract(self, categ_risks[i], time, self.simulation.get_market_premium(), \
                                                     self.contract_runtime_dist.rvs(), \
                                                     self.default_contract_payment_period, \
                                                     expire_immediately=self.simulation_parameters["expire_immediately"], \
                                                     initial_VaR = var_per_risk_per_categ[categ_id])
                        self.underwritten_contracts.append(contract)
                    acceptable_by_category[categ_id] -= 1   # TODO: allow different values per risk (i.e. sum over value (and reinsurance_share) or exposure instead of counting)
                    i += 1

                not_accepted_risks += categ_risks[i:]
                not_accepted_risks = [risk for risk in not_accepted_risks if risk.get("contract") is None]

            # return unacceptables
            #print(self.id, " now has ", len(self.underwritten_contracts), " & returns ", len(not_accepted_risks))
            self.simulation.return_risks(not_accepted_risks)

            #not implemented
            #"""adjust liquidity, borrow or invest"""
            #pass
            
        self.estimated_var()

    def enter_illiquidity(self, time):
        self.enter_bankruptcy(time)

    def enter_bankruptcy(self, time):
        [contract.dissolve(time) for contract in self.underwritten_contracts]   # removing (dissolving) all risks immediately after bankruptcy (may not be realistic, they might instead be bought by another company)
        self.simulation.receive(self.cash)
        self.cash = 0
        self.operational = False
        self.simulation.record_bankruptcy()

    def receive_obligation(self, amount, recipient, due_time):
        obligation = {"amount": amount, "recipient": recipient, "due_time": due_time}
        self.obligations.append(obligation)

    def effect_payments(self, time):
        due = [item for item in self.obligations if item["due_time"]<=time]
        self.obligations = [item for item in self.obligations if item["due_time"]>time]
        sum_due = sum([item["amount"] for item in due])
        if sum_due > self.cash:
            self.obligations += due
            self.enter_illiquidity(time)
            self.simulation.record_unrecovered_claims(sum_due - self.cash)
            # TODO: is this record of uncovered claims correct or should it be sum_due (since the company is impounded and self.cash will also not be paid out for quite some time)?
            # TODO: effect partial payment
        else:
            for obligation in due:
                self.pay(obligation["amount"], obligation["recipient"])


    def pay(self, amount, recipient):
        if self.get_operational() and recipient.get_operational():
            self.cash -= amount
            recipient.receive(amount)

    def receive(self, amount):
        """Method to accept cash payments."""
        self.cash += amount

    def pay_dividends(self, time):
        self.receive_obligation(self.per_period_dividend, self.owner, time)
    
    def obtain_yield(self, time):
        amount = self.cash * self.interest_rate             # TODO: agent should not award her own interest. This interest rate should be taken from self.simulation with a getter method
        self.simulation.receive_obligation(amount, self, time)
    
    def increase_capacity(self):
        raise AttributeError( "Method is not implemented in MetaInsuranceOrg, just in inheriting InsuranceFirm instances" )
        
    def get_cash(self):
        return self.cash

    def get_excess_capital(self):
        return self.excess_capital

    def logme(self):
        self.log('cash', self.cash)
        self.log('underwritten_contracts', self.underwritten_contracts)
        self.log('operational', self.operational)

    #def zeros(self):
    #    return 0

    def len_underwritten_contracts(self):
        return len(self.underwritten_contracts)

    def get_operational(self):
        return self.operational

    def get_underwritten_contracts(self):
        return self.underwritten_contracts
    
    def get_pointer(self):
        return self

    def estimated_var(self):

        self.counter_category = np.zeros(self.simulation_no_risk_categories)
        self.var_category = np.zeros(self.simulation_no_risk_categories)

        self.var_counter = 0
        self.var_counter_per_risk = 0
        self.var_sum = 0
        
        if self.operational:

            for contract in self.underwritten_contracts:
                self.counter_category[contract.category] = self.counter_category[contract.category] + 1
                self.var_category[contract.category] = self.var_category[contract.category] + contract.initial_VaR

            for category in range(len(self.counter_category)):
                self.var_counter = self.var_counter + self.counter_category[category] * self.riskmodel.inaccuracy[category]
                self.var_sum = self.var_sum + self.var_category[category]

            if not sum(self.counter_category) == 0:
                self.var_counter_per_risk = self.var_counter / sum(self.counter_category)
            else:
                self.var_counter_per_risk = 0

    def increase_capacity(self, time):
        assert False, "Method not implemented. increase_capacity method should be implemented in inheriting classes"

    def adjust_dividend(self, time):
        assert False, "Method not implemented. adjust_dividend method should be implemented in inheriting classes"
        
    def adjust_capacity_target(self, time):
        assert False, "Method not implemented. adjust_dividend method should be implemented in inheriting classes"
            
