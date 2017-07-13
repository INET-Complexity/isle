"""
 Insurable risk class for ISLE.
 
 Created by Torsten Heinrich, Davoud Taghawi-Nejad.
"""

# import general python modules
import scipy.stats
import uuid
#import pdb

# InsurableRisk class
class InsurableRisk:
    def __init__(self, time, 
                 value=scipy.stats.pareto(2., 0., 10.),
                 runtime=100,
                 eventDist=scipy.stats.expon(0, 100./3.),
                 eventSizeDist=scipy.stats.pareto(2., 0., 10.),
                 seed=None):
        """Constructor method. Required positional argument
             time (int):                        present simulation time (iteration number)
           Optional arguments:
             value (float):                     value of risk; default to being drawn from power law (not used here)
                                        # TODO: As it is not used, supplying arbitrary value should speed up simulation
             eventDist (rv frozen distribution): damage event separation time distribution
             eventSizeDist (rv frozen distribution): damage size distribution
             seed (int?): random seed
             """
        # Record properties    
        if value is not None:
            self.value = value.rvs() #not used in the case of damage calculation with eventDist and eventSizeDist
        self.eventDist = eventDist
        self.eventSizeDist = eventSizeDist
        self.damage = 0
        self.covered = False
        self.uuid = str(uuid.uuid4())   # Unique ID to allow identification or messages concerning specific risks.
        if runtime is not None:
            self.runtime = runtime
            self.endtime = runtime + time
        assert seed is None

    def getTimeToNextEvent(self, time = None):
        """Method for getting time to next event (by default drawn from self.eventDist distribution).
           Optional argument:
             time (any): Not used. Allows generic use of method that is overwritten in inheriting classes where time is 
             required"""
        return self.eventDist.rvs()

    def getSizeOfEvent(self):
        """Method for getting rv from damage size distribution. No arguments.
           Returns (float): damage size."""
        return self.eventSizeDist.rvs()

    def explode(self, time):
        """Method for effecting risk event, getting and recording damage size, scheduling next event.
           Positional argument:
             time (int): current time
           Returns (tuple (float, InsurableRisk object) or tuple (None, None)): next event time, self or None, None"""
        self.set_damage(self.getSizeOfEvent())
        #print("DEBUG explode: {0:f}".format(self.damage))
        return self.schedule_next_event(time)
    
    def schedule_next_event(self, time):
        """Method for determining whether there is a next event and returning event time if so.
           Positional argument:
             time (int): current time
           Returns (tuple (float, InsurableRisk object) or tuple (None, None)): next event time, self or None, None"""
        explode_time = self.getTimeToNextEvent() + time
        if explode_time <= self.endtime:
            return explode_time, self
        else:
            return None, None
        
    def set_damage(self, damage):
        """Damage setter method. Positional argument:
             damage (float): damage
           Returns None."""
        self.damage = damage
    
    def set_coverage(self, state):
        '''Method to set the insured/non-insured state of the risk
           arguments: 
            state: type bool - indicates whether the risk is currently insured'''
        self.covered = state

    def get_coverage(self):
        '''Method to get the insured/non-insured state of the risk'''
        return self.covered
