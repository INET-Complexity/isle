"""Deterministic risk model implementation for ISLE.
   Defines a deterministic risk model class.
   
   Created by Torsten Heinrich, Davoud Taghawi-Nejad."""

# import general python modules
import scipy.stats
import math
import pdb

# import scipy.stats modules
#from generalizedpareto import GeneralizedPareto
#from generalizedexponential import GeneralizedExponential

# import ISLE modules (none)
#import expectedvaluemc

# Risk model class #TODO: risk models should all inherit from an abstract risk model
class RiskModelGroupedDeterministic:
    def __init__(self,
                 riskDistribution=scipy.stats.pareto(2., 0., 10.),
                 riskPeriod=scipy.stats.expon(0, 100./3.)):
        """
          Constructor method. 
          Arguments:
            eventDist (rv frozen distribution): damage event separation time distribution, defaults to exponential
            eventSizeDist (rv frozen distribution): damage size distribution, defaults to power law
          Returns self.
             
          Setting default distributions:
             Power Law with x_min = 10.
                            alpha = 3.
                        => PDF(x) = 200 * x^(-3)
             Exponential with lambda = .03
                        => PDF(x) = 0.03 * e^(-0.03*x)
        """
        
        # Record properties
        self.riskDistribution = riskDistribution
        self.riskPeriod = riskPeriod
        
        # Prepare variables
        self.price = None               # Price (if premium for identical risks constant in each iteration for speed-up)
        self.acceptable_by_cat = []     # Number of risks that can safely be underwritten by category
        self.last_updated = -1          # Last updated time

    def getPPF(self, tailSize):
        """Method for getting quantile function of the distribution (value at risk).
           Positional arguments:
              tailSize (float >=0, <=1): quantile
           Returns value-at-risk."""
        return self.riskDistribution.ppf(1-tailSize)

    #def evaluate(self, runtime, excess, deductible, expectedReturn=.15):
    def evaluate(self, risk, riskcateg, runtime, excess, deductible, time_correlation_weight, riskcateg_underwritten, \
                                                                              liquidity, expectedReturn=.15, time=None):
        """ Evaluates if exposure to risk category is too high compared to 
             current liquidity. If not ...
            Returns x% (e.g., 15%) over the expected loss which is computed
            
            Positional arguments:
              risk (InsurableRisk object):                  risk to be insured
              runtime (int):                                contract runtime
              excess (float):                               excess
              deductible (float):                           deductible
              time_correlation_weight (float >=0, <=1):     share of correlated risk events (perils)
              riskcateg_underwritten (nested list of int):  numbers of underwritten risks by category
              liquidity (float):                            liquidity holdings of agent
            Optional arguments:
              expectedReturn (float >=0):                   price markup over expected losses 
              time (int):                                   current time
            Returns None or list (premium price, runtime, excess, deductible, risk)
        """
        
        # Since risks are identical, premium only needs to be computed once per iteration   #TODO: why not only once instead of in every iteration?
        if self.last_updated != time:
            # This version does not use MC simulations but ppf's
            #distributionExpectedValue, VaR = expectedvaluemc.getEV(self.riskDistribution, 1000, None, None, excess, 0.02)
            #periodExpectedValue = expectedvaluemc.getEV(self.riskPeriod, 1000, None, None, None)
            distributionExpectedValue, VaR = self.riskDistribution.mean(), self.getPPF(0.02)
            periodExpectedValue = self.riskPeriod.mean()
            
            # Reset time stamp
            if time is not None:
                self.last_updated = time
            
            # Compute expected loss and premium price
            #riskFreq.mean * riskDistribution.mean * runtime - deductible
            expectedLoss = distributionExpectedValue * (1./periodExpectedValue) * runtime - deductible
            #print("DEBUG  **RM", distributionExpectedValue, periodExpectedValue, expectedLoss, expectedReturn, \
            #                                                                    expectedLoss * (1. + expectedReturn))
            self.price = expectedLoss * (1. + expectedReturn)
            print(expectedLoss, self.price)
            # Evaluate how many risks can be underwritten by category
            #group_correlation = time_correlation_weight * 1./len(riskcateg)
            group_correlation = time_correlation_weight
            self.acceptable_by_cat = []
            self.total_acceptable_by_cat = []
            self.total_VaR_by_cat = []
            for i in range(len(riskcateg_underwritten)):
                self.acceptable_by_cat.append([])
                self.total_acceptable_by_cat.append([])
                self.total_VaR_by_cat.append([])
                if riskcateg_underwritten[i] is not None:
                    for j in range(len(riskcateg_underwritten[i])):
                        #acceptable = math.floor(liquidity * group_correlation * 1. / (VaR * (1./periodExpectedValue) \
                        #                                                                        * runtime - deductible))
                        acceptable = math.floor(liquidity * 1./VaR)
                        self.acceptable_by_cat[i].append(acceptable - riskcateg_underwritten[i][j])
                        self.total_acceptable_by_cat[i].append(acceptable)
                        self.total_VaR_by_cat[i].append(riskcateg_underwritten[i][j] * VaR)
                else:
                    self.total_acceptable_by_cat[i] = None
                    self.acceptable_by_cat[i] = None
                    self.total_VaR_by_cat[i] = None
                    
            # print some debugging output. Should be removed in future versions
            print(self.acceptable_by_cat, end=" ")
            print(riskcateg_underwritten, end=" ")
            print(self.total_acceptable_by_cat, end=" ")
            print(self.total_VaR_by_cat, end=" ")
            print("")
        
        # Determine if risks of the category presently considered can be underwritten, otherwise reject and return None
        for i in range(len(riskcateg)):
            if (riskcateg_underwritten[i] is not None) and (riskcateg[i] is not None):
                if self.acceptable_by_cat[i][riskcateg[i]] <= 0:
                    #print("REJECTED")
                    return None
                else:
                    #print(self.acceptable_by_cat[i][riskcateg[i]],end=" ")
                    if (riskcateg[i] is not None):
                        self.acceptable_by_cat[i][riskcateg[i]] -= 1
        
        # Return offer
        return [self.price, runtime, excess, deductible, risk]

        """ TODO: this takes the VaR in terms of damage for single risk group events, not the likelihood 
                  of several risk group events in temporal proximity (i.e. the VaR is computed for total damage 
                  from one hurricane, not for that from all hurricanes over a period)"""



    # def getDistributionPPF(self, tailSize):
    #     """ allows to check for expected size of 1/x period (e.g. 1/200 year) events ... and to compute expected value (.5)"""
    #     return self.riskDistribution.quantile(tailSize);

    # def getPeriodPPF(self, tailSize):
    #     """ allows to compute expected value (.5)"""
    #     return self.riskPeriod.quantile(tailSize);

    # def getDistributionInverseCDF(self, x):
    #     return 1. - self.riskDistribution.cumulative(x);

