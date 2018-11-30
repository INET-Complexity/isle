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

            wfile_0 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_cash.dat", "w")
            wfile_1 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_excess_capital.dat", "w")
            wfile_2 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_profitslosses.dat", "w")
            wfile_3 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_contracts.dat", "w")
            wfile_4 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_operational.dat", "w")
            wfile_5 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_reincash.dat", "w")
            wfile_6 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_reinexcess_capital.dat", "w")
            wfile_7 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_reinprofitslosses.dat", "w")
            wfile_8 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_reincontracts.dat", "w")
            wfile_9 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_reinoperational.dat", "w")
            wfile_10 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_total_catbondsoperational.dat", "w")
            wfile_11 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_premium.dat", "w")
            wfile_12 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_reinpremium.dat", "w")
            wfile_13 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_cumulative_bankruptcies.dat", "w")
            wfile_14 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_cumulative_market_exits", "w")
            wfile_15 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_cumulative_unrecovered_claims.dat", "w")
            wfile_16 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_cumulative_claims.dat", "w")
            wfile_17 = open(os.getcwd() + "/data/record_" + str(nums[str(counter)]) + "_insurance_firms_cash.dat", "w")
            wfile_18 = open(os.getcwd() + "/data/record_" + str(nums[str(counter)]) + "_reinsurance_firms_cash.dat", "w")
            wfile_19 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_market_diffvar.dat", "w")
            wfile_20 = open(os.getcwd() + "/data/" + str(counter) + "_rc_schedule.dat", "w")
            wfile_21 = open(os.getcwd() + "/data/" + str(counter) + "_rc_damage.dat", "w")
            wfile_22 = open(os.getcwd() + "/data/" + str(counter) + "_no_riskmodels.dat", "w")


            """Here the results of the simulations (typically run in the cloud) are collected"""

            for i in range(len(job)):

                directory = os.getcwd() + "/data"

                try: #Here it is checked whether the directory to collect the results exists or not. If not it is created.

                    os.stat(directory)
                except:
                    os.mkdir(directory)

                L.restore_logger_object(result[i])
                L.save_log(True)

                wfile_0.write(str(result[i][0]) + "\n")
                wfile_1.write(str(result[i][1]) + "\n")
                wfile_2.write(str(result[i][2]) + "\n")
                wfile_3.write(str(result[i][3]) + "\n")
                wfile_4.write(str(result[i][4]) + "\n")
                wfile_5.write(str(result[i][5]) + "\n")
                wfile_6.write(str(result[i][6]) + "\n")
                wfile_7.write(str(result[i][7]) + "\n")
                wfile_8.write(str(result[i][8]) + "\n")
                wfile_9.write(str(result[i][9]) + "\n")
                wfile_10.write(str(result[i][10]) + "\n")
                wfile_11.write(str(result[i][11]) + "\n")
                wfile_12.write(str(result[i][12]) + "\n")
                wfile_13.write(str(result[i][13]) + "\n")
                wfile_14.write(str(result[i][14]) + "\n")
                wfile_15.write(str(result[i][15]) + "\n")
                wfile_16.write(str(result[i][16]) + "\n")
                wfile_17.write(str(result[i][17]) + "\n")
                wfile_18.write(str(result[i][18]) + "\n")
                wfile_19.write(str(result[i][19]) + "\n")
                wfile_20.write(str(result[i][20]) + "\n")
                wfile_21.write(str(result[i][21]) + "\n")
                wfile_22.write(str(result[i][22]) + "\n")





            """Once the data is stored in disk the files are closed"""

            wfile_0.close()
            wfile_1.close()
            wfile_2.close()
            wfile_3.close()
            wfile_4.close()
            wfile_5.close()
            wfile_6.close()
            wfile_7.close()
            wfile_8.close()
            wfile_9.close()
            wfile_10.close()
            wfile_11.close()
            wfile_12.close()
            wfile_13.close()
            wfile_14.close()
            wfile_15.close()
            wfile_16.close()
            wfile_17.close()
            wfile_18.close()
            wfile_19.close()
            wfile_20.close()
            wfile_21.close()
            wfile_22.close()


            counter =counter + 1


if __name__ == '__main__':
    host = None
    if len(sys.argv) > 1:
        host = sys.argv[1]     #The server is passed as an argument.
    rake(host)
