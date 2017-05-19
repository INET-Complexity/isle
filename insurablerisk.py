#/**
# * Created by Torsten Heinrich
# */
# Translated to python by Davoud Taghawi-Nejad from random import Random
from generalizedpareto import GeneralizedPareto
from generalizedexponential import GeneralizedExponential
from scipy.stats import genpareto


class InsurableRisk:
    def __init__(self,
                 value=genpareto(10., 10.*3., 1./3.),
                 runtime=100,
                 eventDist=GeneralizedExponential(33.33),
                 eventSizeDist=GeneralizedPareto(10., 10.*3., 1./3.),
                 seed=None):
        self.value = value
        self.eventDist = eventDist
        self.eventSizeDist = eventSizeDist
        self.damage = 0
        self.runtime = runtime
        assert seed is None

    def getTimeToNextEvent(self):
        return self.eventDist.random()

    def getSizeOfEvent(self):
        return self.eventSizeDist.random()

    def explode(self, damage):
        self.damage = damage

