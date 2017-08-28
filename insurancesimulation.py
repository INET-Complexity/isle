
from insurancefirm import InsuranceFirm
from riskmodel import RiskModel
import numpy as np
import scipy.stats
import math

class InsuranceSimulation():
    def __init__(self, simulation_parameters = {"no_categories": 2,\
                                                "no_insurancefirms": 2, \
                                                "no_riskmodels": 2, \
                                                "norm_profit_markup": 0.15, \
                                                "mean_contract_runtime": 50, \
                                                "contract_runtime_halfspread": 0, \
                                                "max_time": 2000, \
                                                "money_supply": 2000000000, \
                                                "event_time_mean_separation": 100/3., \
                                                "expire_immediately": True, \
                                                "risk_factors_present": True, \
                                                "risk_factor_lower_bound": 0.4, \
                                                "risk_factor_upper_bound": 0.6, \
                                                "initial_acceptance_threshold": 0.5, \
                                                "acceptance_threshold_friction": 0.9, \
                                                "initial_agent_cash": 1000000, \
                                                "no_risks": 2000 }):
        
        # save parameters
        self.simulation_parameters = simulation_parameters
        
        # unpack parameters, set up environment (distributions etc.)
        self.damage_distribution = scipy.stats.uniform(loc=0, scale=1)
        self.cat_separation_distribution = scipy.stats.expon(1, simulation_parameters["event_time_mean_separation"])
        self.risk_factor_lower_bound = simulation_parameters["risk_factor_lower_bound"]
        self.risk_factor_spread = simulation_parameters["risk_factor_upper_bound"] - simulation_parameters["risk_factor_lower_bound"]
        self.risk_factor_distribution = scipy.stats.uniform(loc=self.risk_factor_lower_bound, scale=self.risk_factor_spread)
        #self.risk_value_distribution = scipy.stats.uniform(loc=100, scale=9900)
        self.risk_value_distribution = scipy.stats.uniform(loc=1000, scale=0)
        
        # set initial market price (normalized, i.e. must be multiplied by value or excess-deductible)
        self.norm_premium = self.simulation_parameters["mean_contract_runtime"] / \
                        self.cat_separation_distribution.mean() * self.damage_distribution.mean() * \
                        self.risk_factor_distribution.mean() * \
                        (1 + self.simulation_parameters["norm_profit_markup"])
        
        # set up monetary system (should instead be with the customers, if customers are modeled explicitly)
        self.money_supply = self.simulation_parameters["money_supply"]
        self.obligations = []
        
        # set up risk categorues
        self.riskcategories = list(range(self.simulation_parameters["no_categories"]))
        self.rc_event_schedule = []
        for i in self.riskcategories:
            event_schedule = []
            total = 0
            while (total < self.simulation_parameters["max_time"]):
                separation_time = self.cat_separation_distribution.rvs()
                total += separation_time
                if total < self.simulation_parameters["max_time"]:
                    event_schedule.append(int(math.floor(total)))
            self.rc_event_schedule.append(event_schedule)
        
        # set up risks
        risk_value_mean = self.risk_value_distribution.mean() 
        if np.isnan(risk_value_mean):     # unfortunately scipy.stats.mean is not well-defined if scale = 0
            risk_value_mean = self.risk_value_distribution.rvs() 
        rrisk_factors = self.risk_factor_distribution.rvs(size=self.simulation_parameters["no_risks"])
        rvalues = self.risk_value_distribution.rvs(size=self.simulation_parameters["no_risks"])
        rcategories = np.random.randint(0, self.simulation_parameters["no_categories"], size=self.simulation_parameters["no_risks"])
        self.risks = [{"risk_factor": rrisk_factors[i], "value": rvalues[i], "category": rcategories[i], "owner": self} for i in range(self.simulation_parameters["no_risks"])]
            
        # set up risk models
        self.riskmodels = [RiskModel(self.damage_distribution, self.simulation_parameters["expire_immediately"], \
                    self.cat_separation_distribution, self.norm_premium, self.simulation_parameters["no_categories"], \
                    risk_value_mean, self.risk_factor_distribution.mean(), \
                    self.simulation_parameters["norm_profit_markup"]) \
                    for i in range(self.simulation_parameters["no_riskmodels"])]
        
        # set up insurance firms
        self.insurancefirms = []
        for i in range(self.simulation_parameters["no_insurancefirms"]):
            riskmodel = self.riskmodels[i % len(self.riskmodels)]
            agent_parameters = {'id': i, 'initial_cash': simulation_parameters["initial_agent_cash"], \
                                'riskmodel': riskmodel, 'norm_premium': self.norm_premium, \
                                'profit_target': simulation_parameters["norm_profit_markup"], \
                                'initial_acceptance_threshold': simulation_parameters["initial_acceptance_threshold"], \
                                'acceptance_threshold_friction': simulation_parameters["acceptance_threshold_friction"]}
            insurer = InsuranceFirm(self, simulation_parameters, agent_parameters)
            self.insurancefirms.append(insurer)
        self.insurancefirm_weights = [1 for i in self.insurancefirms]
        self.insurancefirm_new_weights = [0 for i in self.insurancefirms]

        
    def run(self):
        for t in range(self.simulation_parameters["max_time"]):
            print()
            print(t, ": ", len(self.risks))
            # pay obligations
            self.effect_payments(t)
            # identify perils and effect claims
            for categ_id in range(len(self.rc_event_schedule)):
                try:
                    if len(self.rc_event_schedule[categ_id]) > 0:
                        assert self.rc_event_schedule[categ_id][0] >= t
                except:
                    print("Something wrong; past events not deleted")
                if len(self.rc_event_schedule[categ_id]) > 0 and self.rc_event_schedule[categ_id][0] == t:
                    self.rc_event_schedule[categ_id] = self.rc_event_schedule[categ_id][1:]
                    affected_contracts = [contract for insurer in self.insurancefirms for contract in insurer.underwritten_contracts if contract.category == categ_id]
                    no_affected = len(affected_contracts)
                    damage = self.damage_distribution.rvs()
                    damagevalues = np.random.beta(1, 1./damage -1, size=no_affected)
                    uniformvalues = np.random.uniform(0, 1, size=no_affected)
                    [contract.explode(self.simulation_parameters["expire_immediately"], t, uniformvalues[i], damagevalues[i]) for i, contract in enumerate(affected_contracts)]
            # reset weights
            self.insurancefirm_weights = np.asarray(self.insurancefirm_new_weights) / sum(self.insurancefirm_new_weights) * len(self.risks)
            self.insurancefirm_weights = np.int64(np.floor(self.insurancefirm_weights))
            self.insurancefirm_new_weights = [0 for i in self.insurancefirms]
            np.random.shuffle(self.risks)
            
            # iterate agents
            for agent in self.insurancefirms:
                agent.iterate(t)

    def return_risks(self, not_accepted_risks):
        self.risks += not_accepted_risks
        
    def solicit_insurance_requests(self, id, cash):
        self.insurancefirm_new_weights[id] = cash
        risks_to_be_sent = self.risks[:self.insurancefirm_weights[id]]
        self.risks = self.risks[self.insurancefirm_weights[id]:]
        return risks_to_be_sent

    def receive_obligation(self, amount, recipient, due_time):
        obligation = {"amount": amount, "recipient": recipient, "due_time": due_time}
        self.obligations.append(obligation)
    
    def effect_payments(self, time):
        due = [item for item in self.obligations if item["due_time"]<=time] 
        self.obligations = [item for item in self.obligations if item["due_time"]>time]
        sum_due = sum([item["amount"] for item in due])
        self.obligations += due
        for obligation in due:
            self.pay(obligation["amount"], obligation["recipient"])

    def pay(self, amount, recipient):
        try:
            assert self.money_supply > amount
        except:
            print("Something wrong: economy out of money")
        self.money_supply -= amount
        recipient.receive(amount)

    def receive(self, amount):
        ## Not necessary in ABCE style
        #pass
        # Non-ABCE style
        """Method to accept cash payments."""
        self.money_supply += amount

# main entry point
if __name__ == "__main__":
    S = InsuranceSimulation()
    S.run()
