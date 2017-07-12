#/**
# * Created by Torsten Heinrich
# */
# Translated to python by Davoud Taghawi-Nejad from random import Random

#from generalizedpareto import GeneralizedPareto
#from generalizedexponential import GeneralizedExponential
#from scipy.stats import genpareto
import scipy.stats
import uuid
#import pdb

#TODO: deal with runtime/endtime and remove risk from the owner's portfolio
class InsurableRisk:
    def __init__(self, time, 
                 value=scipy.stats.pareto(2., 0., 10.),
                 runtime=100,
                 eventDist=scipy.stats.expon(0, 100./3.),
                 eventSizeDist=scipy.stats.pareto(2., 0., 10.),
                 seed=None):
        if value is not None:
            self.value = value.rvs() #not used in the case of damage calculation with eventDist and eventSizeDist
            #print(self.value)
            #pdb.set_trace()
        self.eventDist = eventDist
        self.eventSizeDist = eventSizeDist
        self.damage = 0
        self.covered = False
        self.uuid = str(uuid.uuid4())
        if runtime is not None:
            self.runtime = runtime
            self.endtime = runtime + time
        assert seed is None

    def getTimeToNextEvent(self, time = None):
        return self.eventDist.rvs()

    def getSizeOfEvent(self):
        return self.eventSizeDist.rvs()

    def explode(self, time):
        self.set_damage(self.getSizeOfEvent())
        #print("DEBUG explode: {0:f}".format(self.damage))
        return self.schedule_next_event(time)
    
    def schedule_next_event(self, time):
        explode_time = self.getTimeToNextEvent() + time
        if explode_time <= self.endtime:
            return explode_time, self
        else:
            return None, None
        
    def set_damage(self, damage):
        self.damage = damage
    
    def set_coverage(self, state):
        '''Method to set the insured/non-insured state of the risk
           arguments: 
            state: type bool - indicates whether the risk is currently insured'''
        self.covered = state

    def get_coverage(self):
        '''Method to get the insured/non-insured state of the risk'''
        return self.covered
