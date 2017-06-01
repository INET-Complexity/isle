#/**
# * Created by Torsten Heinrich
# */
# Translated to python by Davoud Taghawi-Nejad
import expectedvaluemc
#from generalizedpareto import GeneralizedPareto
#from generalizedexponential import GeneralizedExponential
import scipy.stats

class RiskModel:
    def __init__(self,
                 riskDistribution=scipy.stats.pareto(2., 0., 10.),
                 riskPeriod=scipy.stats.expon(0, 100./3.)):
        """
          setting default distributions:
             Power Law with x_min = 10.
                            alpha = 3.
                        => PDF(x) = 200 * x^(-3)
             Exponential with lambda = .03
                        => PDF(x) = 0.03 * e^(-0.03*x)
        """
        self.riskDistribution = riskDistribution;
        self.riskPeriod = riskPeriod;

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

    def evaluate(self, runtime, excess, deductible, expectedReturn=.15):
        """ Returns x% (e.g., 15%) over the expected loss which is computed
        using Monte Carlo Simulations of risk distribution (excess respected)
        and risk period /riskPeriod.mean * riskDistribution.mean * runtime -
        deductible = riskFreq.mean * riskDistribution.mean * runtime - deductible """


        distributionExpectedValue = expectedvaluemc.getEV(self.riskDistribution, 1000, None, None, excess);
        periodExpectedValue = expectedvaluemc.getEV(self.riskPeriod, 1000, None, None, None);

        expectedLoss = distributionExpectedValue * (1./periodExpectedValue) * runtime - deductible;
        print("DEBUG  **RM", distributionExpectedValue, periodExpectedValue, expectedLoss, expectedReturn, expectedLoss * (1. + expectedReturn))
        return expectedLoss * (1. + expectedReturn);

