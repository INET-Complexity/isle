
from insurancefirm import InsuranceFirm
from riskmodel import RiskModel
from reinsurancefirm import ReinsuranceFirm
#from reinriskmodel import ReinriskModel
import numpy as np
import scipy.stats
import math
import sys, pdb
import numba as nb
import abce




class InsuranceSimulation():
    def __init__(self, override_no_riskmodels, replic_ID, simulation_parameters):
        # override one-riskmodel case (this is to ensure all other parameters are truly identical for comparison runs)
        if override_no_riskmodels:
            simulation_parameters["no_riskmodels"] = override_no_riskmodels

        # save parameters
        self.background_run = False if replic_ID is None else True
        self.replic_ID = replic_ID
        self.simulation_parameters = simulation_parameters

        # unpack parameters, set up environment (distributions etc.)
        self.damage_distribution = scipy.stats.uniform(loc=0, scale=1)
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
        self.total_no_risks = simulation_parameters["no_risks"]

        #print(self.norm_premium)
        #pdb.set_trace()

        # set up monetary system (should instead be with the customers, if customers are modeled explicitly)
        self.money_supply = self.simulation_parameters["money_supply"]
        self.obligations = []

        # set up risk categories
        self.riskcategories = list(range(self.simulation_parameters["no_categories"]))
        self.rc_event_schedule = []
        self.setup_risk_categories_caller()

        # set up risks
        risk_value_mean = self.risk_value_distribution.mean()
        if np.isnan(risk_value_mean):     # unfortunately scipy.stats.mean is not well-defined if scale = 0
            risk_value_mean = self.risk_value_distribution.rvs()
        rrisk_factors = self.risk_factor_distribution.rvs(size=self.simulation_parameters["no_risks"])
        rvalues = self.risk_value_distribution.rvs(size=self.simulation_parameters["no_risks"])
        rcategories = np.random.randint(0, self.simulation_parameters["no_categories"], size=self.simulation_parameters["no_risks"])
        self.risks = [{"risk_factor": rrisk_factors[i], "value": rvalues[i], "category": rcategories[i], "owner": self} for i in range(self.simulation_parameters["no_risks"])]

        # set up risk models
        inaccuracy = [[(0.5 if (i+j)%2==0 else 2.) for i in range(self.simulation_parameters["no_categories"])] for j in range(self.simulation_parameters["no_riskmodels"])]
        self.riskmodels = [RiskModel(self.damage_distribution, self.simulation_parameters["expire_immediately"], \
                    self.cat_separation_distribution, self.norm_premium, self.simulation_parameters["no_categories"], \
                    risk_value_mean, risk_factor_mean, \
                    self.simulation_parameters["norm_profit_markup"], inaccuracy[i]) \
                    for i in range(self.simulation_parameters["no_riskmodels"])]

        self.reinrisks = []

    def receive_obligation(self, amount, recipient, due_time):
        obligation = {"amount": amount, "recipient": recipient, "due_time": due_time}
        self.obligations.append(obligation)

    def effect_payments(self, time):
        due = [item for item in self.obligations if item["due_time"]<=time]
        #print("SIMULATION obligations: ", len(self.obligations), " of which are due: ", len(due))
        self.obligations = [item for item in self.obligations if item["due_time"]>time]
        sum_due = sum([item["amount"] for item in due])
        for obligation in due:
            self.pay(obligation["amount"], obligation["recipient"])

    def pay(self, amount, recipient):
        #print("SIMULATION paying ", amount)
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

    @nb.jit
    def reset_reinsurance_weights(self, zeros):
        self.reinsurancefirm_weights = self._reinsurancefirm_new_weights / sum(
            self._reinsurancefirm_new_weights) * len(self.reinrisks)
        self.reinsurancefirm_weights = np.int64(np.floor(self.reinsurancefirm_weights))


        #self.reinsurancefirm_new_weights = [0 for i in self.reinsurancefirms]
        #reinsurancefirm_new_weights2 = [0 for i in self.reinsurancefirms]
        self.reinsurancefirm_new_weights = zeros
        #assert self.reinsurancefirm_new_weights == reinsurancefirm_new_weights2

    @nb.jit
    def reset_insurance_weights(self, zeros):
        self.insurancefirm_weights = self._insurancefirm_new_weights / sum(self._insurancefirm_new_weights) * len(self.risks)
        self.insurancefirm_weights = np.int64(np.floor(self._insurancefirm_weights))
        #self.insurancefirm_new_weights = [0 for i in self.insurancefirms]
        self.insurancefirm_new_weights = zeros
        print('@', self.insurancefirm_weights)


    @nb.jit
    def shuffle_risks(self):
        np.random.shuffle(self.reinrisks)
        np.random.shuffle(self.risks)

    def adjust_market_premium(self, capital):
        self.market_premium = self.norm_premium * (self.simulation_parameters["upper_price_limit"] - capital / (self.norm_premium * self.simulation_parameters["no_risks"]))
        if self.market_premium < self.norm_premium * self.simulation_parameters["lower_price_limit"]:
            self.market_premium = self.norm_premium * self.simulation_parameters["lower_price_limit"]

    def get_market_premium(self):
        return self.market_premium

    def append_reinrisks(self, item):
        if(len(item) > 0):
            self.reinrisks.append(item)

    def remove_reinrisks(self,risko):
        if(risko != None):
            self.reinrisks.remove(risko)

    def get_reinrisks(self):
        np.random.shuffle(self.reinrisks)
        return self.reinrisks

    def solicit_insurance_requests(self, id, cash):
        self._insurancefirm_new_weights[id] = cash
        risks_to_be_sent = self.risks[:int(self._insurancefirm_weights[id])]
        self.risks = self.risks[int(self._insurancefirm_weights[id]):]
        print("Number of risks", len(risks_to_be_sent))
        return risks_to_be_sent

    def return_risks(self, not_accepted_risks):
        self.risks += not_accepted_risks

    def solicit_reinsurance_requests(self, id, cash):
        self._reinsurancefirm_new_weights[id] = cash
        reinrisks_to_be_sent = self.reinrisks[:self.reinsurancefirm_weights[id]]
        self.reinrisks = self.reinrisks[self.reinsurancefirm_weights[id]:]
        print("Number of risks",len(reinrisks_to_be_sent))
        return reinrisks_to_be_sent

    def return_reinrisks(self, not_accepted_risks):
        self.reinrisks += not_accepted_risks

    def setup_risk_categories(self):
        for i in self.riskcategories:
            event_schedule = []
            total = 0
            while (total < self.simulation_parameters["max_time"]):
                separation_time = self.cat_separation_distribution.rvs()
                total += int(math.ceil(separation_time))
                if total < self.simulation_parameters["max_time"]:
                    event_schedule.append(total)
            self.rc_event_schedule.append(event_schedule)

    def setup_risk_categories_caller(self):
        if self.background_run:
            self.setup_risk_categories()

            wfile = open("data/rc_event_schedule.dat","a")
            wfile.write(str(self.rc_event_schedule)+"\n")
            wfile.close()

        else:
            self.setup_risk_categories()


