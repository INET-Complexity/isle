
from insurancesimulation import InsuranceSimulation
import pdb, sys

class InsuranceSimulation_One(InsuranceSimulation):

    def replication_log_prepare(self):
        to_log = []
        to_log.append(("data/one_operational.dat", self.history_total_operational, "a"))
        to_log.append(("data/one_contracts.dat", self.history_total_contracts, "a"))
        to_log.append(("data/one_cash.dat", self.history_total_cash, "a"))
        to_log.append(("data/one_reinoperational.dat", self.history_total_reinoperational, "a"))
        to_log.append(("data/one_reincontracts.dat", self.history_total_reincontracts, "a"))
        to_log.append(("data/one_reincash.dat", self.history_total_reincash, "a"))
        return to_log

    def replication_log_z(self):
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
