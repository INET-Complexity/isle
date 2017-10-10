
import numpy as np
import scipy.stats
from insurancecontract import InsuranceContract 
import sys, pdb
import uuid

class InsuranceFirm():
    def __init__(self, simulation, simulation_parameters, agent_parameters):
        self.simulation = simulation
        ##or: ABCE style:
        #def init(self, simulation_parameters, agent_parameters):
        ##note that ABCE-style cannot have a pointer to the simulation. It should deal with customers directly instead.
        self.contract_runtime_dist = scipy.stats.randint(simulation_parameters["mean_contract_runtime"] - \
                  simulation_parameters["contract_runtime_halfspread"], simulation_parameters["mean_contract_runtime"] \
                  + simulation_parameters["contract_runtime_halfspread"] + 1)
        self.id = agent_parameters['id']
        self.cash = agent_parameters['initial_cash']
        self.riskmodel = agent_parameters['riskmodel']
        self.premium = agent_parameters["norm_premium"]
        self.profit_target = agent_parameters['profit_target']
        self.acceptance_threshold = agent_parameters['initial_acceptance_threshold']  # 0.5
        self.acceptance_threshold_friction = agent_parameters['acceptance_threshold_friction']  # 0.9 #1.0 to switch off
        self.obligations = []
        self.underwritten_contracts = []
        #self.reinsurance_contracts = []
        self.operational = True
        
    def iterate(self, time):
        #"""realize income: not necessary"""
        #pass

        self.ans_reinsurance()
        
        """realize due payments"""
        self.effect_payments(time)
        print(time, ":", self.id, len(self.underwritten_contracts), self.cash, self.operational)

        """mature contracts"""
        maturing = [contract for contract in self.underwritten_contracts if contract.expiration <= time]
        for contract in maturing:
            self.underwritten_contracts.remove(contract)
            contract.mature()
        contracts_dissolved = len(maturing)
        
        if self.operational:
            # Only for ABCE:
            #"""collect messages"""
            #self.obligations += [obligation.content for obligation in self.get_messages('obligation')]
            
            """request risks to be considered for underwriting in the next period and collect those for this period"""
            # Non-ABCE style
            new_risks = self.simulation.solicit_insurance_requests(self.id, self.cash)
            ## ABCE style
            #self.message("insurancecustomer", 0, 'solicit_insurance_requests', {"number": self.posession("money")})
            #new_risks = []
            #for new_risks in self.get_messages('new_risks')
            #    new_risks += new_risks.content
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
                try:
                    while(acceptable_by_category[categ_id] > 0 and len(categ_risks) > i): #\
                        #and categ_risks[i]["risk_factor"] < self.acceptance_threshold):
                        contract = InsuranceContract(self, categ_risks[i], time, self.simulation.get_market_premium(), self.contract_runtime_dist.rvs())
                        self.underwritten_contracts.append(contract)
                        acceptable_by_category[categ_id] -= 1
                        i += 1
                except:
                    print(sys.exc_info())
                    pdb.set_trace()
                not_accepted_risks += categ_risks[i:]
                
            #return unacceptables
            #print(self.id, " now has ", len(self.underwritten_contracts), " & returns ", len(not_accepted_risks))

            self.ask_reinsurance()

            self.simulation.return_risks(not_accepted_risks)
    
            #not implemented
            #"""adjust liquidity, borrow or invest"""
            #pass
        else:
            pass
            #Non-ABCE style not required
            #self.simulation.return_risks(self.simulation.solicit_insurance_requests(0))
            #ABCE style:
            # ...requires collecting message with risks like above and sending the all back
        
    def enter_illiquidity(self):
        self.enter_bankruptcy()
    
    def enter_bankruptcy(self):
        [risk.mature() for risk in self.underwritten_contracts]   # removing (maturing) all risks immediately after bankruptcy (may not be realistic, they might instead be bought by another company)
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
            self.enter_illiquidity()
        else:
            for obligation in due:
                self.pay(obligation["amount"], obligation["recipient"])

    
    def pay(self, amount, recipient):
        ## ABCE style:
        #self.give(self, recipient, "cash", amount)
        # Non-ABCE style:
        self.cash -= amount
        recipient.receive(amount)
                
    def receive(self, amount):
        ## Not necessary in ABCE style
        #pass
        # Non-ABCE style
        """Method to accept cash payments."""
        self.cash += amount

    def ask_reinsurance(self):
        nonreinsured = [contract
                        for contract in self.underwritten_contracts
                        if contract.reinrisk == None]
        counter = 0
        limitrein = 0.1 * len(nonreinsured)
        for contract in nonreinsured:
            if counter < limitrein:
                reinvalue = 0
                risk = {"value": contract.value, "category": contract.category, "owner": self,
                        "identifier": uuid.uuid1(),
                        "expiration": contract.expiration, "contract": contract,
                        "risk_factor": contract.risk_factor}
                contract.reinsure(1.)  # TODO percentage to floating point number
                contract.reinrisk = risk["identifier"]
                self.simulation.append_reinrisks(risk)
                counter += 1
            else:
                break

    def ans_reinsurance(self):
        to_remove = []
        #print(self.simulation.reinrisks)
        for rein in self.simulation.get_reinrisks():
            for contract in self.underwritten_contracts:
                if (rein["identifier"] == contract.reinrisk):
                    contract.reinsure(0)
                    contract.reinrisk = None
                    contract.reinsurer = None
                    contract.reincontract = None
                    to_remove.append(rein)

        for item in to_remove:
            self.simulation.remove_reinrisks(item)



