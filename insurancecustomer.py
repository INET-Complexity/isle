"""
 InsuranceCustomer agent class for ISLE.
 
 Created by Torsten Heinrich, Davoud Taghawi-Nejad.
"""

# import general python modules
import random
import pdb

# import abce modules
import abce

# import ISLE modules
#from insurablerisk import InsurableRisk
from categorizedinsurablerisk import CategorizedInsurableRisk
from insurancecontract import InsuranceContract

# InsuranceCustomer class
class InsuranceCustomer(abce.Agent):
    def init(self, simulation_parameters, agent_parameters):
        """Quasi-Constructor method (init, not __init--). Inherits from abce.Agent, requires 2 positional arguments 
           (lists of (1) simulation parameters and (2) agent parameters) as specified in abce.Agent.
           Returns None.
           Creates insurance curtomer agent, records agent properties
        """
        
        # Record properties.
        self.num_insurers = simulation_parameters['numberOfInsurers']
        self.create('money', simulation_parameters['start_cash_customer'])
        self.default_contract_runtime = simulation_parameters['defaultContractRuntime']
        self.default_contract_excess = simulation_parameters['defaultContractExcess']
        self.time_correlation_weight = simulation_parameters['shareOfCorrelatedRisk']
        
        # Prepare variables for handling risks, contracts, obligations
        self.i_contracts = []
        self.risks = []
        self.insurance_contract_dict = {}
        self.risk_dict = {}
        self.obligations_current_round = 0.
    
    #Workaround for collecting agent pointer. To be removed in future version.
    def get_object(self):
        return self

    def startAddRisk(self, number, max_runtime, risk_category_list, eventDist = None, eventSizeDist = None, \
                    bernoulliDistCategory = None, bernoulliDistIndividual = None):
        """Method to add multiple risks at the beginning of the simulation. 3 positional Arguments:
             number (int): number of risks to be added.
             max_runtime (int): end time of the simulation (= number of iterations, as this method is executed 
                                                                                                in iteration 0
             risk_category_list (nested list): list of risk categories present in the simulation.
           Optional arguments:
             eventDist (rv frozen distribution): damage event separation time distribution
             eventSizeDist (rv frozen distribution): damage size distribution
             bernoulliDistCategory (rv frozen distribution): bernoulli distribution for eventschedule mixing.
             bernoulliDistIndividual (rv frozen distribution): bernoulli distribution for eventschedule mixing.
           Returns (list of float): event times
           Note: The bernoulli distriutions are handed over as arguments to save computation time.
        """
        events = []
        for i in range(number): # Loop over the number of risks to be created
            if (eventDist is not None) and (eventSizeDist is not None) and (bernoulliDistIndividual is not None) \
                                                                              and (bernoulliDistCategory is not None):
                # Create risk supplying predefined distributions (computationally efficient but uniform)
                risk = CategorizedInsurableRisk(self.time, max_runtime, risk_category_list, eventDist=eventDist, \
                        eventSizeDist=eventSizeDist, time_correlation_weight=self.time_correlation_weight, \
                        bernoulliDistIndividual=bernoulliDistIndividual, bernoulliDistCategory=bernoulliDistCategory)
            else:
                # Create risk using default distributions
                risk = CategorizedInsurableRisk(self.time, max_runtime, risk_category_list, \
                                                 time_correlation_weight=self.time_correlation_weight)

                # Print warning if some but not all distributions have been supplied and were ignored
                if (eventDist is not None) or (eventSizeDist is not None) or (bernoulliDistCategory is not None) \
                                                                              or (bernoulliDistIndividual is not None):
                    print("""Warning: received only one of four frozen rv distributions for insurable risk. All are 
                                                needed to characterize risk. Defaulting to assigning defaults for all.""")
            
            # Record risk and risk event schedule
            self.risks.append(risk)
            events.append(risk.schedule_next_event(self.round))
            self.risk_dict[risk.uuid] = risk
        return events

    def randomAddRisk(self, prob_add = .9):        # Not used.
        """Method to add a single risk with a certain probability. Optional argument
             prob_add (float >=0, <=1): probability that a risk is added"""
        if random.random() > prob_add:
            # Create risk (with default distributions)
            risk = InsurableRisk(self.round)
            # Record risk
            self.risks.append(risk)
            self.requestInsuranceCoverage(risk)
            #risk.set_coverage()	#risk does not need this information
            retv =  risk.schedule_next_event(self.round)
            #print(retv)
            return retv
        else:
            return None, None

    def randomAddCoverage(self):    #TODO: rename appropriately, this is not random
        """Method to add coverage to existing uninsured risks. No arguments; returns None."""
        
        # Shuffle risks (so that different risks are considered first in different iterations)
        random.shuffle(self.risks)
        for risk in self.risks: # Loop through risks
            
            #if self.id==0: print("DEBUG IC randomaddcoverage: ", risk.get_coverage(), risk.uuid)
            
            # Request coverage from if risk is not insured.
            """In the first (default_contract_runtime + 1) iterations, the firm seeks coverage for only a part of the 
               risks to avoid the effect of simultaneous initialization. In effect, the risks are phased in to equal 
               parts in every iteration""" # TODO: do this in a more generic way?
            if not risk.get_coverage() and (self.round >= self.default_contract_runtime + 1 \
                                             or random.random() < 1./(self.default_contract_runtime + 1. - self.round)):
                #if self.id==0: print("DEBUG IC randomaddcoverage: Coverage requested")
                self.requestInsuranceCoverage(risk, self.default_contract_runtime, self.default_contract_excess)

    def requestInsuranceCoverage(self, risk, runtime = None, excess = None):
        """Method for requesting coverage for a single uninsured risk. Positional argument:
             risk (InsurableRisk object): risk to be insured
           Optional arguments:
             runtime (float) runtime requested
             excess (float): excess requested
           Returns None. Sends messages."""
        
        # If runtime is not given, use runtime of the risk
        if runtime is None:
            assert risk.runtime is not None
            runtime = risk.runtime
        # If excess is not given, use value of the risk
        if excess is None:
            assert risk.value is not None
            runtime = risk.value
        # Request offers from every insurer
        for i in range(self.num_insurers):
            self.message('insurancefirm', i, 'request_insurancequote', 
                                { 'risk': risk.uuid,
                                  'riskcat': risk.category_id,
                                  'runtime': runtime,
                                  'excess': excess,
                                  'deductible': 0.0,
                                  'time_correlation_weight': risk.time_correlation_weight})

    def subscribe_coverage(self):
        """Method to accept best (cheapest) received offers for coverage of any uninsured risk. 
           No arguments, returns None."""
        # Collect offers
        messages = self.get_messages('insurancequotes')
        if len(messages) > 0:
            # Collect risks (unique IDs) for which offers have been received
            riskuuids = set([message.content[4] for message in messages])
            for riskuuid in riskuuids:
                # Sort offers by risk. (Technically: For all risks, select offers for that risk.)
                filtered_messages = [message for message in messages if message.content[4]==riskuuid]
                # Select best offer
                cc = min(filtered_messages, key=lambda x: x.content)
                if cc.content[0] < self.possession('money'):
                    
                    # If agent has enough money to pay the premium, accept this offer
                    
                    # Get risk that is being insured.
                    #risk = cc.content[4]
                    risk = self.risk_dict[riskuuid]
                    
                    # Create contract.
                    new_contract = InsuranceContract({'policyholder': self.name,
                                                      'insurer':  (cc.sender_group, cc.sender_id)},
                                                     endtime=cc.content[1] + self.round,
                                                     risk=riskuuid,
                                                     riskcat=risk.category_id,
                                                     premium=cc.content[0],
                                                     excess=cc.content[2],
                                                     deductible=cc.content[3])
                    #print(type(new_contract), new_contract)
                    
                    # Inform insurer of acceptance.
                    self.message(cc.sender_group, cc.sender_id, 'addcontract', new_contract.__dict__)
                    
                    # Record contract, set risk covered
                    self.i_contracts.append(new_contract)
                    self.insurance_contract_dict[risk] = new_contract
                    risk.set_coverage(True)
            #else:
            #    print("not accepted, money: {0:8f}, content {1:8f}".format(self.possession('money'), cc.content))

    def filobl(self):
        """Method to effect all due payments (premiums in this case). No arguments; returns None."""
        
        # Reset payouts statistic
        self.obligations_current_round = 0
        for contract in self.i_contracts:                                 # Loop over all contracts
            if contract.get_obligations('policyholder')['money'] > 0:   # Test for obligations 
                
                # Collect due obligations for contract.
                payment_current_obligation = contract.get_obligations('policyholder')['money']
                # Record into payments statistic
                self.obligations_current_round += payment_current_obligation
                #print("DEBUG", contract.obligations)
                
                try:
                    # Effect payment
                    contract.fulfill_obligation(self,
                                            von='policyholder',
                                            to='insurer',
                                            delivery={'money': payment_current_obligation})
                except:
                    """Pass. Any future code handling customer bankruptcy should go here.
                       Currently, customer bankruptcy is not of interest for the simulation."""
                    #print("NotEnoughGoods raised: ", self.possession('money'))
                    #pdb.set_trace()
                    # TODO: this allows customers who cannot pay to keep the contracts nevertheless; may or may not be realistic but should be a relatively rare event
                    pass
        
        #print("DEBUG", self.possession('money'))
        
    def logging(self):
        """Logging method. Causes ABCE to log some values at agent level. No arguments, returns None."""        
        self.log('obligations', self.obligations_current_round)
        self.log('money', self.possession('money'))
        self.log('num_contracts', len(self.i_contracts))

    def check_risk(self):
        #print("DEBUG check_risk: ", end="")
        for risk in self.risks:
            #print("{0:f}".format(risk.damage), end="")
            if risk.damage > 0:
                #print(" ... DAMAGE".format(risk.damage))
                insurance_contract = self.insurance_contract_dict.get(risk)
                #insurance_contract = self.insurance_contract_dict[risk]
                if insurance_contract is not None:
                    insurance_contract.execute(risk.damage)
                try:
                    self.destroy('money', risk.damage)
                except abce.NotEnoughGoods:
                    pass
                #print(" risk ", risk)
                risk.set_damage(0)
                # TODO: reduce insurancecustomer's money to reflect damage paid

    def mature_contracts(self):
        """Method to remove expired contracts. No arguments; returns None."""
        # Terminate expired contracts
        [contract.terminate() for contract in self.i_contracts if (contract.get_endtime() < self.round)]
        # Rebuild contracts list
        self.i_contracts = [contract for contract in self.i_contracts if (contract.is_valid())]

        # Rebuild insurance_contract_dict
        #self.insurance_contract_dict = {risk: self.insurance_contract_dict[risk] for risk in self.insurance_contract_dict if not self.insurance_contract_dict[risk].is_valid()}
        new_insurance_contract_dict = {}
        for risk in self.insurance_contract_dict:
            contract = self.insurance_contract_dict[risk]
            if contract.is_valid():
                new_insurance_contract_dict[risk] = contract
            else:
                risk.set_coverage(False)
        self.insurance_contract_dict = new_insurance_contract_dict
        #print(type(self.insurance_contract_dict), len(self.insurance_contract_dict))

    def printmoney(self):
        """Method to print current liquidity holdings of this agent. No arguments; returns None."""
        print("Agent (InsuranceCustomer) has cash: ", self.possession('money'))

    def get_mean_coverage(self):        #TODO: Is this method still used? Delete or rename to more intuitive name.
        """Method to get share of covered risks of this agent. No arguments; 
             Returns (float): share of covered risks."""
        #if self.id==0: print([1 for risk in self.risks if risk.get_coverage()])
        return sum([1 for risk in self.risks if risk.get_coverage()]) * 1. / len(self.risks) 
