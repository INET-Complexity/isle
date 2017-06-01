#/**
# * Created by Torsten Heinrich
# */
# Translated to python by Davoud Taghawi-Nejad from random import Random

#from generalizedpareto import GeneralizedPareto
#from generalizedexponential import GeneralizedExponential
#from scipy.stats import genpareto
import scipy.stats
#import pdb

#TODO: deal with runtime/endtime and remove risk from the owner's portfolio
class InsurableRisk:
    def __init__(self, time, 
                 value=scipy.stats.pareto(2., 0., 10.),
                 runtime=100,
                 eventDist=scipy.stats.expon(0, 100./3.),
                 eventSizeDist=scipy.stats.pareto(2., 0., 10.),
                 seed=None):
        self.value = value.rvs()
        #print(self.value)
        #pdb.set_trace()
        self.eventDist = eventDist
        self.eventSizeDist = eventSizeDist
        self.damage = 0
        self.runtime = runtime
        self.endtime = runtime + time
        #self.coverage = False
        assert seed is None

    def getTimeToNextEvent(self):
        return self.eventDist.rvs()

    def getSizeOfEvent(self):
        return self.eventSizeDist.rvs()

    def explode(self, time):
        self.set_damage(self.getSizeOfEvent())
        return self.schedule_next_event(time)
    
    def schedule_next_event(self, time):
        explode_time = self.getTimeToNextEvent() + time
        if explode_time <= self.endtime:
            return explode_time, self
        else:
            return None, None
        
    def set_damage(self, damage):
        self.damage = damage
    
    #def set_coverage(self):
    #    self.coverage = True
