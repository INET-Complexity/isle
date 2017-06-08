
#import 

class RiskCategory():
    def __init__(self, eventDist=scipy.stats.expon(0, 100./3.), time, max_runtime):
        self.eventDist = eventDist
        self.eventTimeList = self.populateEventList(max_runtime)
    
    def populateEventList(self, time, max_runtime):
        events = []
        while (time < max_runtime):
            time += self.eventDist.rvs()
            if time < max_runtime:
                events.append(time)
        return events
