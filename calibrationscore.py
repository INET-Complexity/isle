"""CalibrationScore class. Defines calibration score object. Can compute and print the calibration score
   based on functions imported from calibration_conditions.py by component and combined."""

import logger
from inspect import getmembers, isfunction
import numpy as np

import calibration_conditions   # Test functions

class CalibrationScore():
    def __init__(self, L):
        """Constructor method.
            Arguments:
                L: Type: Logger object. The log of a single simulation run.
            Returns instance."""

        """Assert sanity of log and save log."""
        assert isinstance(L, logger.Logger)
        self.logger = L
        
        """Prepare list of calibration tests from calibration_conditions.py"""
        self.conditions = [f for f in getmembers(calibration_conditions) if isfunction(f[1])]
        
        """Prepare calibration score variable."""
        self.calibration_score = None
        
    def test_all(self):
        """Method to test all calibration tests.
            No arguments.
            Returns combined calibration score as float \in [0,1]."""
        
        """Compute score components"""
        scores = {condition[0]: condition[1](self.logger) for condition in self.conditions}
        """Print components"""
        print("\n")
        for cond_name, score in scores.items():
            print("{0:47s}: {1:8f}".format(cond_name, score))
        """Compute combined score"""
        self.calibration_score = self.combine_scores(np.array([*scores.values()], dtype=object))
        """Print combined score"""
        print("\n                        Total calibration score: {0:8f}".format(self.calibration_score))
        """Return"""
        return self.calibration_score
    
    def combine_scores(self, slist):
        """Method to combine calibration score components. Combination is additive (mean). Change the function
           for other combination methods (multiplicative or minimum).
            Arguments:
                slist: Type list of numeric or numpy array. List of component calibration scores.
            Returns combined calibration score."""
        return np.nanmean(slist)
