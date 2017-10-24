
from insurancesimulation import InsuranceSimulation
import pdb, sys

class InsuranceSimulation_One(InsuranceSimulation):

    def replication_log(self):
        wfile = open("data/one_operational.dat","a")
        wfile.write(str(self.history_total_operational)+"\n")
        wfile.close()
        wfile = open("data/one_contracts.dat","a")
        wfile.write(str(self.history_total_contracts)+"\n")
        wfile.close()
        wfile = open("data/one_cash.dat","a")
        wfile.write(str(self.history_total_cash)+"\n")
        wfile.close()

    def setup_risk_categories_caller(self):
        if self.background_run:
            rfile = open("data/rc_event_schedule.dat","r")
            found = False
            for i, line in enumerate(rfile):
                print(i, self.replic_ID)
                if i == self.replic_ID:
                    self.rc_event_schedule = eval(line)
                    found = True
            rfile.close()
            assert found, "rc event schedule for current replication ID number {0:d} not found in data file. Exiting.".format(self.replic_ID)
        else:
            self.setup_risk_categories()    

# main entry point
if __name__ == "__main__":
    arg = None
    if len(sys.argv) > 1:
        arg = int(sys.argv[1])
    S = InsuranceSimulation_One(replic_ID = arg, override_no_riskmodels = 1)
    S.run()
