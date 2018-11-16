


class Logger():
    def __init__(self):
        
                self.history_logs = {}

        self.history_logs['total_cash'] = []
        self.history_logs['total_excess_capital'] = []
        self.history_logs['total_profitslosses'] = []
        self.history_logs['total_contracts'] = []
        self.history_logs['total_operational'] = []
        # individual insurance firms
        self.history_logs['individual_contracts'] = []
        
        # sum reinsurance firms
        self.history_logs['total_reincash'] = []
        self.history_logs['total_reinexcess_capital'] = []
        self.history_logs['total_reinprofitslosses'] = []
        self.history_logs['total_reincontracts'] = []
        self.history_logs['total_reinoperational'] = []
        
        self.history_logs['cumulative_bankruptcies'] = []
        self.history_logs['cumulative_claims'] = []          #Here are stored the total cumulative claims received by the whole insurance sector until a certain time.
        self.history_logs['cumulative_unrecovered_claims'] = []

        self.history_logs['total_catbondsoperational'] = []

        self.history_logs['market_premium'] = []
        self.history_logs['market_reinpremium'] = []
        self.history_logs['market_diffvar'] = []
        
        # lists to contain agent-level data
        self.history_logs['insurance_firms_cash'] = []
        self.history_logs['reinsurance_firms_cash'] = []

        self.insurance_models_counter = np.zeros(self.simulation_parameters["no_categories"])
        self.reinsurance_models_counter = np.zeros(self.simulation_parameters["no_categories"])        
    
    
    def save_data(self):
        # # collect data
        # total_cash_no = sum([insurancefirm.cash for insurancefirm in self.insurancefirms])
        # total_excess_capital = sum([insurancefirm.get_excess_capital() for insurancefirm in self.insurancefirms])
        # total_profitslosses =  sum([insurancefirm.get_profitslosses() for insurancefirm in self.insurancefirms])
        # total_contracts_no = sum([len(insurancefirm.underwritten_contracts) for insurancefirm in self.insurancefirms])
        # total_reincash_no = sum([reinsurancefirm.cash for reinsurancefirm in self.reinsurancefirms])
        # total_reinexcess_capital = sum([reinsurancefirm.get_excess_capital() for reinsurancefirm in self.reinsurancefirms])
        # total_reinprofitslosses =  sum([reinsurancefirm.get_profitslosses() for reinsurancefirm in self.reinsurancefirms])
        # total_reincontracts_no = sum([len(reinsurancefirm.underwritten_contracts) for reinsurancefirm in self.reinsurancefirms])
        # operational_no = sum([insurancefirm.operational for insurancefirm in self.insurancefirms])
        # reinoperational_no = sum([reinsurancefirm.operational for reinsurancefirm in self.reinsurancefirms])
        # catbondsoperational_no = sum([catbond.operational for catbond in self.catbonds])
        
        # agent-level data
        
        # insurance_firms = [(insurancefirm.cash,insurancefirm.id,insurancefirm.operational) for insurancefirm in self.insurancefirms]
        # reinsurance_firms = [(reinsurancefirm.cash,reinsurancefirm.id,reinsurancefirm.operational) for reinsurancefirm in self.reinsurancefirms]
        

        self.history_logs['total_cash'].append(total_cash_no)
        self.history_logs['total_excess_capital'].append(total_excess_capital)
        self.history_logs['total_profitslosses'].append(total_profitslosses)
        self.history_logs['total_contracts'].append(total_contracts_no)
        self.history_logs['total_operational'].append(operational_no)
        self.history_logs['total_reincash'].append(total_reincash_no)
        self.history_logs['total_reinexcess_capital'].append(total_reinexcess_capital)
        self.history_logs['total_reinprofitslosses'].append(total_reinprofitslosses)
        self.history_logs['total_reincontracts'].append(total_reincontracts_no)
        self.history_logs['total_reinoperational'].append(reinoperational_no)
        self.history_logs['total_catbondsoperational'].append(catbondsoperational_no)
        self.history_logs['market_premium'].append(self.market_premium)
        self.history_logs['market_reinpremium'].append(self.reinsurance_market_premium)
        self.history_logs['cumulative_bankruptcies'].append(self.cumulative_bankruptcies)
        self.history_logs['cumulative_unrecovered_claims'].append(self.cumulative_unrecovered_claims)
        self.history_logs['cumulative_claims'].append(self.cumulative_claims)    #Log the cumulative claims received so far.
        
        # agent-level data
        self.history_logs['insurance_firms_cash'].append(insurance_firms)
        self.history_logs['reinsurance_firms_cash'].append(reinsurance_firms)
        self.log_vars()
        
        # individual_contracts_no = [len(insurancefirm.underwritten_contracts) for insurancefirm in self.insurancefirms]
        for i in range(len(individual_contracts_no)):
            try:
                self.history_logs['individual_contracts'][i].append(individual_contracts_no[i])
            except:
                print(sys.exc_info())
                pdb.set_trace()


    def obtain_log(self):   #This function allows to return in a list all the data generated by the model. There is no other way to transfer it back from the cloud.

        log = []

        log.append(self.history_logs['total_cash'])
        log.append(self.history_logs['total_excess_capital'])
        log.append(self.history_logs['total_profitslosses'])
        log.append(self.history_logs['total_contracts'])
        log.append(self.history_logs['total_operational'])
        log.append(self.history_logs['total_reincash'])
        log.append(self.history_logs['total_reinexcess_capital'])
        log.append(self.history_logs['total_reinprofitslosses'])
        log.append(self.history_logs['total_reincontracts'])
        log.append(self.history_logs['total_reinoperational'])
        log.append(self.history_logs['total_catbondsoperational'])
        log.append(self.history_logs['market_premium'])
        log.append(self.history_logs['market_reinpremium'])
        log.append(self.history_logs['cumulative_bankruptcies'])
        log.append(self.history_logs['cumulative_unrecovered_claims'])
        log.append(self.history_logs['cumulative_claims'])
        log.append(self.history_logs['insurance_firms_cash'])
        log.append(self.history_logs['reinsurance_firms_cash'])
        log.append(self.history_logs['market_diffvar'])
        log.append(self.rc_event_schedule_initial)
        log.append(self.rc_event_damage_initial)


        return log

    def log(self):
        if self.background_run:
            to_log = self.replication_log_prepare()
        else:
            to_log = self.single_log_prepare()
        
        #TODO: use with file_handle as open structure 
        for filename, data, operation_character in to_log:
            with open(filename, operation_character) as wfile:
                wfile.write(str(data) + "\n")
                wfile.close()
    
    def replication_log_prepare(self):
        filename_prefix = {1: "one", 2: "two", 3: "three", 4: "four"}
        fpf = filename_prefix[self.number_riskmodels]
        to_log = []
        to_log.append(("data/" + fpf + "_history_logs.dat", self.history_logs, "a"))
        return to_log
      
    def single_log_prepare(self):
        to_log = []
        to_log.append(("data/history_logs.dat", self.history_logs, "w"))
        return to_log

    def log_vars(self):

        varsfirms = []
        for firm in self.insurancefirms:                            #TODO
            if firm.operational:
                varsfirms.append(firm.var_counter_per_risk)
        totalina = sum(varsfirms)

        varsfirms = []
        for firm in self.insurancefirms:                            #TODO
            if firm.operational:
                varsfirms.append(1)
        totalreal = sum(varsfirms)

        varsreinfirms = []
        for reinfirm in self.reinsurancefirms:                      #TODO
            if reinfirm.operational:
                varsreinfirms.append(reinfirm.var_counter_per_risk)
        totalina = totalina + sum(varsreinfirms)

        varsreinfirms = []
        for reinfirm in self.reinsurancefirms:                      #TODO
            if reinfirm.operational:
                varsreinfirms.append(1)
        totalreal = totalreal + sum(varsreinfirms)

        totaldiff = totalina - totalreal
        self.history_logs['market_diffvar'].append(totaldiff)
