
import math
import numpy as np
import sys, pdb
import scipy.stats
import numba as nb
import isleconfig
from distributionreinsurance import ReinsuranceDistWrapper


class RiskModel():
    def __init__(self, damage_distribution, expire_immediately, cat_separation_distribution, norm_premium, \
                category_number, init_average_exposure, init_average_risk_factor, init_profit_estimate, \
                margin_of_safety, var_tail_prob, inaccuracy):
        self.cat_separation_distribution = cat_separation_distribution
        self.norm_premium = norm_premium
        self.var_tail_prob = 0.02
        self.expire_immediately = expire_immediately
        self.category_number = category_number
        self.init_average_exposure = init_average_exposure
        self.init_average_risk_factor = init_average_risk_factor
        self.init_profit_estimate = init_profit_estimate
        self.margin_of_safety = margin_of_safety
        """damage_distribution is some scipy frozen rv distribution wich is bound between 0 and 1 and indicates 
           the share of risks suffering damage as part of any single catastrophic peril"""
        self.damage_distribution = [damage_distribution for _ in range(self.category_number)] # TODO: separate that category wise? -> DONE.
        self.damage_distribution_stack = [[] for _ in range(self.category_number)] 
        self.reinsurance_contract_stack = [[] for _ in range(self.category_number)] 
        #self.inaccuracy = np.random.uniform(9/10., 10/9., size=self.category_number) 
        self.inaccuracy = inaccuracy
    
    def getPPF(self, categ_id, tailSize):
        """Method for getting quantile function of the damage distribution (value at risk) by category.
           Positional arguments:
              categ_id  integer:            category 
              tailSize  (float >=0, <=1):   quantile
           Returns value-at-risk."""
        return self.damage_distribution[categ_id].ppf(1-tailSize)

    @nb.jit
    def get_categ_risks(self, risks, categ_id):
        #categ_risks2 = [risk for risk in risks if risk["category"]==categ_id]
        categ_risks = []
        for risk in risks:
            if risk["category"]==categ_id:
                categ_risks.append(risk)
        #assert categ_risks == categ_risks2
        return categ_risks
    
    @nb.jit    
    def compute_expectation(self, categ_risks, categ_id):      #TODO: more intuitive name?
        #average_exposure2 = np.mean([risk["excess"]-risk["deductible"] for risk in categ_risks])
        #
        ##average_risk_factor = np.mean([risk["risk_factor"] for risk in categ_risks])
        #average_risk_factor2 = self.inaccuracy[categ_id] * np.mean([risk["risk_factor"] for risk in categ_risks])
        #
        ## compute expected profits from category
        #mean_runtime2 = np.mean([risk["runtime"] for risk in categ_risks])
        
        exposures = []
        risk_factors = []
        runtimes = []
        for risk in categ_risks:
            # TODO: factor in excess instead of value?
            exposures.append(risk["value"]-risk["deductible"])
            risk_factors.append(risk["risk_factor"])
            runtimes.append(risk["runtime"])
        average_exposure = np.mean(exposures)
        average_risk_factor = self.inaccuracy[categ_id] * np.mean(risk_factors)
        mean_runtime = np.mean(runtimes)
        #assert average_exposure == average_exposure2
        #assert average_risk_factor == average_risk_factor2
        #assert mean_runtime == mean_runtime2
        
        if self.expire_immediately:
            incr_expected_profits = -1
            # TODO: fix the norm_premium estimation
            #incr_expected_profits = (self.norm_premium - (1 - scipy.stats.poisson(1 / self.cat_separation_distribution.mean() * \
            #                    mean_runtime).pmf(0)) * self.damage_distribution[categ_id].mean() * average_risk_factor) * average_exposure * len(categ_risks)
        else:
            incr_expected_profits = -1
            # TODO: expected profits should only be returned once the expire_immediately == False case is fixed
            #incr_expected_profits = (self.norm_premium - mean_runtime / self.cat_separation_distribution[categ_id].mean() * self.damage_distribution.mean() * average_risk_factor) * average_exposure * len(categ_risks)
        
        return average_risk_factor, average_exposure, incr_expected_profits
            
    def evaluate_proportional(self, risks, cash):
        
        assert len(cash) == self.category_number

        # prepare variables
        acceptable_by_category = []
        remaining_acceptable_by_category = []
        cash_left_by_category = np.copy(cash)
        expected_profits = 0
        necessary_liquidity = 0
        
        var_per_risk_per_categ = np.zeros(self.category_number)
        
        # compute acceptable risks by category
        for categ_id in range(self.category_number):
            # compute number of acceptable risks of this category 
            
            categ_risks = self.get_categ_risks(risks=risks, categ_id=categ_id)
            #categ_risks = [risk for risk in risks if risk["category"]==categ_id]
            
            if len(categ_risks) > 0:
                average_risk_factor, average_exposure, incr_expected_profits =  self.compute_expectation(categ_risks=categ_risks, categ_id=categ_id)
            else:
                average_risk_factor = self.init_average_risk_factor
                average_exposure = self.init_average_exposure

                incr_expected_profits = -1
                # TODO: expected profits should only be returned once the expire_immediately == False case is fixed
                #incr_expected_profits = 0

            expected_profits += incr_expected_profits
            
            # compute value at risk
            var_per_risk = self.getPPF(categ_id=categ_id, tailSize=self.var_tail_prob) * average_risk_factor * average_exposure * self.margin_of_safety
            
            # record liquidity requirement and apply margin of safety for liquidity requirement
            necessary_liquidity += var_per_risk * self.margin_of_safety * len(categ_risks)
            #print("RISKMODEL: ", self.getPPF(categ_id=categ_id, tailSize=0.01) * average_risk_factor * average_exposure, " = PPF(0.01) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash[categ_id], "TOTAL_RISK_IN_CATEG: ", self.getPPF(categ_id=categ_id, tailSize=0.01) * average_risk_factor * average_exposure * len(categ_risks))
            if isleconfig.verbose:
                print(self.inaccuracy)
                print("RISKMODEL: ", var_per_risk, " = PPF(0.02) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash[categ_id], "TOTAL_RISK_IN_CATEG: ", var_per_risk * len(categ_risks))
            #print("RISKMODEL: ", self.getPPF(categ_id=categ_id, tailSize=0.05) * average_risk_factor * average_exposure, " = PPF(0.05) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash[categ_id], "TOTAL_RISK_IN_CATEG: ", self.getPPF(categ_id=categ_id, tailSize=0.05) * average_risk_factor * average_exposure * len(categ_risks))
            #print("RISKMODEL: ", self.getPPF(categ_id=categ_id, tailSize=0.1) * average_risk_factor * average_exposure, " = PPF(0.1) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash[categ_id], "TOTAL_RISK_IN_CATEG: ", self.getPPF(categ_id=categ_id, tailSize=0.1) * average_risk_factor * average_exposure * len(categ_risks))
            #print("RISKMODEL: ", self.getPPF(categ_id=categ_id, tailSize=0.25) * average_risk_factor * average_exposure, " = PPF(0.25) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash[categ_id], "TOTAL_RISK_IN_CATEG: ", self.getPPF(categ_id=categ_id, tailSize=0.25) * average_risk_factor * average_exposure * len(categ_risks))
            #print("RISKMODEL: ", self.getPPF(categ_id=categ_id, tailSize=0.5) * average_risk_factor * average_exposure, " = PPF(0.5) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash[categ_id], "TOTAL_RISK_IN_CATEG: ", self.getPPF(categ_id=categ_id, tailSize=0.5) * average_risk_factor * average_exposure * len(categ_risks))
            #if cash[categ_id] < 0:
            #    pdb.set_trace()
            try:
                acceptable = int(math.floor(cash[categ_id] / var_per_risk))
                remaining = acceptable - len(categ_risks)
                cash_left = cash[categ_id] - len(categ_risks) * var_per_risk
            except:
                print(sys.exc_info())
                pdb.set_trace()
            acceptable_by_category.append(acceptable)
            remaining_acceptable_by_category.append(remaining)
            cash_left_by_category[categ_id] = cash_left
            var_per_risk_per_categ[categ_id] = var_per_risk

        # TODO: expected profits should only be returned once the expire_immediately == False case is fixed; the else-clause conditional statement should then be raised to unconditional
        if expected_profits < 0:
            expected_profits = None
        else:
            if necessary_liquidity == 0:
                assert expected_profits == 0
                expected_profits = self.init_profit_estimate * cash[0]
            else:
                expected_profits /= necessary_liquidity
                
        max_category = max(cash_left_by_category)
        remaining_acceptable_by_category[categ_id] = math.floor(
                        remaining_acceptable_by_category[categ_id] * pow(
                            cash_left_by_category[categ_id] / max_category, 5))
        if isleconfig.verbose:
            print("RISKMODEL returns: ", expected_profits, remaining_acceptable_by_category)
        return expected_profits, remaining_acceptable_by_category, cash_left_by_category, var_per_risk_per_categ

    def evaluate_excess_of_loss(self, risks, cash, offered_risk = None):
        
        cash_left_by_categ = np.copy(cash)
        assert len(cash_left_by_categ) == self.category_number
        
        # prepare variables
        additional_required = np.zeros(self.category_number)
        additional_var_per_categ = np.zeros(self.category_number)

        # values at risk and liquidity requirements by category
        for categ_id in range(self.category_number):
            categ_risks = self.get_categ_risks(risks=risks, categ_id=categ_id)
            
            # TODO: allow for different risk distributions for different categories
            # TODO: factor in risk_factors
            percentage_value_at_risk = self.getPPF(categ_id=categ_id, tailSize=self.var_tail_prob)
            
            # compute liquidity requirements from existing contracts
            for risk in categ_risks:
                expected_damage = percentage_value_at_risk * risk["value"] * risk["risk_factor"] \
                                                                           * self.inaccuracy[categ_id]
                expected_claim = min(expected_damage, risk["excess"]) - risk["deductible"]
                
                # record liquidity requirement and apply margin of safety for liquidity requirement
                cash_left_by_categ[categ_id] -= expected_claim * self.margin_of_safety
            
            # compute additional liquidity requirements from newly offered contract
            if (offered_risk is not None) and (offered_risk.get("category") == categ_id):
                expected_damage_fraction = percentage_value_at_risk * offered_risk["risk_factor"] \
                                                                      * self.inaccuracy[categ_id]
                expected_claim_fraction = min(expected_damage_fraction, offered_risk["excess_fraction"]) - offered_risk["deductible_fraction"]
                expected_claim_total = expected_claim_fraction * offered_risk["value"]
                
                # record liquidity requirement and apply margin of safety for liquidity requirement
                additional_required[categ_id] += expected_claim_total * self.margin_of_safety
                additional_var_per_categ[categ_id] += expected_claim_total
        
        # Additional value at risk should only occur in one category. Assert that this is the case.
        assert sum(additional_var_per_categ > 0) <= 1   
        var_this_risk = max(additional_var_per_categ)
        
        return cash_left_by_categ, additional_required, var_this_risk
        
    def evaluate(self, risks, cash, offered_risk = None):
        # ensure that any risk to be considered supplied directly as argument is non-proportional/excess-of-loss
        assert (offered_risk is None) or offered_risk.get("insurancetype") == "excess-of-loss"
        
        # construct cash_left_by_categ as a sequence, defining remaining liquidity by category
        if not isinstance(cash, (np.ndarray, list)):
            cash_left_by_categ = np.ones(self.category_number) * cash
        else:
            cash_left_by_categ = np.copy(cash)
        assert len(cash_left_by_categ) == self.category_number

        # sort current contracts
        el_risks = [risk for risk in risks if risk["insurancetype"] == 'excess-of-loss']
        risks = [risk for risk in risks if risk["insurancetype"] == 'proportional']
        
        # compute liquidity requirements and acceptable risks from existing contract
        if (offered_risk is not None) or (len(el_risks) > 0):
            cash_left_by_categ, additional_required, var_this_risk = self.evaluate_excess_of_loss(el_risks, cash_left_by_categ, offered_risk)
        if (offered_risk is None) or (len(risks) > 0):
            expected_profits_proportional, remaining_acceptable_by_categ, cash_left_by_categ, var_per_risk_per_categ = self.evaluate_proportional(risks, cash_left_by_categ)
        
        if offered_risk is None:
            # return numbers of remaining acceptable risks by category
            return expected_profits_proportional, remaining_acceptable_by_categ, var_per_risk_per_categ, min(cash_left_by_categ)
        else:       
            # return boolean value whether the offered excess_of_loss risk can be accepted
            if isleconfig.verbose:
                print ("REINSURANCE RISKMODEL", cash, cash_left_by_categ, (cash_left_by_categ - additional_required > 0).all())
            #if not (cash_left_by_categ - additional_required > 0).all():
            #    pdb.set_trace()
            return (cash_left_by_categ - additional_required > 0).all(), var_this_risk, min(cash_left_by_categ)
        
    def add_reinsurance(self, categ_id, excess_fraction, deductible_fraction, contract):
        self.damage_distribution_stack[categ_id].append(self.damage_distribution[categ_id])
        self.reinsurance_contract_stack[categ_id].append(contract)
        self.damage_distribution[categ_id] = ReinsuranceDistWrapper(lower_bound=deductible_fraction, \
                                                                    upper_bound=excess_fraction, \
                                                                    dist=self.damage_distribution[categ_id])

    def delete_reinsurance(self, categ_id, excess_fraction, deductible_fraction, contract):
        assert self.reinsurance_contract_stack[categ_id][-1] == contract
        self.reinsurance_contract_stack[categ_id].pop()
        self.damage_distribution[categ_id] = self.damage_distribution_stack[categ_id].pop()
                
