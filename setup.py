"""Class to set up event schedules for reproducible simulation replications.
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

import argparse
import scipy.stats
import pickle
import math
import os
import isleconfig
from distributiontruncated import TruncatedDistWrapper

class SetupSim():

    def __init__(self):

        self.simulation_parameters = isleconfig.simulation_parameters

        """parameters of the simulation setup"""
        self.max_time = self.simulation_parameters["max_time"]
        self.no_categories = self.simulation_parameters["no_categories"]


        """set distribution"""
        self.non_truncated = scipy.stats.pareto(b=2, loc=0, scale=0.25)    #It is assumed that the damages of the catastrophes are drawn from a truncated Pareto distribution.
        self.damage_distribution = TruncatedDistWrapper(lower_bound=0.25, upper_bound=1., dist=self.non_truncated)
        self.cat_separation_distribution = scipy.stats.expon(0, self.simulation_parameters["event_time_mean_separation"])  #It is assumed that the time between catastrophes is exponentially distributed.

        """"random seeds"""
        self.np_seed = []
        self.random_seed = []
        self.general_rc_event_schedule = []
        self.general_rc_event_damage = []

    def schedule(self, replications):  #This method returns the lists of schedule times and damages for an ensemble of replications of the model. The argument (replications) is the number of replications.

        general_rc_event_schedule = []  #In this list will be stored the lists of schedule times of catastrophes for an ensemble of simulations of the model. ([[Schedule 1], [Schedule 2], [Schedule 3],...,[Schedule N]])
        general_rc_event_damage = []    #In this list will be stored the lists of schedule damages of catastrophes for an ensemble of simulations of the model. ([[Schedule 1], [Schedule 2], [Schedule 3],...,[Schedule N]])

        for i in range(replications):
            rc_event_schedule = []      #In this list will be stored the lists of times when there will be catastrophes for every category of the model during a single run. ([[times for C1],[times for C2],[times for C3],[times for C4]])
            rc_event_damage = []        #In this list will be stored the lists of catastrophe damages for every category of the model during a single run. ([[damages for C1],[damages for C2],[damages for C3],[damages for C4]])
            for j in range(self.no_categories):
                event_schedule = []       #In this list will be stored the times when there will be a catastrophe related to a particular category.
                event_damage = []        #In this list will be stored the damages of a catastrophe related to a particular category.
                total = 0
                while (total < self.max_time):
                    separation_time = self.cat_separation_distribution.rvs()
                    total += int(math.ceil(separation_time))
                    if total < self.max_time:
                        event_schedule.append(total)
                        event_damage.append(self.damage_distribution.rvs())
                rc_event_schedule.append(event_schedule)
                rc_event_damage.append(event_damage)

            self.general_rc_event_schedule.append(rc_event_schedule)
            self.general_rc_event_damage.append(rc_event_damage)

        return self.general_rc_event_schedule, self.general_rc_event_damage

    def seeds(self, replications):   #This method returns the seeds required for an ensemble of replications of the model. The argument (replications) is the number of replications.
        """draw random variates for random seeds"""
        for i in range(replications):
            np_seed, random_seed = scipy.stats.randint.rvs(0, 2**32 - 1, size=2)
            self.np_seed.append(np_seed)
            self.random_seed.append(random_seed)

        return self.np_seed, self.random_seed


    def store(self, replications):   #This method stores in a file the the schedules and random seeds required for an ensemble of replications of the model. The argument (replications) is the number of replications.
                                     #With the information stored it is possible to replicate the entire behavior of the ensemble at a later time.
        event_schedules = []

        for i in range(replications):

            """pack to dict"""
            d = {}
            d["np_seed"] = self.np_seed[i]
            d["random_seed"] = self.random_seed[i]
            d["event_times"] = self.general_rc_event_schedule[i]
            d["event_damages"] = self.general_rc_event_damage[i]
            d["num_categories"] = self.simulation_parameters["no_categories"]
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


    def obtain_ensemble(self, replications):  #This method returns all the information (schedules and seeds) required to run an ensemble of simulations of the model. Since it also stores the information in a file it will be possible to replicate the ensemble at a later time. The argument (replications) is the number of replications.
                                              #This method will be called either form ensemble.py or start.py
        [general_rc_event_schedule, general_rc_event_damage] = self.schedule(replications)

        [np_seeds, random_seeds] = self.seeds(replications)

        self.store(replications)

        return general_rc_event_schedule, general_rc_event_damage, np_seeds, random_seeds





    
