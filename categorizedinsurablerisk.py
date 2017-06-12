
import scipy.stats
import random

from insurablerisk import InsurableRisk
from riskcategory import RiskCategory
import auxfunctions

class CategorizedInsurableRisk(InsurableRisk):
    def __init__(self, time, max_runtime, risk_category_list, category=None, time_correlation_weight=.5, ):
        super(CategorizedInsurableRisk, self).__init__(None, None, None, scipy.stats.expon(0, 100./1.), scipy.stats.pareto(2., 0., 10.))
        if category is not None:
            if isinstance(category, int):
                self.category = risk_category_list[category]
            else:
                self.category = category
        else:
            self.category = random.choice(risk_category_list)
        assert auxfunctions.compare_rv_objects(self.eventDist, self.category.eventDist)
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
        g_events_include = scipy.stats.bernoulli(self.time_correlation_weight).rvs(len(self.category.eventTimeList))
        for i in range(len(i_events_include)):
            if i_events_include[i]:
                events.append(ievents[i])
        for i in range(len(g_events_include)):
            if g_events_include[i]:
                events.append(self.category.eventTimeList[i])
        events.sort()
        return events
        

    ## does not need to be overridden
    #def getSizeOfEvent(self):
    #    return self.eventSizeDist.rvs()
