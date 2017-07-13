"""
 Categorized insurable risk (risk with grouped correlation implemented)  class for ISLE.
 
 Created by Torsten Heinrich.
"""

# import general python modules
import scipy.stats
import random
import pdb

# import ISLE modules
from insurablerisk import InsurableRisk
from riskcategory import RiskCategory
import auxfunctions

# CategorizedInsurableRisk class (inherits from InsurableRisk)
class CategorizedInsurableRisk(InsurableRisk):
    def __init__(self, 
                 time, 
                 max_runtime, 
                 risk_category_list, 
                 category=None, 
                 time_correlation_weight=.5, 
                 eventDist = scipy.stats.expon(0, 100./3.), 
                 eventSizeDist = scipy.stats.pareto(2., 0., 10.),
                 bernoulliDistCategory = None,
                 bernoulliDistIndividual = None):
        """Constructor method. Positional arguments:
             time (int):                        present simulation time (iteration number)
             max_runtime (int):                 end of the simulation
             risk_category_list (nested list):  risk category affiliations of the insured risk
           Optional arguments:
             category (nested list of int or pointer): predefined risk category affiliations (random if not given)
             time_correlation_weight (float >=0 <=1): share of correlated risk events   #TODO: implement coherent naming
             eventDist (rv frozen distribution): damage event separation time distribution
             eventSizeDist (rv frozen distribution): damage size distribution
             bernoulliDistCategory (rv frozen distribution): bernoulli distribution for eventschedule mixing.
             bernoulliDistIndividual (rv frozen distribution): bernoulli distribution for eventschedule mixing.
        """
        # Call parent constructor
        super(CategorizedInsurableRisk, self).__init__(None, None, None, eventDist, eventSizeDist)
        
        # Record category affiliation: in this setting exactly one category in two dimensions 
        #                                                                       TODO: implement in a more generic way
        self.category = []
        self.category_id = []
        for i in range(len(risk_category_list)):
            #current_rcl = risk_category_list[i]
            #current_category = None if (category is None) else category[i]
            ##if category is not None:
            ##    current_category = category[i]
            ##else:
            ##    current_category = None
            self.category.append(None)
            self.category_id.append(None)
            #if current_category is not None:
            #    if isinstance(current_category, int):
            #        self.category[i] = current_rcl[current_category]
            #        self.category_id[i] = current_category
            #    else:
            #        self.category[i] = current_category
            #        self.category_id[i] = risk_category_list.index(current_category)
            #else:
            #    self.category_id[i] = random.choice(range(len(current_rcl)))
            #    self.category[i] = current_rcl[self.category_id[i]]
        catd = random.choice(range(len(risk_category_list)))
        current_rcl = risk_category_list[catd]
        self.category_id[catd] = random.choice(range(len(current_rcl)))
        self.category[catd] = current_rcl[self.category_id[catd]]
        
        """Assert that svent separation time distributions are the same for risk and category (otherwise marginal 
                                                                          distributions are not identical any more."""
        assert auxfunctions.compare_rv_objects(self.eventDist, self.category[catd].eventDist)
        
        # Record remaining properties
        self.time_correlation_weight = time_correlation_weight
        self.bernoulliDistCategory = bernoulliDistCategory
        self.bernoulliDistIndividual = bernoulliDistIndividual
        self.eventSchedule = self.populateEventSchedule(time, max_runtime)
    
    def schedule_next_event(self, time):
        """Method for scheduling the next event from the event schedule if any. Positional argument:
             time (int): current time
           Returns (tuple (float, InsurableRisk object) or tuple (None, None)): next event time, self or None, None"""
        i = 0
        while (len(self.eventSchedule) > i and self.eventSchedule[i] < time):
            i += 1
        if len(self.eventSchedule) > i:
            return self.eventSchedule[i], self
        else:
            return None, None		# TODO: Will this cause type errors somewhere? -> no.

    #@profile
    def populateEventSchedule(self, time, max_runtime):
        """Method to create event schedule by: 
              1. Creating individual event schedule by drawing event separation times from the eventDist until the 
                 scheduled simulation end time is reached. 
              2. Mixing induvidual and category event schedules
           Required positional arguments:
             time (int):        present simulation time (iteration number)
             max_runtime (int): end of the simulation
           Returns event schedule (list of float). 
           """
        # Prepare lists
        ievents = []    # unmixed individual event schedule
        events = []     # final (mixed) individual event schedule
        
        # Create unmixed event schedule
        while (time < max_runtime):
            time += self.eventDist.rvs()
            if time < max_runtime:
                ievents.append(time)
        #pdb.set_trace()
        
        # Test for supplied Bernoulli distributions for mixing, create them if not supplied.
        if self.bernoulliDistIndividual is None:
            i_events_include = scipy.stats.bernoulli(1-self.time_correlation_weight).rvs(len(ievents))
        else:
            i_events_include = self.bernoulliDistIndividual.rvs(len(ievents))
        
        # Draw Bernoulli random variates for mixing
        g_events_include = []
        #cat_share =  1. / len(self.category)
        cat_share =  1.
        for catd in range(len(self.category)):
            if self.category[catd] is not None:
                if self.bernoulliDistCategory is None:
                    bernoulli_rv = scipy.stats.bernoulli(self.time_correlation_weight*cat_share).rvs(len(self.category[catd].eventTimeList))
                else:
                    bernoulli_rv = self.bernoulliDistCategory.rvs(len(self.category[catd].eventTimeList))
                g_events_include.append(bernoulli_rv)
            else:
                g_events_include.append(None)      
        
        # Mix distributions using Bernoulli random variated drawn above
        for i in range(len(i_events_include)):
            if i_events_include[i]:
                events.append(ievents[i])
        for catd in range(len(self.category)):
            if g_events_include[catd] is not None:
                for i in range(len(g_events_include[catd])):
                    if g_events_include[catd][i]:
                        events.append(self.category[catd].eventTimeList[i])
        events.sort()
        
        # Return final event schedule
        return events
