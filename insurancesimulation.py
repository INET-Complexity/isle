from insurancefirm import InsuranceFirm
#from riskmodel import RiskModel
from reinsurancefirm import ReinsuranceFirm
from distributiontruncated import TruncatedDistWrapper
import numpy as np
import scipy.stats
import math
import sys, pdb
import isleconfig
import random
import copy
import logger

if isleconfig.show_network:
    import visualization_network

if isleconfig.use_abce:
    import abce
    #print("abce imported")
#else:
#    print("abce not imported")



class InsuranceSimulation():
    def __init__(self, override_no_riskmodels, replic_ID, simulation_parameters, rc_event_schedule, rc_event_damage):
        # override one-riskmodel case (this is to ensure all other parameters are truly identical for comparison runs)
        if override_no_riskmodels:
            simulation_parameters["no_riskmodels"] = override_no_riskmodels
        self.number_riskmodels = simulation_parameters["no_riskmodels"]
        
        # save parameters
        if (replic_ID is None) or (isleconfig.force_foreground):
            self.background_run = False 
        else:
            self.background_run = True
        self.replic_ID = replic_ID
        self.simulation_parameters = simulation_parameters

        # unpack parameters, set up environment (distributions etc.)
        
        # damage distribution
        # TODO: control damage distribution via parameters, not directly
        #self.damage_distribution = scipy.stats.uniform(loc=0, scale=1)
        non_truncated = scipy.stats.pareto(b=2, loc=0, scale=0.25)
        self.damage_distribution = TruncatedDistWrapper(lower_bound=0.25, upper_bound=1., dist=non_truncated)
        
        # remaining parameters
        self.catbonds_off = simulation_parameters["catbonds_off"]
        self.reinsurance_off = simulation_parameters["reinsurance_off"]
        self.cat_separation_distribution = scipy.stats.expon(0, simulation_parameters["event_time_mean_separation"])
        self.risk_factor_lower_bound = simulation_parameters["risk_factor_lower_bound"]
        self.risk_factor_spread = simulation_parameters["risk_factor_upper_bound"] - simulation_parameters["risk_factor_lower_bound"]
        self.risk_factor_distribution = scipy.stats.uniform(loc=self.risk_factor_lower_bound, scale=self.risk_factor_spread)
        if not simulation_parameters["risk_factors_present"]:
            self.risk_factor_distribution = scipy.stats.uniform(loc=1.0, scale=0)
        #self.risk_value_distribution = scipy.stats.uniform(loc=100, scale=9900)
        self.risk_value_distribution = scipy.stats.uniform(loc=1000, scale=0)

        risk_factor_mean = self.risk_factor_distribution.mean()
        if np.isnan(risk_factor_mean):     # unfortunately scipy.stats.mean is not well-defined if scale = 0
            risk_factor_mean = self.risk_factor_distribution.rvs()

        # set initial market price (normalized, i.e. must be multiplied by value or excess-deductible)
        if self.simulation_parameters["expire_immediately"]:
            assert self.cat_separation_distribution.dist.name == "expon"
            expected_damage_frequency = 1 - scipy.stats.poisson(1 / self.simulation_parameters["event_time_mean_separation"] * \
                                                                self.simulation_parameters["mean_contract_runtime"]).pmf(0)
        else:
            expected_damage_frequency = self.simulation_parameters["mean_contract_runtime"] / \
                                                        self.cat_separation_distribution.mean()
        self.norm_premium = expected_damage_frequency * self.damage_distribution.mean() * \
                        risk_factor_mean * \
                        (1 + self.simulation_parameters["norm_profit_markup"])

        self.market_premium = self.norm_premium
        self.reinsurance_market_premium = self.market_premium       # TODO: is this problematic as initial value? (later it is recomputed in every iteration)
        self.total_no_risks = simulation_parameters["no_risks"]

        # set up monetary system (should instead be with the customers, if customers are modeled explicitly)
        self.money_supply = self.simulation_parameters["money_supply"]
        self.obligations = []

        # set up risk categories
        self.riskcategories = list(range(self.simulation_parameters["no_categories"]))
        self.rc_event_schedule = []
        self.rc_event_damage = []
        self.rc_event_schedule_initial = []   #For debugging (cloud debugging) purposes is good to store the initial schedule of catastrophes
        self.rc_event_damage_initial = []     #and damages that will be use in a single run of the model.

        if rc_event_schedule is not None and rc_event_damage is not None: #If we have schedules pass as arguments we used them.
            self.rc_event_schedule = copy.copy(rc_event_schedule)
            self.rc_event_schedule_initial = copy.copy(rc_event_schedule)

            self.rc_event_damage = copy.copy(rc_event_damage)
            self.rc_event_damage_initial = copy.copy(rc_event_damage)
        else:                                                              #Otherwise the schedules and damages are generated.
            self.setup_risk_categories_caller()


        # set up risks
        risk_value_mean = self.risk_value_distribution.mean()
        if np.isnan(risk_value_mean):     # unfortunately scipy.stats.mean is not well-defined if scale = 0
            risk_value_mean = self.risk_value_distribution.rvs()
        rrisk_factors = self.risk_factor_distribution.rvs(size=self.simulation_parameters["no_risks"])
        rvalues = self.risk_value_distribution.rvs(size=self.simulation_parameters["no_risks"])
        rcategories = np.random.randint(0, self.simulation_parameters["no_categories"], size=self.simulation_parameters["no_risks"])
        self.risks = [{"risk_factor": rrisk_factors[i], "value": rvalues[i], "category": rcategories[i], "owner": self} for i in range(self.simulation_parameters["no_risks"])]

        self.risks_counter = [0,0,0,0]

        for item in self.risks:
            self.risks_counter[item["category"]] = self.risks_counter[item["category"]] + 1


        # set up risk models
        #inaccuracy = [[(1./self.simulation_parameters["riskmodel_inaccuracy_parameter"] if (i + j) % 2 == 0 \
        #                else self.simulation_parameters["riskmodel_inaccuracy_parameter"]) \
        #                for i in range(self.simulation_parameters["no_categories"])] \
        #                for j in range(self.simulation_parameters["no_riskmodels"])]

        self.inaccuracy = self.get_all_riskmodel_combinations(self.simulation_parameters["no_categories"], self.simulation_parameters["riskmodel_inaccuracy_parameter"])

        self.inaccuracy = random.sample(self.inaccuracy, self.simulation_parameters["no_riskmodels"])

        risk_model_configurations = [{"damage_distribution": self.damage_distribution,
                                      "expire_immediately": self.simulation_parameters["expire_immediately"],
                                      "cat_separation_distribution": self.cat_separation_distribution,
                                      "norm_premium": self.norm_premium,
                                      "no_categories": self.simulation_parameters["no_categories"],
                                      "risk_value_mean": risk_value_mean,
                                      "risk_factor_mean": risk_factor_mean,
                                      "norm_profit_markup": self.simulation_parameters["norm_profit_markup"],
                                      "margin_of_safety": self.simulation_parameters["riskmodel_margin_of_safety"],
                                      "var_tail_prob": self.simulation_parameters["value_at_risk_tail_probability"],
                                      "inaccuracy_by_categ": self.inaccuracy[i]} \
                                      for i in range(self.simulation_parameters["no_riskmodels"])]
        
        # prepare setting up agents (to be done from start.py)
        self.agent_parameters = {"insurancefirm": [], "reinsurance": []}    # TODO: rename reinsurance -> reinsurancefirm (also in start.py and below in method accept_agents

        self.insurer_id_counter = 0
        # TODO: collapse the following two loops into one generic one?
        for i in range(simulation_parameters["no_insurancefirms"]):
            if simulation_parameters['static_non-proportional_reinsurance_levels']:
                insurance_reinsurance_level = simulation_parameters["default_non-proportional_reinsurance_deductible"]
            else:
                insurance_reinsurance_level = np.random.uniform(simulation_parameters["insurance_reinsurance_levels_lower_bound"], simulation_parameters["insurance_reinsurance_levels_upper_bound"])

            riskmodel_config = risk_model_configurations[i % len(risk_model_configurations)]
            self.agent_parameters["insurancefirm"].append({'id': self.get_unique_insurer_id(), 'initial_cash': simulation_parameters["initial_agent_cash"],
                                     'riskmodel_config': riskmodel_config, 'norm_premium': self.norm_premium,
                                     'profit_target': simulation_parameters["norm_profit_markup"],
                                     'initial_acceptance_threshold': simulation_parameters["initial_acceptance_threshold"],
                                     'acceptance_threshold_friction': simulation_parameters["acceptance_threshold_friction"],
                                     'reinsurance_limit': simulation_parameters["reinsurance_limit"],
                                     'non-proportional_reinsurance_level': insurance_reinsurance_level,
                                     'capacity_target_decrement_threshold': simulation_parameters['capacity_target_decrement_threshold'],
                                     'capacity_target_increment_threshold': simulation_parameters['capacity_target_increment_threshold'],
                                     'capacity_target_decrement_factor': simulation_parameters['capacity_target_decrement_factor'],
                                     'capacity_target_increment_factor': simulation_parameters['capacity_target_increment_factor'],
                                     'interest_rate': simulation_parameters["interest_rate"]})

        self.reinsurer_id_counter = 0
        for i in range(simulation_parameters["no_reinsurancefirms"]):
            if simulation_parameters['static_non-proportional_reinsurance_levels']:
                reinsurance_reinsurance_level = simulation_parameters["default_non-proportional_reinsurance_deductible"]
            else:
                reinsurance_reinsurance_level = np.random.uniform(simulation_parameters["reinsurance_reinsurance_levels_lower_bound"], simulation_parameters["reinsurance_reinsurance_levels_upper_bound"])

            riskmodel_config = risk_model_configurations[i % len(risk_model_configurations)]
            self.agent_parameters["reinsurance"].append({'id': self.get_unique_reinsurer_id(), 'initial_cash': simulation_parameters["initial_reinagent_cash"],
                                'riskmodel_config': riskmodel_config, 'norm_premium': self.norm_premium,
                                'profit_target': simulation_parameters["norm_profit_markup"],
                                'initial_acceptance_threshold': simulation_parameters["initial_acceptance_threshold"],
                                'acceptance_threshold_friction': simulation_parameters["acceptance_threshold_friction"],
                                'reinsurance_limit': simulation_parameters["reinsurance_limit"],
                                'non-proportional_reinsurance_level': reinsurance_reinsurance_level,
                                'capacity_target_decrement_threshold': simulation_parameters['capacity_target_decrement_threshold'],
                                'capacity_target_increment_threshold': simulation_parameters['capacity_target_increment_threshold'],
                                'capacity_target_decrement_factor': simulation_parameters['capacity_target_decrement_factor'],
                                'capacity_target_increment_factor': simulation_parameters['capacity_target_increment_factor'],
                                'interest_rate': simulation_parameters["interest_rate"]})
                                
        # set up remaining list variables
        
        # agent lists
        self.reinsurancefirms = []
        self.insurancefirms = []
        self.catbonds = []
        
        # lists of agent weights
        self.insurers_weights = {}
        self.reinsurers_weights = {}


        # list of reinsurance risks offered for underwriting
        self.reinrisks = []
        self.not_accepted_reinrisks = []
        
        # cumulative variables for history and logging
        self.cumulative_bankruptcies = 0
        self.cumulative_unrecovered_claims = 0.0
        self.cumulative_claims = 0.0
        
        # lists for logging history
        self.logger = logger.Logger(no_riskmodels=simulation_parameters["no_riskmodels"], 
                                    rc_event_schedule_initial=self.rc_event_schedule_initial, 
                                    rc_event_damage_initial=self.rc_event_damage_initial)
        
        self.insurance_models_counter = np.zeros(self.simulation_parameters["no_categories"])
        self.reinsurance_models_counter = np.zeros(self.simulation_parameters["no_categories"])

            
    
    def build_agents(self, agent_class, agent_class_string, parameters, agent_parameters):
        #assert agent_parameters == self.agent_parameters[agent_class_string]       #assert fits only the initial creation of agents, not later additions   # TODO: fix
        agents = []
        for ap in agent_parameters:
            agents.append(agent_class(parameters, ap))
        return agents
        
    def accept_agents(self, agent_class_string, agents, agent_group=None, time=0):
        # TODO: fix agent id's for late entrants (both firms and catbonds)
        if agent_class_string == "insurancefirm":
            try:
                self.insurancefirms += agents
                self.insurancefirms_group = agent_group
            except:
                print(sys.exc_info())
                pdb.set_trace()
            # fix self.history_logs['individual_contracts'] list
            for agent in agents:
                self.logger.add_insurance_agent()
            # remove new agent cash from simulation cash to ensure stock flow consistency
            new_agent_cash = sum([agent.cash for agent in agents])
            self.reduce_money_supply(new_agent_cash)
        elif agent_class_string == "reinsurance":
            try:
                self.reinsurancefirms += agents
                self.reinsurancefirms_group = agent_group
            except:
                print(sys.exc_info())
                pdb.set_trace()
            # remove new agent cash from simulation cash to ensure stock flow consistency
            new_agent_cash = sum([agent.cash for agent in agents])
            self.reduce_money_supply(new_agent_cash)
        elif agent_class_string == "catbond":
            try:
                self.catbonds += agents
            except:
                print(sys.exc_info())
                pdb.set_trace()            
        else:
            assert False, "Error: Unexpected agent class used {0:s}".format(agent_class_string)

    def delete_agents(self, agent_class_string, agents):
        if agent_class_string == "catbond":
            for agent in agents:
                self.catbonds.remove(agent)
        else:
            assert False, "Trying to remove unremovable agent, type: {0:s}".format(agent_class_string)
    
    def iterate(self, t):

        if isleconfig.verbose:
            print()
            print(t, ": ", len(self.risks))
        if isleconfig.showprogress:
            print("\rTime: {0:4d}".format(t), end="")

        self.reset_pls()


        # adjust market premiums
        sum_capital = sum([agent.get_cash() for agent in self.insurancefirms])      #TODO: include reinsurancefirms
        self.adjust_market_premium(capital=sum_capital)
        self.adjust_reinsurance_market_premium(capital=sum_capital)

        # pay obligations
        self.effect_payments(t)
        
        # identify perils and effect claims
        for categ_id in range(len(self.rc_event_schedule)):
            try:
                if len(self.rc_event_schedule[categ_id]) > 0:
                    assert self.rc_event_schedule[categ_id][0] >= t
            except:
                print("Something wrong; past events not deleted", file=sys.stderr)
            if len(self.rc_event_schedule[categ_id]) > 0 and self.rc_event_schedule[categ_id][0] == t:
                self.rc_event_schedule[categ_id] = self.rc_event_schedule[categ_id][1:]
                damage_extent = copy.copy(self.rc_event_damage[categ_id][0])      #Schedules of catastrophes and damages must me generated at the same time.
                self.inflict_peril(categ_id=categ_id, damage=damage_extent, t=t)# TODO: consider splitting the following lines from this method and running it with nb.jit
                self.rc_event_damage[categ_id] = self.rc_event_damage[categ_id][1:]
            else:
                if isleconfig.verbose:
                    print("Next peril ", self.rc_event_schedule[categ_id])
        
        # shuffle risks (insurance and reinsurance risks)
        self.shuffle_risks()

        # reset reinweights
        self.reset_reinsurance_weights()
                    
        # iterate reinsurnace firm agents
        for reinagent in self.reinsurancefirms:
            reinagent.iterate(t)
        # TODO: is the following necessary for abce to work (log) properly?
        #if isleconfig.use_abce:
        #    self.reinsurancefirms_group.iterate(time=t)
        #else:
        #    for reinagent in self.reinsurancefirms:
        #        reinagent.iterate(t)
        
        # remove all non-accepted reinsurance risks

        self.reinrisks = []

        # reset weights
        self.reset_insurance_weights()
                    
        # iterate insurance firm agents
        for agent in self.insurancefirms:
            agent.iterate(t)
        # TODO: is the following necessary for abce to work (log) properly?
        #if isleconfig.use_abce:
        #    self.insurancefirms_group.iterate(time=t)
        #else:
        #    for agent in self.insurancefirms:
        #        agent.iterate(t)
        
        # iterate catbonds 
        for agent in self.catbonds:
            agent.iterate(t)

        self.insurance_models_counter = np.zeros(self.simulation_parameters["no_categories"])

        for insurer in self.insurancefirms:
            for i in range(len(self.inaccuracy)):
                if insurer.operational:
                    if insurer.riskmodel.inaccuracy == self.inaccuracy[i]:
                        self.insurance_models_counter[i] += 1

        self.reinsurance_models_counter = np.zeros(self.simulation_parameters["no_categories"])

        for reinsurer in self.reinsurancefirms:
            for i in range(len(self.inaccuracy)):
                if reinsurer.operational:
                    if reinsurer.riskmodel.inaccuracy == self.inaccuracy[i]:
                        self.reinsurance_models_counter[i] += 1
        
        #print(isleconfig.show_network)
        # TODO: use network representation in a more generic way, perhaps only once at the end to characterize the network and use for calibration(?)
        if isleconfig.show_network and t % 40 == 0 and t > 0:
            RN = visualization_network.ReinsuranceNetwork(self.insurancefirms, self.reinsurancefirms, self.catbonds)
            RN.compute_measures()
            RN.visualize()
        
        
    def save_data(self):
        """Method to collect statistics about the current state of the simulation. Will pass these to the 
           Logger object (self.logger) to be recorded.
            No arguments.
            Returns None."""
        
        """ collect data """
        total_cash_no = sum([insurancefirm.cash for insurancefirm in self.insurancefirms])
        total_excess_capital = sum([insurancefirm.get_excess_capital() for insurancefirm in self.insurancefirms])
        total_profitslosses =  sum([insurancefirm.get_profitslosses() for insurancefirm in self.insurancefirms])
        total_contracts_no = sum([len(insurancefirm.underwritten_contracts) for insurancefirm in self.insurancefirms])
        total_reincash_no = sum([reinsurancefirm.cash for reinsurancefirm in self.reinsurancefirms])
        total_reinexcess_capital = sum([reinsurancefirm.get_excess_capital() for reinsurancefirm in self.reinsurancefirms])
        total_reinprofitslosses =  sum([reinsurancefirm.get_profitslosses() for reinsurancefirm in self.reinsurancefirms])
        total_reincontracts_no = sum([len(reinsurancefirm.underwritten_contracts) for reinsurancefirm in self.reinsurancefirms])
        operational_no = sum([insurancefirm.operational for insurancefirm in self.insurancefirms])
        reinoperational_no = sum([reinsurancefirm.operational for reinsurancefirm in self.reinsurancefirms])
        catbondsoperational_no = sum([catbond.operational for catbond in self.catbonds])
        
        """ collect agent-level data """
        insurance_firms = [(insurancefirm.cash,insurancefirm.id,insurancefirm.operational) for insurancefirm in self.insurancefirms]
        reinsurance_firms = [(reinsurancefirm.cash,reinsurancefirm.id,reinsurancefirm.operational) for reinsurancefirm in self.reinsurancefirms]
        
        """ prepare dict """
        current_log = {}
        current_log['total_cash'] = total_cash_no
        current_log['total_excess_capital'] = total_excess_capital
        current_log['total_profitslosses'] = total_profitslosses
        current_log['total_contracts'] = total_contracts_no
        current_log['total_operational'] = operational_no
        current_log['total_reincash'] = total_reincash_no
        current_log['total_reinexcess_capital'] = total_reinexcess_capital
        current_log['total_reinprofitslosses'] = total_reinprofitslosses
        current_log['total_reincontracts'] = total_reincontracts_no
        current_log['total_reinoperational'] = reinoperational_no
        current_log['total_catbondsoperational'] = catbondsoperational_no
        current_log['market_premium'] = self.market_premium
        current_log['market_reinpremium'] = self.reinsurance_market_premium
        current_log['cumulative_bankruptcies'] = self.cumulative_bankruptcies
        current_log['cumulative_unrecovered_claims'] = self.cumulative_unrecovered_claims
        current_log['cumulative_claims'] = self.cumulative_claims    #Log the cumulative claims received so far.
        
        """ add agent-level data to dict""" 
        current_log['insurance_firms_cash'] = insurance_firms
        current_log['reinsurance_firms_cash'] = reinsurance_firms
        current_log['market_diffvar'] = self.compute_market_diffvar()
        
        current_log['individual_contracts'] = []
        individual_contracts_no = [len(insurancefirm.underwritten_contracts) for insurancefirm in self.insurancefirms]
        for i in range(len(individual_contracts_no)):
            current_log['individual_contracts'].append(individual_contracts_no[i])

        """ call to Logger object """
        self.logger.record_data(current_log)
        
    def obtain_log(self):   #This function allows to return in a list all the data generated by the model. There is no other way to transfer it back from the cloud.
        return self.logger.obtain_log()
    
    def advance_round(self, *args):
        pass
    
    def finalize(self, *args):
        """Function to handle oberations after the end of the simulation run.
           Currently empty.
           It may be used to handle e.g. loging by including:
            self.log()
           but logging has been moved to start.py and ensemble.py
           """
        pass

    def inflict_peril(self, categ_id, damage, t):
        affected_contracts = [contract for insurer in self.insurancefirms for contract in insurer.underwritten_contracts if contract.category == categ_id]
        if isleconfig.verbose:
            print("**** PERIL ", damage)
        damagevalues = np.random.beta(1, 1./damage -1, size=self.risks_counter[categ_id])
        uniformvalues = np.random.uniform(0, 1, size=self.risks_counter[categ_id])
        [contract.explode(t, uniformvalues[i], damagevalues[i]) for i, contract in enumerate(affected_contracts)]
    
    def receive_obligation(self, amount, recipient, due_time, purpose):
        obligation = {"amount": amount, "recipient": recipient, "due_time": due_time, "purpose": purpose}
        self.obligations.append(obligation)

    def effect_payments(self, time):
        due = [item for item in self.obligations if item["due_time"]<=time]
        #print("SIMULATION obligations: ", len(self.obligations), " of which are due: ", len(due))
        self.obligations = [item for item in self.obligations if item["due_time"]>time]
        sum_due = sum([item["amount"] for item in due])
        for obligation in due:
            self.pay(obligation)

    def pay(self, obligation):
        amount = obligation["amount"]
        recipient = obligation["recipient"]
        purpose = obligation["purpose"]
        try:
            assert self.money_supply > amount
        except:
            print("Something wrong: economy out of money", file=sys.stderr)
        if self.get_operational() and recipient.get_operational():
            self.money_supply -= amount
            recipient.receive(amount)

    def receive(self, amount):
        """Method to accept cash payments."""
        self.money_supply += amount

    def reduce_money_supply(self, amount):
        """Method to reduce money supply immediately and without payment recipient (used to adjust money supply to compensate for agent endowment)."""
        self.money_supply -= amount
        assert self.money_supply >= 0

    def reset_reinsurance_weights(self):

        self.not_accepted_reinrisks = []

        operational_reinfirms = [reinsurancefirm for reinsurancefirm in self.reinsurancefirms if reinsurancefirm.operational]

        operational_no = len(operational_reinfirms)

        reinrisks_no = len(self.reinrisks)

        self.reinsurers_weights = {}

        for reinsurer in self.reinsurancefirms:
            self.reinsurers_weights[reinsurer.id] = 0

        if operational_no > 0:

            if reinrisks_no/operational_no > 1:
                weights = reinrisks_no/operational_no
                for reinsurer in self.reinsurancefirms:
                    self.reinsurers_weights[reinsurer.id] = math.floor(weights)
            else:
                for i in range(len(self.reinrisks)):
                    s = math.floor(np.random.uniform(0, len(operational_reinfirms), 1))
                    self.reinsurers_weights[operational_reinfirms[s].id] += 1
        else:
            self.not_accepted_reinrisks = self.reinrisks

    def reset_insurance_weights(self):

        operational_no = sum([insurancefirm.operational for insurancefirm in self.insurancefirms])

        operational_firms = [insurancefirm for insurancefirm in self.insurancefirms if insurancefirm.operational]

        risks_no = len(self.risks)

        self.insurers_weights = {}

        for insurer in self.insurancefirms:
            self.insurers_weights[insurer.id] = 0

        if operational_no > 0:

            if risks_no/operational_no > 1:
                weights = risks_no/operational_no
                for insurer in self.insurancefirms:
                    self.insurers_weights[insurer.id] = math.floor(weights)
            else:
                for i in range(len(self.risks)):
                    s = math.floor(np.random.uniform(0, len(operational_firms), 1))
                    self.insurers_weights[operational_firms[s].id] += 1

    def shuffle_risks(self):
        np.random.shuffle(self.reinrisks)
        np.random.shuffle(self.risks)

    def adjust_market_premium(self, capital):
        self.market_premium = self.norm_premium * (self.simulation_parameters["upper_price_limit"] - capital / (self.simulation_parameters["initial_agent_cash"] * self.damage_distribution.mean() * self.simulation_parameters["no_risks"]))
        if self.market_premium < self.norm_premium * self.simulation_parameters["lower_price_limit"]:
            self.market_premium = self.norm_premium * self.simulation_parameters["lower_price_limit"]
    
    def adjust_reinsurance_market_premium(self, capital):
         self.reinsurance_market_premium = self.market_premium

    def get_market_premium(self):
        return self.market_premium

    def get_reinsurance_premium(self, np_reinsurance_deductible_fraction):
        # TODO: cut this out of the insurance market premium -> OBSOLETE??
        # TODO: make premiums dependend on the deductible per value (np_reinsurance_deductible_fraction) -> DONE.
        # TODO: make max_reduction into simulation_parameter ?
        if self.reinsurance_off:
            return float('inf')
        max_reduction = 0.1
        return self.reinsurance_market_premium * (1. - max_reduction * np_reinsurance_deductible_fraction)
        
    def get_cat_bond_price(self, np_reinsurance_deductible_fraction):
        # TODO: implement function dependent on total capital in cat bonds and on deductible ()
        # TODO: make max_reduction and max_CB_surcharge into simulation_parameters ?
        if self.catbonds_off:
            return float('inf')
        max_reduction = 0.9
        max_CB_surcharge = 0.5 
        return self.reinsurance_market_premium * (1. + max_CB_surcharge - max_reduction * np_reinsurance_deductible_fraction)
        
    def append_reinrisks(self, item):
        if(len(item) > 0):
            self.reinrisks.append(item)

    def remove_reinrisks(self,risko):
        if(risko != None):
            self.reinrisks.remove(risko)

    def get_reinrisks(self):
        np.random.shuffle(self.reinrisks)
        return self.reinrisks

    def solicit_insurance_requests(self, id, cash, insurer):

        risks_to_be_sent = self.risks[:int(self.insurers_weights[insurer.id])]
        self.risks = self.risks[int(self.insurers_weights[insurer.id]):]
        for risk in insurer.risks_kept:
            risks_to_be_sent.append(risk)

        insurer.risks_kept = []

        np.random.shuffle(risks_to_be_sent)

        return risks_to_be_sent

    def solicit_reinsurance_requests(self, id, cash, reinsurer):
        reinrisks_to_be_sent = self.reinrisks[:int(self.reinsurers_weights[reinsurer.id])]
        self.reinrisks = self.reinrisks[int(self.reinsurers_weights[reinsurer.id]):]

        for reinrisk in reinsurer.reinrisks_kept:
            reinrisks_to_be_sent.append(reinrisk)

        reinsurer.reinrisks_kept = []

        np.random.shuffle(reinrisks_to_be_sent)

        return reinrisks_to_be_sent

    def return_risks(self, not_accepted_risks):
        self.risks += not_accepted_risks

    def return_reinrisks(self, not_accepted_risks):
        self.not_accepted_reinrisks += not_accepted_risks

    def get_all_riskmodel_combinations(self, n, rm_factor):
        riskmodels = []
        for i in range(self.simulation_parameters["no_categories"]):
            riskmodel_combination = rm_factor * np.ones(self.simulation_parameters["no_categories"])
            riskmodel_combination[i] = 1/rm_factor
            riskmodels.append(riskmodel_combination.tolist())
        return riskmodels

    def setup_risk_categories(self):
        for i in self.riskcategories:
            event_schedule = []
            event_damage = []
            total = 0
            while (total < self.simulation_parameters["max_time"]):
                separation_time = self.cat_separation_distribution.rvs()
                total += int(math.ceil(separation_time))
                if total < self.simulation_parameters["max_time"]:
                    event_schedule.append(total)
                    event_damage.append(self.damage_distribution.rvs())   #Schedules of catastrophes and damages must me generated at the same time. Reason: replication across different risk models.
            self.rc_event_schedule.append(event_schedule)
            self.rc_event_damage.append(event_damage)

        self.rc_event_schedule_initial = copy.copy(self.rc_event_damage)   #For debugging (cloud debugging) purposes is good to store the initial schedule of catastrophes
        self.rc_event_damage_initial = copy.copy(self.rc_event_damage)     #and damages that will be use in a single run of the model.

    def setup_risk_categories_caller(self):
        #if self.background_run:
        if self.replic_ID is not None:
            if isleconfig.replicating:
                self.restore_state_and_risk_categories()
            else:
                self.setup_risk_categories()
                self.save_state_and_risk_categories()
        else:
            self.setup_risk_categories()

    def save_state_and_risk_categories(self):
        # save numpy Mersenne Twister state
        mersennetwoster_randomseed = str(np.random.get_state())
        mersennetwoster_randomseed = mersennetwoster_randomseed.replace("\n","").replace("array", "np.array").replace("uint32", "np.uint32")
        wfile = open("data/replication_randomseed.dat","a")
        wfile.write(mersennetwoster_randomseed+"\n")
        wfile.close()
        # save event schedule
        wfile = open("data/replication_rc_event_schedule.dat","a")
        wfile.write(str(self.rc_event_schedule)+"\n")
        wfile.close()
        
    def restore_state_and_risk_categories(self):
        rfile = open("data/replication_rc_event_schedule.dat","r")
        found = False
        for i, line in enumerate(rfile):
            #print(i, self.replic_ID)
            if i == self.replic_ID:
                self.rc_event_schedule = eval(line)
                found = True
        rfile.close()
        assert found, "rc event schedule for current replication ID number {0:d} not found in data file. Exiting.".format(self.replic_ID)
        rfile = open("data/replication_randomseed.dat","r")
        found = False
        for i, line in enumerate(rfile):
            #print(i, self.replic_ID)
            if i == self.replic_ID:
                mersennetwister_randomseed = eval(line)
                found = True
        rfile.close()
        np.random.set_state(mersennetwister_randomseed)
        assert found, "mersennetwister randomseed for current replication ID number {0:d} not found in data file. Exiting.".format(self.replic_ID)

    def insurance_firm_market_entry(self, prob=-1, agent_type="InsuranceFirm"):             # TODO: replace method name with a more descriptive one
        if prob == -1:
            if agent_type == "InsuranceFirm":
                prob = self.simulation_parameters["insurance_firm_market_entry_probability"]
            elif agent_type == "ReinsuranceFirm":
                prob = self.simulation_parameters["reinsurance_firm_market_entry_probability"]
            else:
                assert False, "Unknown agent type. Simulation requested to create agent of type {0:s}".format(agent_type)
        if np.random.random() < prob:
            return True
        else:
            return False

    def record_bankruptcy(self):
        self.cumulative_bankruptcies += 1

    def record_unrecovered_claims(self, loss):
        self.cumulative_unrecovered_claims += loss

    def record_claims(self, claims):   #This method records every claim made to insurers and reinsurers. It is called from both insurers and reinsurers (metainsuranceorg.py).
        self.cumulative_claims += claims
    
    def log(self):
        self.logger.save_log(self.background_run)
        
    def compute_market_diffvar(self):

        varsfirms = []
        for firm in self.insurancefirms:
            if firm.operational:
                varsfirms.append(firm.var_counter_per_risk)
        totalina = sum(varsfirms)

        varsfirms = []
        for firm in self.insurancefirms:
            if firm.operational:
                varsfirms.append(1)
        totalreal = sum(varsfirms)

        varsreinfirms = []
        for reinfirm in self.reinsurancefirms:
            if reinfirm.operational:
                varsreinfirms.append(reinfirm.var_counter_per_risk)
        totalina = totalina + sum(varsreinfirms)

        varsreinfirms = []
        for reinfirm in self.reinsurancefirms:
            if reinfirm.operational:
                varsreinfirms.append(1)
        totalreal = totalreal + sum(varsreinfirms)

        totaldiff = totalina - totalreal
        
        return totaldiff
        #self.history_logs['market_diffvar'].append(totaldiff)

    def count_underwritten_and_reinsured_risks_by_category(self):
        underwritten_risks = 0
        reinsured_risks = 0
        underwritten_per_category = np.zeros(self.simulation_parameters["no_categories"])
        reinsured_per_category = np.zeros(self.simulation_parameters["no_categories"])
        for firm in self.insurancefirms:
            if firm.operational:
                underwritten_by_category += firm.counter_category
                if self.simulation_parameters["simulation_reinsurance_type"] == "non-proportional":
                    reinsured_per_category += firm.counter_category * firm.category_reinsurance 
        if self.simulation_parameters["simulation_reinsurance_type"] == "proportional":
            for firm in self.insurancefirms:
                if firm.operational:
                    reinsured_per_category += firm.counter_category

    def get_unique_insurer_id(self):
        current_id = self.insurer_id_counter
        self.insurer_id_counter += 1
        return current_id

    def get_unique_reinsurer_id(self):
        current_id = self.reinsurer_id_counter
        self.reinsurer_id_counter += 1
        return current_id

    def insurance_entry_index(self):
        return self.insurance_models_counter[0:self.simulation_parameters["no_riskmodels"]].argmin()

    def reinsurance_entry_index(self):
        return self.reinsurance_models_counter[0:self.simulation_parameters["no_riskmodels"]].argmin()

    def get_operational(self):
        return True

    def reinsurance_capital_entry(self):     #This method determines the capital market entry of reinsurers. It is only run in start.py.
        capital_per_non_re_cat = []

        for reinrisk in self.not_accepted_reinrisks:
            capital_per_non_re_cat.append(reinrisk["value"])     #It takes all the values of the reinsurance risks NOT REINSURED.

        if len(capital_per_non_re_cat) > 0:  #We only perform this action if there are reinsurance contracts that has not been reinsured in the last period of time.
            capital_per_non_re_cat = np.random.choice(capital_per_non_re_cat, 10)        #Only 10 values sampled randomly are considered. (Too low?)
            entry = max(capital_per_non_re_cat)            #For market entry the maximum of the sample is considered.
            entry = 2 * entry           #The capital market entry of those values will be the double of the maximum.
        else:    #Otherwise the default reinsurance cash market entry is considered.
            entry = self.simulation_parameters["initial_reinagent_cash"]

        return entry           #The capital market entry is returned.

    def reset_pls(self):
        """Reset_pls Method.
               Accepts no arguments:
               No return value.
           This method reset all the profits and losses of all insurance firms, reinsurance firms and catbonds."""
        for insurancefirm in self.insurancefirms:
            insurancefirm.reset_pl()

        for reininsurancefirm in self.reinsurancefirms:
            reininsurancefirm.reset_pl()

        for catbond in self.catbonds:
            catbond.reset_pl()

