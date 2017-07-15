"""
 InsuranceFirm agent class for ISLE.
 
 Created by Torsten Heinrich, Davoud Taghawi-Nejad.
"""

# import general python modules
from __future__ import division
import pdb
import scipy.stats

# import ABCE modules
import abce

# import ISLE modules: InsuranceContract and one of the RiskModel classes.
from insurancecontract import InsuranceContract
#from riskmodel import RiskModel
#from riskmodel_grouped import RiskModelGrouped
#from riskmodel_grouped_iterationstatic import RiskModelGroupedS
from riskmodel_grouped_deterministic import RiskModelGroupedDeterministic

# InsuranceFirm class
class InsuranceFirm(abce.Agent):
    def init(self, simulation_parameters, agent_parameters):
        """Quasi-Constructor method (init, not __init--). Inherits from abce.Agent, requires 2 positional arguments 
           (lists of (1) simulation parameters and (2) agent parameters) as specified in abce.Agent.
           Returns None.
           Creates insurance firm agent, records agent properties
        """
        # Record properties
        self.riskmodel = RiskModelGroupedDeterministic(riskDistribution=scipy.stats.pareto(2., 0., 10.), \
                                                                               riskPeriod=scipy.stats.expon(0, 100./3.))
        self.create('money', simulation_parameters['start_cash_insurer'])
        self.start_cash_insurer = simulation_parameters['start_cash_insurer']
        self.alive = True
        self.defaulted_numeric = 0.	# This is 0 if self.alive is True, 1 otherwise. We need this to make logging of the 
                                    # number of defaulted firms possible. TODO: Switch to simulation-level logging.
        
        # Prepare variables for handling contracts and claim payouts
        self.contracts = []
        self.underwritten_by_cat = [[0 for i in range(simulation_parameters['numberOfRiskCategories'])] \
                                                for j in range(simulation_parameters['numberOfRiskCategoryDimensions'])]
        self.insurance_payouts = 0.

    #Workaround for collecting agent pointer. To be removed in future version.
    def get_object(self):
        return self

    def set_oblivious(self, risk_cat_dim):
        """Method to set (in)ability to consider specific risk categories in underwriting decisions. Positional argument:
             risk_cat_dim (int: 0, 1): which part (dimension) of risk categories to set invisible to insurer.
             Returns None.
             TODO: Shift this to the risk model instead of the insurer.
           """
        self.underwritten_by_cat[risk_cat_dim] = None

    def quote(self):
        """Method to consider risks, create, and send offers. No arguments, returns None. Handles and sends messages."""
        for request in self.get_messages('request_insurancequote'):     # loop through all offer requests
            quote = self.acceptInsuranceContract(request.content)       # get premium quote (if None, the risk cannot be 
                                                                        #                                   underwritten)
            if quote is not None:
                self.message(request.sender_group, request.sender_id, 'insurancequotes', quote)

    def acceptInsuranceContract(self, request):
        """Method to consider underwriting a risk and obtain premium quote. Positional argument:
             request (dict): request for insurance contract offer.
           Returns premium quote (float or None).
           """
        if self.alive:  # Only return quotes if insurance firm is not bankrupted yet. TODO: Move this to quote function.
            """Set consistent maximum liquidity holdings. TODO: Model this and the investment of the remainder in 
                                                                                    long-term investments explicitly."""
            liquidity = min(self.possession('money'), self.start_cash_insurer)
            # Call RiskModel.evaluate to determine premium and whether or not to underwrite
            return self.riskmodel.evaluate(request['risk'], request['riskcat'], request['runtime'], request['excess'] , request['deductible'],  request['time_correlation_weight'], self.underwritten_by_cat, liquidity, time=self.round)
            #return self.riskmodel.evaluate(request['runtime'], request['excess'] , request['deductible'])
        else:
            return None

    def add_contract(self):
        """Method to record accepted contracts. No arguments, returns None.
           The method copies insurance customer's contract object identically. This is because insurance customer and 
           self may run in different processes."""
        #revenue_sum = 0
        for contract in self.get_messages('addcontract'):
            # Copy contract object.
            self.contracts.append(InsuranceContract.generated(contract.content))
            # Record underwritten risk by category.
            for i in range(len(self.underwritten_by_cat)):
                if self.underwritten_by_cat[i] is not None:
                    risk_cat_current_contract = self.contracts[-1].risk_category[i]
                    if risk_cat_current_contract is not None:
                        self.underwritten_by_cat[i][risk_cat_current_contract] += 1
            #revenue_sum += contract.content["premium"]
        #try:
        #    print("DEBUG InsuranceFirm {0:d} money in: {1:f}".format(self.id, revenue_sum))
        #except:
        #    pdb.set_trace()
        

    def filobl(self):
        """Method to effect all due payments (reimbursements for claims in this case). No arguments; returns None."""
        #print("DEBUG InsuranceFirm {0:d} money: {1:f}".format(self.id,self.possession('money')))
        
        # Reset payouts statistic
        self.insurance_payouts = 0 
        
        for contract in self.contracts:     # Loop over all contracts
            # Collect due payments from contract.
            current_payout = contract.get_obligation('insurer', 'money')
            
            if current_payout > 0:
                try:
                    # Effect payment
                    contract.fulfill_obligation(self,
                                            von='insurer',
                                            to='policyholder',
                                            delivery={'money': current_payout})
                    # Record payment in payouts statistic.
                    self.insurance_payouts += current_payout
                except abce.NotEnoughGoods:
                    # Enter bankruptcy if agent has insufficient liquidity to complete payment.
                    self.bankrupt()
                #print("DEBUG: Booked claim payout ", current_payout)
        
    def logging(self):
        """Logging method. Causes ABCE to log some values at agent level. No arguments, returns None."""
        self.log('insurancepayouts', self.insurance_payouts)
        self.log('money', self.possession('money'))
        self.log('num_contracts', len(self.contracts))
        self.log('defaulted', int(self.defaulted_numeric))	
        """ TODO: some data series sometimes do not produce aggregated statistics in the graphical representation 
               -> but logging works fine (csv file has correct data)
               -> it seems unrelated to data type (float or int) or how it is created"""

    def bankrupt(self):
        """Method to set agent bankrupt. This will cause the agent to not enter new contracts in the future. 
           No arguments; returns None."""
        self.alive = False
        self.defaulted_numeric = 1.
    
    def is_bankrupt(self):		#not used
        """Getter method for bankruptcy status. No arguments.
             Returns (boolean): whether the firm is bankrupt."""
        return not self.alive

    def mature_contracts(self):
        """Method to remove expired contracts. No arguments; returns None."""
        # TODO: does this work with multiprocessing?
        #       -> should work, but it may be good to check that firm and customer agree on contract ending time
        for contract in self.contracts: # Loop through all contracts of this agent.
            if (contract.get_endtime() < self.round):   # Test if expired.
                # Terminate contract.
                contract.terminate() 
                # Remove contract from statistic of underwritten risks by category   
                for i in range(len(self.underwritten_by_cat)):
                    if (self.underwritten_by_cat[i] is not None) and (contract.risk_category[i] is not None):
                        self.underwritten_by_cat[i][contract.risk_category[i]] -= 1
        # Rebuild agent's contracts list to only include non-terminated contracts.
        self.contracts = [contract for contract in self.contracts if (contract.is_valid())]

        # Remove excess liquidity. TODO: Should be done with investments instead.
        if self.possession('money') > self.start_cash_insurer:
            self.create('longterm_investment', self.possession('money') - self.start_cash_insurer)
            self.destroy('money', self.possession('money') - self.start_cash_insurer)


    def printmoney(self):
        """Method to print current liquidity holdings of this agent. No arguments; returns None."""
        print("Agent (InsuranceFirm) has cash: ", self.possession('money'))
