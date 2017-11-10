
import isleconfig
import numpy as np
import scipy.stats
from insurancecontract import InsuranceContract
from reinsurancecontract import ReinsuranceContract
import sys, pdb
import uuid
import numba as nb

if isleconfig.use_abce:
    from genericagentabce import GenericAgent
    #print("abce imported")
else:
    from genericagent import GenericAgent
    #print("abce not imported")

class InsuranceFirm(GenericAgent):
    def init(self, simulation_parameters, agent_parameters):
        self.simulation = simulation_parameters['simulation']
        self.contract_runtime_dist = scipy.stats.randint(simulation_parameters["mean_contract_runtime"] - \
                  simulation_parameters["contract_runtime_halfspread"], simulation_parameters["mean_contract_runtime"] \
                  + simulation_parameters["contract_runtime_halfspread"] + 1)
        self.default_contract_payment_period = simulation_parameters["default_contract_payment_period"]
        self.id = agent_parameters['id']
        self.cash = agent_parameters['initial_cash']
        self.riskmodel = agent_parameters['riskmodel']
        self.premium = agent_parameters["norm_premium"]
        self.profit_target = agent_parameters['profit_target']
        self.acceptance_threshold = agent_parameters['initial_acceptance_threshold']  # 0.5
        self.acceptance_threshold_friction = agent_parameters['acceptance_threshold_friction']  # 0.9 #1.0 to switch off
        self.interest_rate = agent_parameters["interest_rate"]
        self.reinsurance_limit = agent_parameters["reinsurance_limit"]
        self.simulation_reinsurance_type = simulation_parameters["simulation_reinsurance_type"]
        if self.simulation_reinsurance_type == 'non-proportional':
            self.np_reinsurance_deductible = simulation_parameters["default_non-proportional_reinsurance_deductible"]
            self.np_reinsurance_excess = simulation_parameters["default_non-proportional_reinsurance_excess"]
        self.obligations = []
        self.underwritten_contracts = []
        #self.reinsurance_contracts = []
        self.operational = True
        self.is_insurer = True
        self.is_reinsurer = False

    def iterate(self, time):
        """obtain investments yield"""
        self.obtain_yield(time)

        """realize due payments"""
        self.effect_payments(time)
        print(time, ":", self.id, len(self.underwritten_contracts), self.cash, self.operational)
        
        """mature contracts"""
        print("Number of underwritten contracts ", len(self.underwritten_contracts))
        maturing = [contract for contract in self.underwritten_contracts if contract.expiration <= time]
        for contract in maturing:
            self.underwritten_contracts.remove(contract)
            contract.mature(time)
        contracts_dissolved = len(maturing)

        """effect payments from contracts"""
        [contract.check_payment_due(time) for contract in self.underwritten_contracts]

        if self.operational:

            """request risks to be considered for underwriting in the next period and collect those for this period"""
            new_risks = []
            if self.is_insurer:
                new_risks += self.simulation.solicit_insurance_requests(self.id, self.cash)
            if self.is_reinsurer:
                new_risks += self.simulation.solicit_reinsurance_requests(self.id, self.cash)
            contracts_offered = len(new_risks)
            try:
                assert contracts_offered > 2 * contracts_dissolved
            except:
                print("Something wrong; agent {0:d} receives too few new contracts {1:d} <= {2:d}".format(self.id, contracts_offered, 2*contracts_dissolved))
            #print(self.id, " has ", len(self.underwritten_contracts), " & receives ", contracts_offered, " & lost ", contracts_dissolved)


            """make underwriting decisions, category-wise"""
            underwritten_risks = [{"excess": contract.value, "category": contract.category, \
                            "risk_factor": contract.risk_factor, "deductible": contract.deductible, \
                            "runtime": contract.runtime} for contract in self.underwritten_contracts if contract.reinsurance_share != 1.0]
            # TODO: Enable reinsurance shares other tan 0.0 and 1.0
            expected_profit, acceptable_by_category = self.riskmodel.evaluate(underwritten_risks, self.cash)

            #if expected_profit * 1./self.cash < self.profit_target:
            #    self.acceptance_threshold = ((self.acceptance_threshold - .4) * 5. * self.acceptance_threshold_friction) / 5. + .4
            #else:
            #    self.acceptance_threshold = (1 - self.acceptance_threshold_friction * (1 - (self.acceptance_threshold - .4) * 5.)) / 5. + .4

            growth_limit = max(50, 2 * len(self.underwritten_contracts) + contracts_dissolved)
            if sum(acceptable_by_category) > growth_limit:
                acceptable_by_category = np.asarray(acceptable_by_category)
                acceptable_by_category = acceptable_by_category * growth_limit / sum(acceptable_by_category)
                acceptable_by_category = np.int64(np.round(acceptable_by_category))

            not_accepted_risks = []
            for categ_id in range(len(acceptable_by_category)):
                categ_risks = [risk for risk in new_risks if risk["category"] == categ_id]
                new_risks = [risk for risk in new_risks if risk["category"] != categ_id]
                categ_risks = sorted(categ_risks, key = lambda risk: risk["risk_factor"])
                i = 0
                print("InsuranceFirm underwrote: ", len(self.underwritten_contracts), " will accept: ", acceptable_by_category[categ_id], " out of ", len(categ_risks), "acceptance threshold: ", self.acceptance_threshold)
                while (acceptable_by_category[categ_id] > 0 and len(categ_risks) > i): #\
                    #and categ_risks[i]["risk_factor"] < self.acceptance_threshold):
                    if categ_risks[i].get("contract") is not None: #categ_risks[i]["reinsurance"]:
                        if categ_risks[i]["contract"].expiration > time:    # required to rule out contracts that have exploded in the meantime
                            #print("ACCEPTING", categ_risks[i]["contract"].expiration, categ_risks[i]["expiration"], categ_risks[i]["identifier"], categ_risks[i].get("contract").terminating)
                            contract = ReinsuranceContract(self, categ_risks[i], time, \
                                          self.simulation.get_market_premium(), categ_risks[i]["expiration"] - time, self.default_contract_payment_period)  # TODO: make second-to-last agrument less convoluted, but consistent with insurancefirm
                            self.underwritten_contracts.append(contract)
                            #categ_risks[i]["contract"].reincontract = contract
                            # TODO: move this to insurancecontract (ca. line 14) -> DONE
                            # TODO: do not write into other object's properties, use setter -> DONE

                            assert categ_risks[i]["contract"].expiration >= contract.expiration, "Reinsurancecontract lasts longer than insurancecontract: {0:d}>{1:d} (EXPIRATION2: {2:d} Time: {3:d})".format(contract.expiration, categ_risks[i]["contract"].expiration, categ_risks[i]["expiration"], time)
                        #else:
                        #    pass
                    else:
                        contract = InsuranceContract(self, categ_risks[i], time, self.simulation.get_market_premium(), self.contract_runtime_dist.rvs(), self.default_contract_payment_period)
                        self.underwritten_contracts.append(contract)
                    acceptable_by_category[categ_id] -= 1   # TODO: allow different values per risk (i.e. sum over value (and reinsurance_share) or exposure instead of counting)
                    i += 1

                not_accepted_risks += categ_risks[i:]
                not_accepted_risks = [risk for risk in not_accepted_risks if risk.get("contract") is None]

            # seek reinsurance
            if self.is_insurer:
                # TODO: Why should only insurers be able to get reinsurance (not reinsurers)? (Technically, it should work)
                self.ask_reinsurance()

            # return unacceptables
            #print(self.id, " now has ", len(self.underwritten_contracts), " & returns ", len(not_accepted_risks))
            self.simulation.return_risks(not_accepted_risks)

            #not implemented
            #"""adjust liquidity, borrow or invest"""
            #pass

    def enter_illiquidity(self, time):
        self.enter_bankruptcy(time)

    def enter_bankruptcy(self, time):
        [contract.dissolve(time) for contract in self.underwritten_contracts]   # removing (dissolving) all risks immediately after bankruptcy (may not be realistic, they might instead be bought by another company)
        self.simulation.receive(self.cash)
        self.cash = 0
        self.operational = False

    def receive_obligation(self, amount, recipient, due_time):
        obligation = {"amount": amount, "recipient": recipient, "due_time": due_time}
        self.obligations.append(obligation)

    def effect_payments(self, time):
        due = [item for item in self.obligations if item["due_time"]<=time]
        self.obligations = [item for item in self.obligations if item["due_time"]>time]
        sum_due = sum([item["amount"] for item in due])
        if sum_due > self.cash:
            self.obligations += due
            self.enter_illiquidity(time)
        else:
            for obligation in due:
                self.pay(obligation["amount"], obligation["recipient"])


    def pay(self, amount, recipient):
        self.cash -= amount
        recipient.receive(amount)

    def receive(self, amount):
        """Method to accept cash payments."""
        self.cash += amount

    def obtain_yield(self, time):
        amount = self.cash * self.interest_rate
        self.simulation.receive_obligation(amount, self, time)
    
    def ask_reinsurance(self):
        if self.simulation_reinsurance_type == 'proportional':
            self.ask_reinsurance_proportional()
        elif self.simulation_reinsurance_type == 'non-proportional':
            self.ask_reinsurance_non_proportional()
        else:
            assert False, "Undefined reinsurance type"
        
    def ask_reinsurance_non_proportional(self):
        pass

    @nb.jit
    def ask_reinsurance_proportional(self):
        nonreinsured = []
        for contract in self.underwritten_contracts:
            if contract.reincontract == None:
                nonreinsured.append(contract)

        #nonreinsured_b = [contract
        #                for contract in self.underwritten_contracts
        #                if contract.reincontract == None]
        #
        #try:
        #    assert nonreinsured == nonreinsured_b
        #except:
        #    pdb.set_trace()

        nonreinsured.reverse()

        if len(nonreinsured) >= (1 - self.reinsurance_limit) * len(self.underwritten_contracts):
            counter = 0
            limitrein = len(nonreinsured) - (1 - self.reinsurance_limit) * len(self.underwritten_contracts)
            for contract in nonreinsured:
                if counter < limitrein:
                    risk = {"value": contract.value, "category": contract.category, "owner": self,
                            #"identifier": uuid.uuid1(),
                            "reinsurance_share": 1.,
                            "expiration": contract.expiration, "contract": contract,
                            "risk_factor": contract.risk_factor}

                    #print("CREATING", risk["expiration"], contract.expiration, risk["contract"].expiration, risk["identifier"])
                    self.simulation.append_reinrisks(risk)
                    counter += 1
                else:
                    break

    def get_cash(self):
        return self.cash

    def logme(self):
        self.log('cash', self.cash)
        self.log('underwritten_contracts', self.underwritten_contracts)
        self.log('operational', self.operational)

    #def zeros(self):
    #    return 0

    def len_underwritten_contracts(self):
        return len(self.underwritten_contracts)

    def get_operational(self):
        return self.operational

    def get_underwritten_contracts(self):
        return self.underwritten_contracts
    
    def get_pointer(self):
        return self
