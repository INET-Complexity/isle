#!/usr/bin/env python
# Created by Thomas French
#
# Copyright (c) 2017 Sandtable Ltd. All rights reserved.
import sys
import random
import os
import math
import scipy.stats

from sandman2.api import operation, Session

import start

@operation
def agg(*outputs):
    # do nothing
   return outputs


def rake(hostname):

    replications = 4

    model = start.main

    m = operation(model, include_modules = True)

    # replications

    riskmodels = [1,2,3,4]

    jobs = []

    general_rc_event_schedule = []
    seeds = []

    for z in range(replications):
        seeds.append(random.randint(0, 2**32-1))

    print(seeds)


    for i in riskmodels:

        simulation_parameters={"no_categories": 4,
                       "no_insurancefirms": 20,
                       "no_reinsurancefirms": 4,
                       "no_riskmodels": i,
                       "riskmodel_inaccuracy_parameter": 4, # values >=1; inaccuracy higher with higher values
                       "riskmodel_margin_of_safety": 2, # values >=1; factor of additional liquidity beyond value at risk
                       "value_at_risk_tail_probability": 0.005, # values <1, >0, usually close to 0; tail probability at which the value at risk is taken by the risk models
                       "norm_profit_markup": 0.15,
                       "rein_norm_profit_markup": 0.15,
                       "dividend_share_of_profits": 0.5,
                       "mean_contract_runtime": 36,
                       "contract_runtime_halfspread": 10,
                       "default_contract_payment_period": 12,
                       "max_time": 500,
                       "money_supply": 2000000000,
                       "event_time_mean_separation": 100 / 3.,
                       "expire_immediately": False,
                       "risk_factors_present": False,
                       "risk_factor_lower_bound": 0.4,
                       "risk_factor_upper_bound": 0.6,
                       "initial_acceptance_threshold": 0.5,
                       "acceptance_threshold_friction": 0.9,
                       "insurance_firm_market_entry_probability": 0.3,#0.02,
                       "reinsurance_firm_market_entry_probability": 0.1,#0.004,
                       "simulation_reinsurance_type": 'non-proportional',
                       "default_non-proportional_reinsurance_deductible": 0.2,
                       "default_non-proportional_reinsurance_excess": 1.0,
                       "default_non-proportional_reinsurance_premium_share": 0.2,
                       "static_non-proportional_reinsurance_levels": False,
                       "catbonds_off": True,
                       "reinsurance_off": False,
                       "capacity_target_decrement_threshold": 1.8,
                       "capacity_target_increment_threshold": 1.2,
                       "capacity_target_decrement_factor": 24/25.,
                       "capacity_target_increment_factor": 25/24.,
                       "insurance_reinsurance_levels_lower_bound": 0.1,
                       "insurance_reinsurance_levels_upper_bound": 0.15,
                       "reinsurance_reinsurance_levels_lower_bound": 0.15,
                       "reinsurance_reinsurance_levels_upper_bound": 0.20,
                       "initial_agent_cash": 80000,
                       "initial_reinagent_cash": 800000,
                       "interest_rate": 0.002,
                       "reinsurance_limit": 0.1,
                       "upper_price_limit": 1.2,
                       "lower_price_limit": 0,
                       "no_risks": 20000}


        if not general_rc_event_schedule:
            cat_separation_distribution = scipy.stats.expon(0, simulation_parameters["event_time_mean_separation"])

            for i in range(replications):
                rc_event_schedule = []
                for j in range(simulation_parameters["no_categories"]):
                    event_schedule = []
                    total = 0
                    while (total < simulation_parameters["max_time"]):
                        separation_time = cat_separation_distribution.rvs()
                        total += int(math.ceil(separation_time))
                        if total < simulation_parameters["max_time"]:
                            event_schedule.append(total)
                    rc_event_schedule.append(event_schedule)
                general_rc_event_schedule.append(rc_event_schedule)

            print(general_rc_event_schedule)

        job = [m(simulation_parameters,general_rc_event_schedule[x],seeds[x]) for x in range(replications)]
        print(len(general_rc_event_schedule))
        jobs.append(job)

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

    with Session(host=hostname, default_cb_to_stdout=True) as sess:
        counter = 1
        for job in jobs:
            result = sess.submit(job)

            wfile_0 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_cash.dat", "w")
            wfile_1 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_contracts.dat", "w")
            wfile_2 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_operational.dat", "w")
            wfile_3 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_reincash.dat", "w")
            wfile_4 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_reincontracts.dat", "w")
            wfile_5 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_reinoperational.dat", "w")
            wfile_6 = open(os.getcwd() + "/data/" + str(nums[str(counter)]) + "_premium.dat", "w")
            wfile_7 = open(os.getcwd() + "/data/" + str(counter) + "_rc_schedule.dat", "w")


            for i in range(len(job)):
                directory = os.getcwd() + "/data"
                try:
                    os.stat(directory)
                except:
                    os.mkdir(directory)

                wfile_0.write(str(result[i][0]) + "\n")
                wfile_1.write(str(result[i][1]) + "\n")
                wfile_2.write(str(result[i][2]) + "\n")
                wfile_3.write(str(result[i][3]) + "\n")
                wfile_4.write(str(result[i][4]) + "\n")
                wfile_5.write(str(result[i][5]) + "\n")
                wfile_6.write(str(result[i][6]) + "\n")
                wfile_7.write(str(result[i][7]) + "\n")


            wfile_0.close()
            wfile_1.close()
            wfile_2.close()
            wfile_3.close()
            wfile_4.close()
            wfile_5.close()
            wfile_6.close()
            wfile_7.close()


            counter =counter + 1


    print(store)


if __name__ == '__main__':
    host = None
    if len(sys.argv) > 1:
        host = sys.argv[1]
    rake(host)
