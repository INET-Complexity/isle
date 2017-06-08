
import scipy.stats

class RiskCategory():
    def __init__(self, time, max_runtime, eventDist=scipy.stats.expon(0, 100./3.)):
        self.eventDist = eventDist
        self.eventTimeList = self.populateEventList(max_runtime)
    
    def populateEventList(self, time, max_runtime):
        events = []
        while (time < max_runtime):
            time += self.eventDist.rvs()
            if time < max_runtime:
                events.append(time)
        return events
