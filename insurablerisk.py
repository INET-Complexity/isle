#/**
# * Created by Torsten Heinrich
# */
# Translated to python by Davoud Taghawi-Nejad from random import Random

#from generalizedpareto import GeneralizedPareto
#from generalizedexponential import GeneralizedExponential
#from scipy.stats import genpareto
import scipy.stats
#import pdb

class InsurableRisk:
    def __init__(self,
                 value=scipy.stats.genpareto(10., 10.*3., 1./3.).rvs(),
                 runtime=100,
                 eventDist=scipy.stats.expon(33.33),
                 eventSizeDist=scipy.stats.genpareto(10., 10.*3., 1./3.),
                 seed=None):
        self.value = value
        #print(self.value)
        #pdb.set_trace()
        self.eventDist = eventDist
        self.eventSizeDist = eventSizeDist
        self.damage = 0
        self.runtime = runtime
        assert seed is None

    def getTimeToNextEvent(self):
        return self.eventDist.rvs()

    def getSizeOfEvent(self):
        return self.eventSizeDist.rvs()

    def explode(self, damage):
        self.damage = damage

