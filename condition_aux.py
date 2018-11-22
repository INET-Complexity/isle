"""Auxiliary functions and data for calibration test functions"""

import numpy as np


"""Data"""

"""Bloomberg size data for US firms"""
insurance_firm_sizes_empirical_2017 = [42.4701, 108.0418, 110.2641, 114.437, 130.2988, 133.674, 146.438, 152.3354, 
                                       239.032, 337.689, 375.914, 376.988, 395.859, 436.191, 482.503, 585.824, 667.849, 
                                       842.264, 894.848, 896.227, 904.873, 1231.126, 1357.016, 1454.999, 1518.236, 
                                       1665.859, 1681.94, 1737.9198, 1771.21, 1807.279, 1989.742, 2059.921, 2385.485, 
                                       2756.695, 2947.244, 3014.3, 3659.2, 3840.1, 4183.431, 4929.197, 5101.323, 
                                       5224.622, 5900.881, 7686.431, 8376.2, 8439.743, 8764.0, 9095.0, 11198.34, 
                                       14433.0, 15469.6, 19403.5, 21843.0, 23192.374, 24299.917, 25218.63, 31843.0, 
                                       32051.658, 32805.016, 38701.2, 56567.0, 60658.0, 79586.0, 103483.0, 112422.0, 
                                       167022.0, 225260.0, 498301.0, 702095.0]
reinsurance_firm_sizes_empirical_2017 = [396.898, 627.808, 6644.189, 15226.131, 25384.317, 23591.792, 3357.393, 
                                         13606.422, 4671.794, 614.121, 60514.818, 24760.177, 2001.669, 182.2, 12906.4]

"""Functions"""

def condition_stationary_state(series):
    """Stationarity test function for time series. Tests if the mean of the last 25% of the time series is within 1-2
       standard deviation of the mean of the middle section (between 25% and 75% of the time series). The first
       25% are not considered to discard the transient.
        Arguments:
            series: Type list of numeric or numpy array. The time series
        Returns:
            Calibration score between 0 and 1. Is 1 if last 25% are within one standard deviation, between 0 and 1 if
                they are between 1 and 2 standard deviations, 0 otherwise."""
                
    """Compute means and standard deviation"""
    mean_reference = np.mean(series[int(len(series)*.25):int(len(series)*.75)])
    std_reference = np.std(series[int(len(series)*.25):int(len(series)*.75)])
    mean_test = np.mean(series[int(len(series)*.75):int(len(series)*1.)])
    
    """Compute score"""
    score = 1 + (np.abs(mean_test - mean_reference) - std_reference) / std_reference
    score = 1 if score>1 else score
    score = 0 if score<0 else score
    
    """Set score to one if standard deviation is zero"""
    if score == np.nan and np.std(series[int(len(series)*.25):int(len(series)*.75)]) == 0:
        score = 1
    return score
    

def scaler(series): # TODO: find a better way to scale heavy-tailed distributions than to use standard score scaling on logs 
    """Function to do a standard score scaling of the log of a heavy-tailed distribution. This is used to calibrate
       distributions where the unit is not important (distributions of sizes of firms e.g.). This would be perfectly
       appropriate for lognormal distributions, but should work reasonably well for calibration of other heavy-tailed 
       distributions. An alternative would be a scaling robust towards outliers (as included in the sklearn package).
        Arguments:
            series: Type list of numeric or numpy array. The time series
        Returns:
            Calibratied series."""
    series = np.asarray(series)
    assert (series>1).all()
    logseries = np.log(series)
    mean = np.mean(logseries)
    std = np.std(logseries)
    z = (logseries - mean)/std
    newseries = np.exp(z)
    return newseries
