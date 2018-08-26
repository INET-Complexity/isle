
import isleconfig
import numpy as np
import scipy.stats
from insurancecontract import InsuranceContract
from reinsurancecontract import ReinsuranceContract
from metainsuranceorg import MetaInsuranceOrg
from riskmodel import RiskModel
import sys, pdb
import uuid
import numba as nb

class CatBond(MetaInsuranceOrg):
    def init(self, simulation, per_period_premium, owner, interest_rate = 0):   # do we need simulation parameters
        self.simulation = simulation
        self.id = 0
        self.underwritten_contracts = []
        self.cash = 0
        self.obligations = []
        self.operational = True
        self.owner = owner
        self.per_period_dividend = per_period_premium
        self.interest_rate = interest_rate  # TODO: shift obtain_yield method to insurancesimulation, thereby making it unnecessary to drag parameters like self.interest_rate from instance to instance and from class to class
        #self.simulation_no_risk_categories = self.simulation.simulation_parameters["no_categories"]
    
    # TODO: change start and InsuranceSimulation so that it iterates CatBonds
    #old parent class init, cat bond class should be much smaller
    def parent_init(self, simulation_parameters, agent_parameters):
        #def init(self, simulation_parameters, agent_parameters):
        self.simulation = simulation_parameters['simulation']
        self.simulation_parameters = simulation_parameters
        self.contract_runtime_dist = scipy.stats.randint(simulation_parameters["mean_contract_runtime"] - \
                  simulation_parameters["contract_runtime_halfspread"], simulation_parameters["mean_contract_runtime"] \
                  + simulation_parameters["contract_runtime_halfspread"] + 1)
        self.default_contract_payment_period = simulation_parameters["default_contract_payment_period"]
        self.id = agent_parameters['id']
        self.cash = agent_parameters['initial_cash']
        self.premium = agent_parameters["norm_premium"]
        self.profit_target = agent_parameters['profit_target']
        self.acceptance_threshold = agent_parameters['initial_acceptance_threshold']  # 0.5
        self.acceptance_threshold_friction = agent_parameters['acceptance_threshold_friction']  # 0.9 #1.0 to switch off
        self.interest_rate = agent_parameters["interest_rate"]
        self.reinsurance_limit = agent_parameters["reinsurance_limit"]
        self.simulation_no_risk_categories = simulation_parameters["no_categories"]
        self.simulation_reinsurance_type = simulation_parameters["simulation_reinsurance_type"]
        
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

    def iterate(self, time):
        """obtain investments yield"""
        self.obtain_yield(time)

        """realize due payments"""
        self.effect_payments(time)
        if isleconfig.verbose:
            print(time, ":", self.id, len(self.underwritten_contracts), self.cash, self.operational)
            
            """mature contracts"""
            print("Number of underwritten contracts ", len(self.underwritten_contracts))
        maturing = [contract for contract in self.underwritten_contracts if contract.expiration <= time]
        for contract in maturing:
            self.underwritten_contracts.remove(contract)
            contract.mature(time)
        contracts_dissolved = len(maturing)

        """effect payments from contracts"""
        [contract.check_payment_due(time) for contract in self.underwritten_contracts]
        
        if self.underwritten_contracts == []:
            self.mature_bond()  #TODO: mature_bond method should check if operational
            
        else:   #TODO: dividend should only be payed according to pre-arranged schedule, and only if no risk events have materialized so far
            if self.operational:
                self.pay_dividends(time)

        #self.estimated_var()   # cannot compute VaR for catbond as catbond does not have a riskmodel
    
    #old parent class iterate, cat bond class should be much smaller
    def parent_iterate(self, time):        # TODO: split function so that only the sequence of events remains here and everything else is in separate methods
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
            try:
                assert contracts_offered > 2 * contracts_dissolved
            except:
                print("Something wrong; agent {0:d} receives too few new contracts {1:d} <= {2:d}".format(self.id, contracts_offered, 2*contracts_dissolved), file=sys.stderr)
            #print(self.id, " has ", len(self.underwritten_contracts), " & receives ", contracts_offered, " & lost ", contracts_dissolved)
            
            new_nonproportional_risks = [risk for risk in new_risks if risk.get("insurancetype")=='excess-of-loss' and risk["owner"] is not self]
            new_risks = [risk for risk in new_risks if risk.get("insurancetype") in ['proportional', None] and risk["owner"] is not self]

            underwritten_risks = [{"value": contract.value, "category": contract.category, \
                            "risk_factor": contract.risk_factor, "deductible": contract.deductible, \
                            "excess": contract.excess, "insurancetype": contract.insurancetype, \
                            "runtime": contract.runtime} for contract in self.underwritten_contracts if contract.reinsurance_share != 1.0]
            
            """deal with non-proportional risks first as they must evaluate each request separatly, then with proportional ones"""
            for risk in new_nonproportional_risks:
                accept, var_this_risk = self.riskmodel.evaluate(underwritten_risks, self.cash, risk)       # TODO: change riskmodel.evaluate() to accept new risk to be evaluated and to account for existing non-proportional risks correctly -> DONE.
                if accept:
                    per_value_reinsurance_premium = self.np_reinsurance_premium_share * risk["periodized_total_premium"] * risk["runtime"] / risk["value"]            #TODO: rename this to per_value_premium in insurancecontract.py to avoid confusion
                    contract = ReinsuranceContract(self, risk, time, per_value_reinsurance_premium, risk["runtime"], \
                                                  self.default_contract_payment_period, \
                                                  expire_immediately=self.simulation_parameters["expire_immediately"], \
                                                  initial_VaR=var_this_risk, \
                                                  insurancetype=risk["insurancetype"])        # TODO: implement excess of loss for reinsurance contracts
                    self.underwritten_contracts.append(contract)
                #pass    # TODO: write this nonproportional risk acceptance decision section based on commented code in the lines above this -> DONE.
            
            """make underwriting decisions, category-wise"""
            # TODO: Enable reinsurance shares other tan 0.0 and 1.0
            expected_profit, acceptable_by_category, var_per_risk_per_categ = self.riskmodel.evaluate(underwritten_risks, self.cash)

            #if expected_profit * 1./self.cash < self.profit_target:
            #    self.acceptance_threshold = ((self.acceptance_threshold - .4) * 5. * self.acceptance_threshold_friction) / 5. + .4
            #else:
            #    self.acceptance_threshold = (1 - self.acceptance_threshold_friction * (1 - (self.acceptance_threshold - .4) * 5.)) / 5. + .4

            growth_limit = max(50, 2 * len(self.underwritten_contracts) + contracts_dissolved)
            if sum(acceptable_by_category) > growth_limit:
                acceptable_by_category = np.asarray(acceptable_by_category)
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

            # seek reinsurance
            if self.is_insurer:
                # TODO: Why should only insurers be able to get reinsurance (not reinsurers)? (Technically, it should work)
                self.ask_reinsurance(time)

            # return unacceptables
            #print(self.id, " now has ", len(self.underwritten_contracts), " & returns ", len(not_accepted_risks))
            self.simulation.return_risks(not_accepted_risks)

            #not implemented
            #"""adjust liquidity, borrow or invest"""
            #pass

        self.estimated_var()
    
    def set_owner(self, owner):
        self.owner = owner
        if isleconfig.verbose:
            print("SOLD")
        #pdb.set_trace()
    
    def set_contract(self, contract):
        self.underwritten_contracts.append(contract)
    
    def mature_bond(self):
        self.pay(self.cash, self.simulation)
        self.simulation.delete_agents("catbond", [self])
        self.operational = False


