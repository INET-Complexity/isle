"""Risk Category module for ISLE.
   Defines RiskCategory class to handle grouped risk event correlation.
   
   Created by Torsten Heinrich."""

import scipy.stats

# RiskCategory class
class RiskCategory():
    def __init__(self, time, max_runtime, eventDist=scipy.stats.expon(0, 100./3.), \
                                    share_of_category_scale_perils = None, share_selection_bernoulli_dist = None):
        """Constructor method. Requires positional arguments:
             time (int):        present simulation time (iteration number)
             max_runtime (int): end of the simulation
           Optional argument:
             eventDist (scipy.stats rv frozen distribution): event sepatation time distribution, defaults to exponential
             share_of_category_scale_perils (float >=0, <=1 or None): share of category-scale perils
             share_selection_bernoulli_dist (scipy.stats rv frozen distribution of None): bernoulli distribution for 
                                                                                                    eventschedule mixing.
           Returns self.
           Method creates category and populates category event schedule."""
        self.share_of_category_scale_perils = share_of_category_scale_perils
        self.eventDist = eventDist                                      # separation time distribution
        self.eventTimeList = self.populateEventList(time, max_runtime)  # event schedule
        if share_selection_bernoulli_dist is not None:
            bernoulli_rv = share_selection_bernoulli_dist.rvs(len(self.eventTimeList))
            reducedEventTimeList = []
            for i in range(len(bernoulli_rv)):
                if bernoulli_rv[i]:
                    reducedEventTimeList.append(self.eventTimeList[i])
            self.eventTimeList = reducedEventTimeList
        #print(self.eventTimeList)
    
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
