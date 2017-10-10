
from insurancesimulation import InsuranceSimulation
import pdb, sys

class InsuranceSimulation_One(InsuranceSimulation):
    def setup_risk_categories_caller(self):
        if self.background_run:
            rfile = open("data/rc_event_schedule.dat","r")
            for i, line in enumerate(rfile):
                if i == self.replic_ID:
                    self.rc_event_schedule = eval(line)
            rfile.close()
            
        else:
            self.setup_risk_categories()    

# main entry point
if __name__ == "__main__":
    arg = None
    if len(sys.argv) > 1:
        arg = int(sys.argv[1])
    S = InsuranceSimulation_One(replic_ID = arg, override_no_riskmodels = 1)
    S.run()
