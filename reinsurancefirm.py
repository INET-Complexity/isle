import numpy as np
import scipy.stats
from reinsurancecontract import ReinsuranceContract
import sys, pdb


class ReinsuranceFirm():
    def __init__(self, simulation, simulation_parameters, agent_parameters):
        self.simulation = simulation
        ##or: ABCE style:
        # def init(self, simulation_parameters, agent_parameters):
        ##note that ABCE-style cannot have a pointer to the simulation. It should deal with customers directly instead.

        self.id = agent_parameters['id']
        self.cash = agent_parameters['initial_cash']
        self.reinriskmodel = agent_parameters['reinriskmodel']
        self.premium = agent_parameters["norm_premium"]
        self.profit_target = agent_parameters['profit_target']
        self.acceptance_threshold = agent_parameters['initial_acceptance_threshold']  # 0.5
        self.acceptance_threshold_friction = agent_parameters['acceptance_threshold_friction']  # 0.9 #1.0 to switch off
        self.obligations_reinsurer = []
        self.rein_underwritten_contracts = []
        self.operational = True


    def iterate(self, time):
        # """realize income: not necessary"""
        # pass

        """realize due payments"""
        self.effect_payments(time)
        print(time, ":", self.id, len(self.rein_underwritten_contracts), self.cash, self.operational)

        """mature reincontracts"""
        print("Hey", len(self.rein_underwritten_contracts))
        maturing = [reincontract for reincontract in self.rein_underwritten_contracts if reincontract.expiration <= time]
        for reincontract in maturing:
            self.rein_underwritten_contracts.remove(reincontract)
        reincontracts_dissolved = len(maturing)

        print(len(self.rein_underwritten_contracts))

        if self.operational:
            # Only for ABCE:
            # """collect messages"""
            # self.obligations += [obligation.content for obligation in self.get_messages('obligation')]

            """request risks to be considered for rein_underwriting in the next period and collect those for this period"""
            # Non-ABCE style
            new_reinrisks = self.simulation.solicit_reinsurance_requests(self.id, self.cash)
            ## ABCE style
            # self.message("insurancecustomer", 0, 'solicit_insurance_requests', {"number": self.posession("money")})
            # new_reinrisks = []
            # for new_reinrisks in self.get_messages('new_reinrisks')
            #    new_reinrisks += new_reinrisks.content
            reincontracts_offered = len(new_reinrisks)
            try:
                assert reincontracts_offered > 2 * reincontracts_dissolved
            except:
                print("Something wrong; agent {0:d} receives too few new reincontracts {1:d} <= {2:d}".format(self.id,
                                                                                                          reincontracts_offered,
                                                                                                          2 * reincontracts_dissolved))
            # print(self.id, " has ", len(self.rein_underwritten_contracts), " & receives ", reincontracts_offered, " & lost ", reincontracts_dissolved)


            """make rein_underwriting decisions, category-wise"""
            rein_underwritten_risks = [{"excess": reincontract.excess, "category": reincontract.category, "deductible": reincontract.deductible, \
                                   "runtime": reincontract.runtime, "risk_factor": reincontract.risk_factor} \
                                   for reincontract in self.rein_underwritten_contracts]
            expected_profit, acceptable_by_category = self.reinriskmodel.evaluate(rein_underwritten_risks, self.cash)

            self.acceptable_mem = acceptable_by_category
            # if expected_profit * 1./self.cash < self.profit_target:
            #    self.acceptance_threshold = ((self.acceptance_threshold - .4) * 5. * self.acceptance_threshold_friction) / 5. + .4
            # else:
            #    self.acceptance_threshold = (1 - self.acceptance_threshold_friction * (1 - (self.acceptance_threshold - .4) * 5.)) / 5. + .4

            growth_limit = max(50, 2 * len(self.rein_underwritten_contracts) + reincontracts_dissolved)
            if sum(acceptable_by_category) > growth_limit:
                acceptable_by_category = np.asarray(acceptable_by_category)
                acceptable_by_category = acceptable_by_category * growth_limit / sum(acceptable_by_category)
                acceptable_by_category = np.int64(np.round(acceptable_by_category))

            not_accepted_reinrisks = []
            for categ_id in range(len(acceptable_by_category)):
                categ_risks = [risk for risk in new_reinrisks if risk["category"] == categ_id]
                new_reinrisks = [risk for risk in new_reinrisks if risk["category"] != categ_id]
                i = 0
                print("InsuranceFirm rein_underwrote: ", len(self.rein_underwritten_contracts), " will accept: ",
                      acceptable_by_category[categ_id], " out of ", len(categ_risks), "acceptance threshold: ",
                      self.acceptance_threshold)
                try:
                    while (acceptable_by_category[categ_id] > 0 and len(categ_risks) > i):  # \
                        # and categ_risks[i]["risk_factor"] < self.acceptance_threshold):
                        #reincontract = ReinsuranceContract(self, categ_risks[i], time, self.simulation.get_market_premium())
                        #reincontract = ReinsuranceContract(self, categ_risks[i], time, self.simulation.get_market_premium(), categ_risks[i]["contract"].expiration - time)  # TODO: make last agrument less convoluted, but consistent with insurancefirm 
                        reincontract = ReinsuranceContract(self, categ_risks[i], time, self.simulation.get_market_premium(), categ_risks[i]["expiration"] - time)  # TODO: make last agrument less convoluted, but consistent with insurancefirm 
                        self.rein_underwritten_contracts.append(reincontract)
                        categ_risks[i]["contract"].reincontract = reincontract
                        acceptable_by_category[categ_id] -= 1
                        i += 1
                        print(len(self.rein_underwritten_contracts))
                except:
                    print(sys.exc_info())
                    pdb.set_trace()
                not_accepted_reinrisks += categ_risks[i:]

            # return unacceptables
            # print(self.id, " now has ", len(self.rein_underwritten_contracts), " & returns ", len(not_accepted_reinrisks))


            self.simulation.return_reinrisks(not_accepted_reinrisks)


            # not implemented
            # """adjust liquidity, borrow or invest"""
            # pass
        else:
            pass
            # Non-ABCE style not required
            # self.simulation.return_risks(self.simulation.solicit_insurance_requests(0))
            # ABCE style:
            # ...requires collecting message with risks like above and sending the all back

    def enter_illiquidity(self):
        self.enter_bankruptcy()

    def enter_bankruptcy(self):
        self.simulation.receive(self.cash)
        self.cash = 0
        self.operational = False

    def reinsurer_receive_obligation(self, amount, recipient, due_time):
        obligation = {"amount": amount, "recipient": recipient, "due_time": due_time}
        self.obligations_reinsurer.append(obligation)

    def effect_payments(self, time):
        due = [item for item in self.obligations_reinsurer if item["due_time"] <= time]
        self.obligations_reinsurer = [item for item in self.obligations_reinsurer if item["due_time"] > time]
        sum_due = sum([item["amount"] for item in due])
        if sum_due > self.cash:
            self.obligations_reinsurer += due
            self.enter_illiquidity()
        else:
            for obligation in due:
                self.pay(obligation["amount"], obligation["recipient"])

    def pay(self, amount, recipient):
        ## ABCE style:
        # self.give(self, recipient, "cash", amount)
        # Non-ABCE style:
        self.cash -= amount
        recipient.receive(amount)

    def receive(self, amount):
        ## Not necessary in ABCE style
        # pass
        # Non-ABCE style
        """Method to accept cash payments."""
        self.cash += amount

    def return_reinrisks(self,reinrisk):
        print(self.simulation.reinrisks)
        self.simulation.return_reinrisks(reinrisk)
        print(self.simulation.reinrisks)
