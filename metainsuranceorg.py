
import isleconfig
import numpy as np
import scipy.stats
import copy
from insurancecontract import InsuranceContract
from reinsurancecontract import ReinsuranceContract
from riskmodel import RiskModel
import sys, pdb
import uuid

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
        self.profits_losses = 0
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
        self.naccep = []
        self.risks_kept = []
        self.reinrisks_kept = []
        self.balance_ratio = simulation_parameters['insurers_balance_ratio']
        self.recursion_limit = simulation_parameters['insurers_recursion_limit']
        self.cash_left_by_categ = [self.cash for i in range(self.simulation_parameters["no_categories"])]
        self.market_permanency_counter = 0

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
                new_risks += self.simulation.solicit_insurance_requests(self.id, self.cash, self)
            if self.is_reinsurer:
                new_risks += self.simulation.solicit_reinsurance_requests(self.id, self.cash, self)
            contracts_offered = len(new_risks)
            if isleconfig.verbose and contracts_offered < 2 * contracts_dissolved:
                print("Something wrong; agent {0:d} receives too few new contracts {1:d} <= {2:d}".format(
                                                                self.id, contracts_offered, 2*contracts_dissolved))
            
            new_nonproportional_risks = [risk for risk in new_risks if risk.get("insurancetype")=='excess-of-loss' and risk["owner"] is not self]
            new_risks = [risk for risk in new_risks if risk.get("insurancetype") in ['proportional', None] and risk["owner"] is not self]
            
            """deal with non-proportional risks first as they must evaluate each request separatly, then with proportional ones"""

            [reinrisks_per_categ, number_reinrisks_categ] = self.risks_reinrisks_organizer(new_nonproportional_risks)  #Here the new reinrisks are organized by category.

            for repetition in range(self.recursion_limit):     # TODO: find an efficient way to stop the recursion if there are no more risks to accept or if it is not accepting any more over several iterations.
                former_reinrisks_per_categ = copy.copy(reinrisks_per_categ)
                [reinrisks_per_categ, not_accepted_reinrisks] = self.process_newrisks_reinsurer(reinrisks_per_categ, number_reinrisks_categ, time)  #Here we process all the new reinrisks in order to keep the portfolio as balanced as possible.
                if former_reinrisks_per_categ == reinrisks_per_categ:   #Stop condition implemented. Might solve the previous TODO.
                    break

            self.simulation.return_reinrisks(not_accepted_reinrisks)

            underwritten_risks = [{"value": contract.value, "category": contract.category, \
                                   "risk_factor": contract.risk_factor, "deductible": contract.deductible, \
                                   "excess": contract.excess, "insurancetype": contract.insurancetype, \
                                   "runtime": contract.runtime} for contract in self.underwritten_contracts if
                                  contract.reinsurance_share != 1.0]

            """obtain risk model evaluation (VaR) for underwriting decisions and for capacity specific decisions"""
            # TODO: Enable reinsurance shares other tan 0.0 and 1.0
            expected_profit, acceptable_by_category, cash_left_by_categ, var_per_risk_per_categ, self.excess_capital = self.riskmodel.evaluate(underwritten_risks, self.cash)
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

            [risks_per_categ, number_risks_categ] = self.risks_reinrisks_organizer(new_risks)  #Here the new risks are organized by category.

            for repetition in range(self.recursion_limit):   # TODO: find an efficient way to stop the recursion if there are no more risks to accept or if it is not accepting any more over several iterations.
                former_risks_per_categ = copy.copy(risks_per_categ)
                [risks_per_categ, not_accepted_risks] = self.process_newrisks_insurer(risks_per_categ, number_risks_categ, acceptable_by_category,
                                         var_per_risk_per_categ, cash_left_by_categ, time) #Here we process all the new risks in order to keep the portfolio as balanced as possible.
                if former_risks_per_categ == risks_per_categ:   #Stop condition implemented. Might solve the previous TODO.
                    break

            # return unacceptables
            #print(self.id, " now has ", len(self.underwritten_contracts), " & returns ", len(not_accepted_risks))
            self.simulation.return_risks(not_accepted_risks)

            #not implemented
            #"""adjust liquidity, borrow or invest"""
            #pass

        self.market_permanency(time)
            
        self.estimated_var()

    def enter_illiquidity(self, time):
        self.enter_bankruptcy(time)

    def enter_bankruptcy(self, time):
        [contract.dissolve(time) for contract in self.underwritten_contracts]   # removing (dissolving) all risks immediately after bankruptcy (may not be realistic, they might instead be bought by another company)
        self.simulation.return_risks(self.risks_kept)
        self.risks_kept = []
        self.reinrisks_kept = []
        self.simulation.receive(self.cash)
        self.cash = 0                           #Cash is 0 after bankruptcy.
        self.excess_capital = 0                 #Excess of capital is 0 after bankruptcy.
        self.profits_losses = 0                 #Profits and losses are 0 after bankruptcy.
        if self.operational:
            self.simulation.record_bankruptcy()
        self.operational = False


    def market_exit(self, time):
        [contract.dissolve(time) for contract in self.underwritten_contracts]   # removing (dissolving) all risks immediately after market exit (may not be realistic, they might instead be bought by another company)
        self.simulation.return_risks(self.risks_kept)
        self.risks_kept = []
        self.reinrisks_kept = []
        due = [item for item in self.obligations]
        for obligation in due:
            self.pay(obligation)
        self.simulation.receive(self.cash)
        self.cash = 0                           #Cash is 0 after bankruptcy.
        self.excess_capital = 0                 #Excess of capital is 0 after bankruptcy.
        self.profits_losses = 0                 #Profits and losses are 0 after bankruptcy.
        if self.operational:
            self.simulation.record_market_exit()
        self.operational = False


    def receive_obligation(self, amount, recipient, due_time, purpose):
        obligation = {"amount": amount, "recipient": recipient, "due_time": due_time, "purpose": purpose}
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
                self.pay(obligation)


    def pay(self, obligation):
        amount = obligation["amount"]
        recipient = obligation["recipient"]
        purpose = obligation["purpose"]
        if self.get_operational() and recipient.get_operational():
            self.cash -= amount
            if purpose is not 'dividend':
                self.profits_losses -= amount
            recipient.receive(amount)

    def receive(self, amount):
        """Method to accept cash payments."""
        self.cash += amount
        self.profits_losses += amount

    def pay_dividends(self, time):
        self.receive_obligation(self.per_period_dividend, self.owner, time, 'dividend')
    
    def obtain_yield(self, time):
        amount = self.cash * self.interest_rate             # TODO: agent should not award her own interest. This interest rate should be taken from self.simulation with a getter method
        self.simulation.receive_obligation(amount, self, time, 'yields')
    
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

    def get_profitslosses(self):
        return self.profits_losses

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

    def risks_reinrisks_organizer(self, new_risks):  #This method organizes the new risks received by the insurer (or reinsurer)

        risks_per_categ = [[] for x in range(self.simulation_parameters["no_categories"])]      #This method organizes the new risks received by the insurer (or reinsurer) by category in the nested list "risks_per_categ".
        number_risks_categ = [[] for x in range(self.simulation_parameters["no_categories"])]   #This method also counts the new risks received by the insurer (or reinsurer) by category in the list "number_risks_categ".

        for categ_id in range(self.simulation_parameters["no_categories"]):
            risks_per_categ[categ_id] = [risk for risk in new_risks if risk["category"] == categ_id]
            number_risks_categ[categ_id] = len(risks_per_categ[categ_id])

        return risks_per_categ, number_risks_categ   #The method returns both risks_per_categ and risks_per_categ.

    def balanced_portfolio(self, risk, cash_left_by_categ, var_per_risk): #This method decides whether the portfolio is balanced enough to accept a new risk or not. If it is balanced enough return True otherwise False.
                                                                          #This method also returns the cash available per category independently the risk is accepted or not.
        cash_reserved_by_categ = np.zeros(self.simulation_parameters["no_categories"])

        for i in range(len(cash_left_by_categ)):
            cash_reserved_by_categ[i] = self.cash - cash_left_by_categ[i]     #Here it is computed the cash already reserved by category

        std_pre = cash_reserved_by_categ.std()                                #Here it is computed the standard deviation of the cash reserved by category

        cash_reserved_by_categ_store = np.copy(cash_reserved_by_categ)

        if risk.get("insurancetype")=='excess-of-loss':
            percentage_value_at_risk = self.riskmodel.getPPF(categ_id=risk["category"], tailSize=self.riskmodel.var_tail_prob)
            expected_damage = percentage_value_at_risk * risk["value"] * risk["risk_factor"] \
                              * self.riskmodel.inaccuracy[risk["category"]]
            expected_claim = min(expected_damage, risk["value"] * risk["excess_fraction"]) - risk["value"] * risk["deductible_fraction"]

            # record liquidity requirement and apply margin of safety for liquidity requirement

            cash_reserved_by_categ_store[risk["category"]] += expected_claim * self.riskmodel.margin_of_safety  #Here it is computed how the cash reserved by category would change if the new reinsurance risk was accepted

        else:
            cash_reserved_by_categ_store[risk["category"]] += var_per_risk[risk["category"]] #Here it is computed how the cash reserved by category would change if the new insurance risk was accepted

        mean = cash_reserved_by_categ_store.mean()     #Here it is computed the mean of the cash reserved by category after the new risk of reinrisk is accepted
        std_post = cash_reserved_by_categ_store.std()  #Here it is computed the standard deviation of the cash reserved by category after the new risk of reinrisk is accepted

        total_cash_reserved_by_categ_post = sum(cash_reserved_by_categ_store)

        if (std_post * total_cash_reserved_by_categ_post/self.cash) <= (self.balance_ratio * mean) or std_post < std_pre:      #The new risk is accepted is the standard deviation is reduced or the cash reserved by category is very well balanced. (std_post) <= (self.balance_ratio * mean)
            for i in range(len(cash_left_by_categ)):                                                                           #The balance condition is not taken into account if the cash reserve is far away from the limit. (total_cash_employed_by_categ_post/self.cash <<< 1)
                cash_left_by_categ[i] = self.cash - cash_reserved_by_categ_store[i]

            return True, cash_left_by_categ
        else:
            for i in range(len(cash_left_by_categ)):
                cash_left_by_categ[i] = self.cash - cash_reserved_by_categ[i]

            return False, cash_left_by_categ

    def process_newrisks_reinsurer(self, reinrisks_per_categ, number_reinrisks_categ, time): #This method processes one by one the reinrisks contained in reinrisks_per_categ in order to decide whether they should be underwritten or not.
                                                                                             #It is done in this way to maintain the portfolio as balanced as possible. For that reason we process risk[C1], risk[C2], risk[C3], risk[C4], risk[C1], risk[C2], ... and so forth.
        for iterion in range(max(number_reinrisks_categ)):
            for categ_id in range(self.simulation_parameters["no_categories"]):   #Here we take only one risk per category at a time to achieve risk[C1], risk[C2], risk[C3], risk[C4], risk[C1], risk[C2], ... if possible.
                if iterion < number_reinrisks_categ[categ_id] and reinrisks_per_categ[categ_id][iterion] is not None:
                    risk_to_insure = reinrisks_per_categ[categ_id][iterion]
                    underwritten_risks = [{"value": contract.value, "category": contract.category, \
                                           "risk_factor": contract.risk_factor,
                                           "deductible": contract.deductible, \
                                           "excess": contract.excess, "insurancetype": contract.insurancetype, \
                                           "runtime_left": (contract.expiration - time)} for contract in
                                          self.underwritten_contracts if contract.insurancetype == "excess-of-loss"]
                    accept, cash_left_by_categ, var_this_risk, self.excess_capital = self.riskmodel.evaluate(
                        underwritten_risks, self.cash,
                        risk_to_insure)  # TODO: change riskmodel.evaluate() to accept new risk to be evaluated and to account for existing non-proportional risks correctly -> DONE.
                    if accept:
                        per_value_reinsurance_premium = self.np_reinsurance_premium_share * risk_to_insure[
                            "periodized_total_premium"] * risk_to_insure["runtime"] / risk_to_insure[
                                                            "value"]  # TODO: rename this to per_value_premium in insurancecontract.py to avoid confusion
                        [condition, cash_left_by_categ] = self.balanced_portfolio(risk_to_insure, cash_left_by_categ, None) #Here it is check whether the portfolio is balanced or not if the reinrisk (risk_to_insure) is underwritten. Return True if it is balanced. False otherwise.
                        if condition:
                            contract = ReinsuranceContract(self, risk_to_insure, time, per_value_reinsurance_premium,
                                                           risk_to_insure["runtime"], \
                                                           self.default_contract_payment_period, \
                                                           expire_immediately=self.simulation_parameters[
                                                               "expire_immediately"], \
                                                           initial_VaR=var_this_risk, \
                                                           insurancetype=risk_to_insure[
                                                               "insurancetype"])  # TODO: implement excess of loss for reinsurance contracts
                            self.underwritten_contracts.append(contract)
                            self.cash_left_by_categ = cash_left_by_categ
                            reinrisks_per_categ[categ_id][iterion] = None

        not_accepted_reinrisks = []
        for categ_id in range(self.simulation_parameters["no_categories"]):
            for reinrisk in reinrisks_per_categ[categ_id]:
                if reinrisk is not None:
                    not_accepted_reinrisks.append(reinrisk)



        return reinrisks_per_categ, not_accepted_reinrisks

    def process_newrisks_insurer(self, risks_per_categ, number_risks_categ, acceptable_by_category, var_per_risk_per_categ, cash_left_by_categ, time): #This method processes one by one the risks contained in risks_per_categ in order to decide whether they should be underwritten or not.
                                                                                             #It is done in this way to maintain the portfolio as balanced as possible. For that reason we process risk[C1], risk[C2], risk[C3], risk[C4], risk[C1], risk[C2], ... and so forth.

        for iter in range(max(number_risks_categ)):
            for categ_id in range(len(acceptable_by_category)):    #Here we take only one risk per category at a time to achieve risk[C1], risk[C2], risk[C3], risk[C4], risk[C1], risk[C2], ... if possible.
                if iter < number_risks_categ[categ_id] and acceptable_by_category[categ_id] > 0 and \
                                risks_per_categ[categ_id][iter] is not None:
                    risk_to_insure = risks_per_categ[categ_id][iter]
                    if risk_to_insure.get("contract") is not None and risk_to_insure[
                        "contract"].expiration > time:  # risk_to_insure["contract"]: # required to rule out contracts that have exploded in the meantime
                        [condition, cash_left_by_categ] = self.balanced_portfolio(risk_to_insure, cash_left_by_categ, None)   #Here it is check whether the portfolio is balanced or not if the reinrisk (risk_to_insure) is underwritten. Return True if it is balanced. False otherwise.
                        if condition:
                            contract = ReinsuranceContract(self, risk_to_insure, time, \
                                                           self.simulation.get_reinsurance_market_premium(),
                                                           risk_to_insure["expiration"] - time, \
                                                           self.default_contract_payment_period, \
                                                           expire_immediately=self.simulation_parameters[
                                                               "expire_immediately"], )
                            self.underwritten_contracts.append(contract)
                            self.cash_left_by_categ = cash_left_by_categ
                            risks_per_categ[categ_id][iter] = None
                            # TODO: move this to insurancecontract (ca. line 14) -> DONE
                            # TODO: do not write into other object's properties, use setter -> DONE
                    else:
                        [condition, cash_left_by_categ] = self.balanced_portfolio(risk_to_insure, cash_left_by_categ,
                                                                                  var_per_risk_per_categ) #Here it is check whether the portfolio is balanced or not if the risk (risk_to_insure) is underwritten. Return True if it is balanced. False otherwise.
                        if condition:
                            contract = InsuranceContract(self, risk_to_insure, time, self.simulation.get_market_premium(), \
                                                         self.contract_runtime_dist.rvs(), \
                                                         self.default_contract_payment_period, \
                                                         expire_immediately=self.simulation_parameters[
                                                             "expire_immediately"], \
                                                         initial_VaR=var_per_risk_per_categ[categ_id])
                            self.underwritten_contracts.append(contract)
                            self.cash_left_by_categ = cash_left_by_categ
                            risks_per_categ[categ_id][iter] = None
                    acceptable_by_category[categ_id] -= 1  # TODO: allow different values per risk (i.e. sum over value (and reinsurance_share) or exposure instead of counting)

        not_accepted_risks = []
        for categ_id in range(len(acceptable_by_category)):
            for risk in risks_per_categ[categ_id]:
                if risk is not None:
                    not_accepted_risks.append(risk)

        return risks_per_categ, not_accepted_risks


    def market_permanency(self, time):     #This method determines whether an insurer or reinsurer stays in the market. If it has very few risks underwritten or too much cash left for TOO LONG it eventually leaves the market.
                                                      # If it has very few risks underwritten it cannot balance the portfolio so it makes sense to leave the market.
        if not self.simulation_parameters["market_permanency_off"]:

            cash_left_by_categ = np.asarray(self.cash_left_by_categ)

            avg_cash_left = cash_left_by_categ.mean()

            if self.cash < self.simulation_parameters["cash_permanency_limit"]:         #If their level of cash is so low that they cannot underwrite anything they also leave the market.
                self.market_exit(time)
            else:
                if self.is_insurer:

                    if len(self.underwritten_contracts) < self.simulation_parameters["insurance_permanency_contracts_limit"] or avg_cash_left / self.cash > self.simulation_parameters["insurance_permanency_ratio_limit"]:
                        #Insurers leave the market if they have contracts under the limit or an excess capital over the limit for too long.
                        self.market_permanency_counter += 1
                    else:
                        self.market_permanency_counter = 0                                    #All these limits maybe should be parameters in isleconfig.py

                    if self.market_permanency_counter >= self.simulation_parameters["insurance_permanency_time_constraint"]:    # Here we determine how much is too long.
                        self.market_exit(time)

                if self.is_reinsurer:

                    if len(self.underwritten_contracts) < self.simulation_parameters["reinsurance_permanency_contracts_limit"] or avg_cash_left / self.cash > self.simulation_parameters["reinsurance_permanency_ratio_limit"]:
                        #Reinsurers leave the market if they have contracts under the limit or an excess capital over the limit for too long.

                        self.market_permanency_counter += 1                                       #Insurers and reinsurers potentially have different reasons to leave the market. That's why the code is duplicated here.
                    else:
                        self.market_permanency_counter = 0

                    if self.market_permanency_counter >= self.simulation_parameters["reinsurance_permanency_time_constraint"]:  # Here we determine how much is too long.
                        self.market_exit(time)

    def register_claim(self, claim):    #This method records in insurancesimulation.py every claim made. It is called either from insurancecontract.py or reinsurancecontract.py respectively.
        self.simulation.record_claims(claim)

    def reset_pl(self):
        """Reset_pl Method.
               Accepts no arguments:
               No return value.
           Reset the profits and losses variable of each firm at the beginning of every iteration. It has to be run in insurancesimulation.py at the beginning of the iterate method"""
        self.profits_losses = 0







