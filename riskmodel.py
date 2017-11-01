
import math
import numpy as np
import sys, pdb
import scipy.stats
import numba as nb

class RiskModel():
    def __init__(self, damage_distribution, expire_immediately, cat_separation_distribution, norm_premium, \
                category_number, init_average_exposure, init_average_risk_factor, init_profit_estimate, inaccuracy):
        """risk_distribution is some scipy frozen rv distribution wich is bound between 0 and 1 and indicates 
           the share of risks suffering damage as part of any single catastrophic peril"""
        self.damage_distribution = damage_distribution  # TODO: separate that category wise?
        self.cat_separation_distribution = cat_separation_distribution
        self.norm_premium = norm_premium
        self.var_tail_prob = 0.02
        self.expire_immediately = expire_immediately
        self.category_number = category_number
        self.init_average_exposure = init_average_exposure
        self.init_average_risk_factor = init_average_risk_factor
        self.init_profit_estimate = init_profit_estimate
        #self.inaccuracy = np.random.uniform(9/10., 10/9., size=self.category_number) 
        self.inaccuracy = inaccuracy
    
    def getPPF(self, tailSize):
        """Method for getting quantile function of the distribution (value at risk).
           Positional arguments:
              tailSize (float >=0, <=1): quantile
           Returns value-at-risk."""
        return self.damage_distribution.ppf(1-tailSize)

    nb.jit
    def get_categ_risks(self, risks, categ_id):
        #categ_risks2 = [risk for risk in risks if risk["category"]==categ_id]
        categ_risks = []
        for risk in risks:
            if risk["category"]==categ_id:
                categ_risks.append(risk)
        #assert categ_risks == categ_risks2
        return categ_risks
    
    nb.jit    
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
            exposures.append(risk["excess"]-risk["deductible"])
            risk_factors.append(risk["risk_factor"])
            runtimes.append(risk["runtime"])
        average_exposure = np.mean(exposures)
        average_risk_factor = self.inaccuracy[categ_id] * np.mean(risk_factors)
        mean_runtime = np.mean(runtimes)
        #assert average_exposure == average_exposure2
        #assert average_risk_factor == average_risk_factor2
        #assert mean_runtime == mean_runtime2
        
        if self.expire_immediately:
            incr_expected_profits = (self.norm_premium - (1 - scipy.stats.poisson(1 / self.cat_separation_distribution.mean() * \
                                mean_runtime).pmf(0)) * self.damage_distribution.mean() * average_risk_factor) * average_exposure * len(categ_risks)
        else:
            incr_expected_profits = (self.norm_premium - mean_runtime / self.cat_separation_distribution.mean() * self.damage_distribution.mean() * average_risk_factor) * average_exposure * len(categ_risks)
        
        return average_risk_factor, average_exposure, incr_expected_profits
            
    def evaluate(self, risks, cash):
        acceptable_by_category = []
        remaining_acceptable_by_category = []
        expected_profits = 0
        necessary_liquidity = 0
        for categ_id in range(self.category_number):
            # compute number of acceptable risks of this category 
            
            categ_risks = self.get_categ_risks(risks=risks, categ_id=categ_id)
            #categ_risks = [risk for risk in risks if risk["category"]==categ_id]
            
            if len(categ_risks) > 0:
                average_risk_factor, average_exposure, incr_expected_profits =  self.compute_expectation(categ_risks=categ_risks, categ_id=categ_id)
            else:
                average_risk_factor = self.init_average_risk_factor
                average_exposure = self.init_average_exposure
                incr_expected_profits = 0
            expected_profits += incr_expected_profits
            var_per_risk = self.getPPF(self.var_tail_prob) * average_risk_factor * average_exposure
            necessary_liquidity += var_per_risk * len(categ_risks)
            #print("RISKMODEL: ", self.getPPF(0.01) * average_risk_factor * average_exposure, " = PPF(0.01) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash, "TOTAL_RISK_IN_CATEG: ", self.getPPF(0.01) * average_risk_factor * average_exposure * len(categ_risks))
            print(self.inaccuracy)
            print("RISKMODEL: ", var_per_risk, " = PPF(0.02) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash, "TOTAL_RISK_IN_CATEG: ", var_per_risk * len(categ_risks))
            #print("RISKMODEL: ", self.getPPF(0.05) * average_risk_factor * average_exposure, " = PPF(0.05) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash, "TOTAL_RISK_IN_CATEG: ", self.getPPF(0.05) * average_risk_factor * average_exposure * len(categ_risks))
            #print("RISKMODEL: ", self.getPPF(0.1) * average_risk_factor * average_exposure, " = PPF(0.1) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash, "TOTAL_RISK_IN_CATEG: ", self.getPPF(0.1) * average_risk_factor * average_exposure * len(categ_risks))
            #print("RISKMODEL: ", self.getPPF(0.25) * average_risk_factor * average_exposure, " = PPF(0.25) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash, "TOTAL_RISK_IN_CATEG: ", self.getPPF(0.25) * average_risk_factor * average_exposure * len(categ_risks))
            #print("RISKMODEL: ", self.getPPF(0.5) * average_risk_factor * average_exposure, " = PPF(0.5) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash, "TOTAL_RISK_IN_CATEG: ", self.getPPF(0.5) * average_risk_factor * average_exposure * len(categ_risks))
            try:
                acceptable = int(math.floor(cash / var_per_risk))
                remaining = acceptable - len(categ_risks)
            except:
                print(sys.exc_info())
                pdb.set_trace()
            acceptable_by_category.append(acceptable)
            remaining_acceptable_by_category.append(remaining)
        if necessary_liquidity == 0:
            assert expected_profits == 0
            expected_profits = self.init_profit_estimate * cash
        else:
            expected_profits /= necessary_liquidity
        print("RISKMODEL returns: ", expected_profits, remaining_acceptable_by_category)
        return expected_profits, remaining_acceptable_by_category
