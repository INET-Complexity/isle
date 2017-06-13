
import scipy.stats
import random

from insurablerisk import InsurableRisk
from riskcategory import RiskCategory
import auxfunctions

class CategorizedInsurableRisk(InsurableRisk):
    def __init__(self, time, max_runtime, risk_category_list, category=None, time_correlation_weight=.5, ):
        super(CategorizedInsurableRisk, self).__init__(None, None, None, scipy.stats.expon(0, 100./1.), scipy.stats.pareto(2., 0., 10.))
        self.category = []
        for i in range(len(risk_category_list)):
            current_rcl = risk_category_list[i]
            current_category = None if (category is None) else category[i]
            #if category is not None:
            #    current_category = category[i]
            #else:
            #    current_category = None
            self.category.append(None)
            if current_category is not None:
                if isinstance(current_category, int):
                    self.category[i] = current_rcl[current_category]
                else:
                    self.category[i] = current_category
            else:
                self.category[i] = random.choice(current_rcl)
            assert auxfunctions.compare_rv_objects(self.eventDist, self.category[i].eventDist)
        self.time_correlation_weight = time_correlation_weight
        self.eventSchedule = self.populateEventSchedule(time, max_runtime)
    
    def schedule_next_event(self, time):
        i = 0
        while (len(self.eventSchedule) > i and self.eventSchedule[i] < time):
            i += 1
        if len(self.eventSchedule) > i:
            return self.eventSchedule[i], self
        else:
            return None, None		# TODO: Will this cause type errors somewhere?

    def populateEventSchedule(self, time, max_runtime):
        ievents = []
        events = []
        while (time < max_runtime):
            time += self.eventDist.rvs()
            if time < max_runtime:
                ievents.append(time)
        i_events_include = scipy.stats.bernoulli(1-self.time_correlation_weight).rvs(len(ievents))
        g_events_include = []
        cat_share =  1. / len(self.category)
        for catd in range(len(self.category)):
            g_events_include.append(scipy.stats.bernoulli(self.time_correlation_weight*cat_share).rvs(len(self.category[catd].eventTimeList)))
        for i in range(len(i_events_include)):
            if i_events_include[i]:
                events.append(ievents[i])
        for catd in range(len(self.category)):
            for i in range(len(g_events_include[catd])):
                if g_events_include[catd][i]:
                    events.append(self.category[catd].eventTimeList[i])
        events.sort()
        return events
        

    ## does not need to be overridden
    #def getSizeOfEvent(self):
    #    return self.eventSizeDist.rvs()
