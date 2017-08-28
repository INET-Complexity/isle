
import math
import numpy as np
import sys, pdb
import scipy.stats

class RiskModel():
    def __init__(self, damage_distribution, expire_immediately, cat_separation_distribution, norm_premium, \
                category_number, init_average_exposure, init_average_risk_factor, init_profit_estimate):
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
    
    def getPPF(self, tailSize):
        """Method for getting quantile function of the distribution (value at risk).
           Positional arguments:
              tailSize (float >=0, <=1): quantile
           Returns value-at-risk."""
        return self.damage_distribution.ppf(1-tailSize)
            
    def evaluate(self, risks, cash):
        acceptable_by_category = []
        remaining_acceptable_by_category = []
        expected_profits = 0
        necessary_liquidity = 0
        for categ_id in range(self.category_number):
            # compute number of acceptable risks of this category 
            categ_risks = [risk for risk in risks if risk["category"]==categ_id]
            if len(categ_risks) > 0:
                average_exposure = np.mean([risk["excess"]-risk["deductible"] for risk in categ_risks])
                average_risk_factor = np.mean([risk["risk_factor"] for risk in categ_risks])
                # compute expected profits from category
                mean_runtime = np.mean([risk["runtime"] for risk in categ_risks])
                if self.expire_immediately:
                    expected_profits += (self.norm_premium - (1 - scipy.stats.poisson(1 / self.cat_separation_distribution.mean() * \
                                        mean_runtime).pmf(0)) * self.damage_distribution.mean() * average_risk_factor) * average_exposure * len(categ_risks)
                else:
                    expected_profits += (self.norm_premium - mean_runtime / self.cat_separation_distribution.mean() * self.damage_distribution.mean() * average_risk_factor) * average_exposure * len(categ_risks)
            else:
                average_risk_factor = self.init_average_risk_factor
                average_exposure = self.init_average_exposure
                expected_profits += 0
            var_per_risk = self.getPPF(self.var_tail_prob) * average_risk_factor * average_exposure
            necessary_liquidity += var_per_risk * len(categ_risks)
            #print("RISKMODEL: ", self.getPPF(0.01) * average_risk_factor * average_exposure, " = PPF(0.01) * ", average_risk_factor, " * ", average_exposure, " vs. cash: ", cash, "TOTAL_RISK_IN_CATEG: ", self.getPPF(0.01) * average_risk_factor * average_exposure * len(categ_risks))
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
            expected_profits / necessary_liquidity
        print("RISKMODEL returns: ", expected_profits, remaining_acceptable_by_category)
        return expected_profits, remaining_acceptable_by_category
