"""Script to set up event schedules for reproducible simulation replications. 
   Event schedule sets are written to files and include event schedules for every replication as dictionaries in a list.
   Every event schedule dictionary has:
      - event_times: list of list of int - iteration periods of risk events in each category
      - event_damages: list of list of float (0, 1) - damage as share of theoretically possible damage for each risk event
      - num_categories: int - number of risk categories 
      - np_seed: int - numpy module random seed
      - random_seed: int - random module random seed
   A simulation given event schedule dictionary d should be set up like so:
        assert isleconfig.simulation_parameters["no_categories"] == d["num_categories"]
        simulation.rc_event_schedule = d["event_times"]
        simulation.rc_event_damages = d["event_damages"]
        np.random.seed(d["np_seed"])
        random.random.seed(d["np_seed"])
    """

import scipy.stats
import argparse
import scipy.stats
import pickle
import math
import os

import isleconfig
from distributiontruncated import TruncatedDistWrapper


parser = argparse.ArgumentParser(description='Model the Insurance sector')
parser.add_argument("-r", "--replications", type=int, help="number of replications (default 300)")
args = parser.parse_args()


def setup_risk_event_schedule(num_replications = 300):
    """read parameters"""
    simulation_parameters = isleconfig.simulation_parameters
    
    """set distribution"""
    non_truncated = scipy.stats.pareto(b=2, loc=0, scale=0.25)
    damage_distribution = TruncatedDistWrapper(lower_bound=0.25, upper_bound=1., dist=non_truncated)
    cat_separation_distribution = scipy.stats.expon(0, simulation_parameters["event_time_mean_separation"])
    
    event_schedules = []
    
    for r in range(num_replications):
        """draw random variates for events"""
        event_times = []
        event_damages = []
        for i in range(simulation_parameters["no_categories"]):
            event_times_cat = []
            total = 0
            while (total < simulation_parameters["max_time"]):
                separation_time = cat_separation_distribution.rvs()
                total += int(math.ceil(separation_time))
                if total < simulation_parameters["max_time"]:
                    event_times_cat.append(total)
            event_times.append(event_times_cat)
            damages_cat = damage_distribution.rvs(size=len(event_times_cat))
            event_damages.append(damages_cat)
        
        """draw random variates for random seeds"""
        np_seed, random_seed = scipy.stats.randint.rvs(0, 2**32 - 1, size=2)    
        
        """pack to dict"""
        d = {}
        d["np_seed"] = np_seed    
        d["random_seed"] = random_seed    
        d["event_times"] = event_times    
        d["event_damages"] = event_damages    
        d["num_categories"] = simulation_parameters["no_categories"]
        event_schedules.append(d)
    
    """ ensure that logging directory exists"""
    if not os.path.isdir("data"):
        assert not os.path.exists("data"), "./data exists as regular file. This filename is required for the logging and event schedule directory"
        os.makedirs("data")

    """Save as both pickle and txt"""
    with open("./data/risk_event_schedules.pkl", "wb") as wfile:
        pickle.dump(event_schedules, wfile, protocol=pickle.HIGHEST_PROTOCOL)
        
    with open("./data/risk_event_schedules.txt", "w") as wfile:
        for rep_schedule in event_schedules:
            wfile.write(str(rep_schedule).replace("\n","").replace("array", "np.array").replace("uint32", "np.uint32") + "\n")

if __name__ == "__main__":
    if args.replications:
        setup_risk_event_schedule(args.replications) 
    else:
        setup_risk_event_schedule() 
    
