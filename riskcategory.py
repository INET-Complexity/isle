"""Risk Category module for ISLE.
   Defines RiskCategory class to handle grouped risk event correlation.
   
   Created by Torsten Heinrich."""

import scipy.stats

# RiskCategory class
class RiskCategory():
    def __init__(self, time, max_runtime, eventDist=scipy.stats.expon(0, 100./3.)):
        """Constructor method. Requires positional arguments:
             time (int):        present simulation time (iteration number)
             max_runtime (int): end of the simulation
           Optional argument:
             eventDist (scipy.stats rv frozen distribution): event sepatation time distribution, defaults to exponential
           Returns self.
           Method creates category and populates category event schedule."""
        self.eventDist = eventDist                                      # separation time distribution
        self.eventTimeList = self.populateEventList(time, max_runtime)  # event schedule
        print(self.eventTimeList)
    
    def populateEventList(self, time, max_runtime):
        """Method to create event schedule by drawing event separation times from the eventDist until the scheduled 
           simulation end time is reached. Required positional arguments:
             time (int):        present simulation time (iteration number)
             max_runtime (int): end of the simulation
           Returns event schedule (list of float). 
           """
        events = []
        while (time < max_runtime):
            time += self.eventDist.rvs()
            if time < max_runtime:
                events.append(time)
        return events
