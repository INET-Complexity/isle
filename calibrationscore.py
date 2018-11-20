import logger
from inspect import getmembers, isfunction
import numpy as np

import calibration_conditions

class CalibrationScore():
    def __init__(self, L):
        assert isinstance(L, logger.Logger)
        self.logger = L
        self.conditions = [f for f in getmembers(calibration_conditions) if isfunction(f[1])]
        self.calibration_score = None
        
    def test_all(self):
        scores = {condition[0]: condition[1](self.logger) for condition in self.conditions}
        print("\n")
        for cond_name, score in scores.items():
            print("{0:47s}: {1:8f}".format(cond_name, score))
        self.calibration_score = self.combine_scores(np.array([*scores.values()], dtype=object))
        print("\n                        Total calibration score: {0:8f}".format(self.calibration_score))
        return self.calibration_score
    
    def combine_scores(self, slist):
        return np.nanmean(slist)
