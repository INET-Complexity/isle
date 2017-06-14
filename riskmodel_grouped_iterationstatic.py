#/**
# * Created by Torsten Heinrich
# */
# Translated to python by Davoud Taghawi-Nejad
import expectedvaluemc
#from generalizedpareto import GeneralizedPareto
#from generalizedexponential import GeneralizedExponential
import scipy.stats
import math
import pdb

class RiskModelGroupedS:
    def __init__(self,
                 riskDistribution=scipy.stats.pareto(2., 0., 10.),
                 riskPeriod=scipy.stats.expon(0, 100./1.)):
        """
          setting default distributions:
             Power Law with x_min = 10.
                            alpha = 3.
                        => PDF(x) = 200 * x^(-3)
             Exponential with lambda = .01
                        => PDF(x) = 0.01 * e^(-0.01*x)
        """
        self.riskDistribution = riskDistribution;
        self.riskPeriod = riskPeriod;
        self.price = None
        self.acceptable_by_cat = []
        self.last_updated = -1

    # def getDistributionPPF(self, tailSize):
    #     """ allows to check for expected size of 1/x period (e.g. 1/200 year) events ... and to compute expected value (.5)"""
    #     return self.riskDistribution.quantile(tailSize);

    def getPPF(self, tailSize):
        """alias of getDistributionPPF """
        return self.riskDistribution.ppf(tailSize);		#TODO: correct syntax?

    # def getPeriodPPF(self, tailSize):
    #     """ allows to compute expected value (.5)"""
    #     return self.riskPeriod.quantile(tailSize);

    # def getDistributionInverseCDF(self, x):
    #     return 1. - self.riskDistribution.cumulative(x);

    #def evaluate(self, runtime, excess, deductible, expectedReturn=.15):
    def evaluate(self, risk, riskcateg, runtime, excess, deductible, time_correlation_weight, riskcateg_underwritten, liquidity, expectedReturn=.15, time=None):
        """ Evaluates if exposure to risk category is too high compared to 
             current liquidity. If not ...
            Returns x% (e.g., 15%) over the expected loss which is computed
        using Monte Carlo Simulations of risk distribution (excess respected)
        and risk period /riskPeriod.mean * riskDistribution.mean * runtime -
        deductible = riskFreq.mean * riskDistribution.mean * runtime - deductible """
        
        if self.last_updated != time:
            distributionExpectedValue, VaR = expectedvaluemc.getEV(self.riskDistribution, 1000, None, None, excess, 0.02)
            periodExpectedValue = expectedvaluemc.getEV(self.riskPeriod, 1000, None, None, None)
            if time is not None:
                self.last_updated = time
            expectedLoss = distributionExpectedValue * (1./periodExpectedValue) * runtime - deductible
            #print("DEBUG  **RM", distributionExpectedValue, periodExpectedValue, expectedLoss, expectedReturn, expectedLoss * (1. + expectedReturn))
            self.price = expectedLoss * (1. + expectedReturn)
            group_correlation = time_correlation_weight * 1./len(riskcateg)
            self.acceptable_by_cat = []
            for i in range(len(riskcateg_underwritten)):
                self.acceptable_by_cat.append([])
                if riskcateg_underwritten[i] is not None:
                    for j in range(len(riskcateg_underwritten[i])):
                        acceptable = math.floor(liquidity * group_correlation * 1. / (VaR * (1./periodExpectedValue) * runtime - deductible))
                        self.acceptable_by_cat[i].append(acceptable)
                else:
                    self.acceptable_by_cat[i] = None
        
        for i in range(len(riskcateg)):
            if riskcateg_underwritten[i] is not None:
                if self.acceptable_by_cat[i][riskcateg[i]] <= 0:
                    return None
                else:
                    self.acceptable_by_cat[i][riskcateg[i]] -= 1
        return [self.price, runtime, excess, deductible, risk]

        """ TODO: this takes the VaR in terms of damage for single risk group events, not the likelihood 
                  of several risk group events in temporal proximity (i.e. the VaR is computed for total damage 
                  from one hurricane, not for that from all hurricanes over a period)"""

