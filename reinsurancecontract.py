
from insurancecontract import InsuranceContract 

class ReinsuranceContract(InsuranceContract):
    def mature(self):
        pass
        
    def explode(self, expire_immediately, time):
        if expire_immediately:
            self.expiration = time
