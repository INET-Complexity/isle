#This script allows to launch an ensemble of simulations for different number of risks models.
#It can be run locally if no argument is passed when called from the terminal.
#It can be run in the cloud if it is passed as argument the server that will be used.
import sys
import random
import os
import math
import copy
import scipy.stats
import start
import logger
import isleconfig
from distributiontruncated import TruncatedDistWrapper
from setup import SetupSim
from sandman2.api import operation, Session



@operation
def agg(*outputs):
    # do nothing
   return outputs


def rake(hostname):

    jobs = []

    """Configuration of the ensemble"""

    replications = 70    #Number of replications to be carried out for each configuration. Usually one risk model, two risk models, three risk models, four risk models.

    model = start.main

    m = operation(model, include_modules = True)

    riskmodels = [1,2,3,4]   #The number of risk models that will be used.

    parameters = isleconfig.simulation_parameters

    """Setup of the simulations"""

    setup = SetupSim()   #Here the setup for the simulation is done.
    [general_rc_event_schedule, general_rc_event_damage, np_seeds, random_seeds] = setup.obtain_ensemble(replications)  #Since this script is used to carry out simulations in the cloud will usually have more than 1 replication..
    save_iter = isleconfig.simulation_parameters["max_time"] + 2    # never save simulation state in ensemble runs (resuming is impossible anyway)
    
    for i in riskmodels:   #In this loop the parameters, schedules and random seeds for every run are prepared. Different risk models will be run with the same schedule, damage size and random seed for a fair comparison.

        simulation_parameters = copy.copy(parameters)       #Here the parameters used for the simulation are loaded. Clone is needed otherwise all the runs will be carried out with the last number of thee loop.
        simulation_parameters["no_riskmodels"] = i      #Since we want to obtain ensembles for different number of risk models, we vary here the number of risks models.
        job = [m(simulation_parameters, general_rc_event_schedule[x], general_rc_event_damage[x], np_seeds[x], random_seeds[x], save_iter) for x in range(replications)]  #Here is assembled each job with the corresponding: simulation parameters, time events, damage events and seeds.
        jobs.append(job)    #All jobs are collected in the jobs list.

    store = []

    nums = {'1': 'one',
            '2': 'two',
            '3': 'three',
            '4': 'four',
            '5': 'five',
            '6': 'six',
            '7': 'seven',
            '8': 'eight',
            '9': 'nine'}

    """Here the jobs are submitted"""

    with Session(host=hostname, default_cb_to_stdout=True) as sess:
        counter = 1
        for job in jobs:     #If there are 4 risk models jobs will be a list with 4 elements.
            result = sess.submit(job)
            
            """Recreate logger object and save as open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_history_logs.dat"""
            L = logger.Logger()

            
            """These are the files created to collect the results"""
            wfiles = []
            prefixes = (
                "_cash.dat _excess_capital.dat _profitslosses.dat _contracts.dat "
                "_operational.dat _reincash.dat _reinexcess_capital.dat "
                "_reinprofitslosses.dat _reincontracts.dat _reinoperational.dat "
                "_total_catbondsoperational.dat _premium.dat _reinpremium.dat "
                "_cumulative_bankruptcies.dat _cumulative_market_exits "
                "_cumulative_unrecovered_claims.dat _cumulative_claims.dat"
            ).split(' ')
            for prefix in prefixes:
                wfiles.append(open(os.getcwd() + "/data/" + str(nums[str(counter)]) + prefix, "w"))

            wfiles.append(open(os.getcwd() + "/data/record_" + str(nums[str(counter)]) + "_insurance_firms_cash.dat", "w"))
            wfiles.append(open(os.getcwd() + "/data/record_" + str(nums[str(counter)]) + "_reinsurance_firms_cash.dat", "w"))
            wfiles.append(open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_market_diffvar.dat", "w"))
            for prefix in ["_rc_schedule.dat", "_rc_damage.dat", "_no_riskmodels.dat"]:
                wfiles.append(open(os.getcwd() + "/data/" + str(counter) + prefix, "w"))


            """Here the results of the simulations (typically run in the cloud) are collected"""

            for i in range(len(job)):

                directory = os.getcwd() + "/data"

                try: #Here it is checked whether the directory to collect the results exists or not. If not it is created.

                    os.stat(directory)
                except:
                    os.mkdir(directory)

                L.restore_logger_object(result[i])
                L.save_log(True)

                for ii in range(23):
                    wfiles[ii].write(str(result[i][ii]) + "\n")


            """Once the data is stored in disk the files are closed"""
            for wfile in wfiles:
                wfile.close()
            del wfiles[:]

            counter =counter + 1


if __name__ == '__main__':
    host = None
    if len(sys.argv) > 1:
        host = sys.argv[1]     #The server is passed as an argument.
    rake(host)
