"""Collection of calibration test conditions as functions to be imported by the CalibrationScore class.
   Each function accepts a Logger object as argument and runs the tests on this. Auxiliary functions are
   in calibration_aux.py.
   
Components of Logger log, that can used for validation/calibration are:

                [0]: 'total_cash'
                [1]: 'total_excess_capital'
                [2]: 'total_profitslosses'
                [3]: 'total_contracts'
                [5]: 'total_reincash'
                [6]: 'total_reinexcess_capital'
                [7]: 'total_reinprofitslosses'
                [8]: 'total_reincontracts'
                [9]: 'total_reinoperational'
                [10]: 'total_catbondsoperational'
                [11]: 'market_premium'
                [12]: 'market_reinpremium'
                [13]: 'cumulative_bankruptcies'
                [14]: 'cumulative_unrecovered_claims'
                [15]: 'cumulative_claims'
                [16]: 'insurance_firms_cash'
                [17]: 'reinsurance_firms_cash'
                [18]: 'market_diffvar'
                [19]: rc_event_schedule_initial
                [20]: rc_event_damage_initial
                [21]: number_riskmodels
"""

from scipy import stats
import condition_aux
import isleconfig

def condition_stationary_state_cash(logobj):
    """Stationarity test for total cash"""
    return condition_aux.condition_stationary_state(logobj.history_logs['total_cash'])
    
def condition_stationary_state_excess_capital(logobj):
    """Stationarity test for total excess capital"""
    return condition_aux.condition_stationary_state(logobj.history_logs['total_excess_capital'])

def condition_stationary_state_profits_losses(logobj):
    """Stationarity test for total profits and losses"""
    return condition_aux.condition_stationary_state(logobj.history_logs['total_profitslosses'])

def condition_stationary_state_contracts(logobj):
    """Stationarity test for total number of contracts"""
    return condition_aux.condition_stationary_state(logobj.history_logs['total_contracts'])

def condition_stationary_state_rein_cash(logobj):
    """Stationarity test for total cash (reinsurers)"""
    return condition_aux.condition_stationary_state(logobj.history_logs['total_reincash'])

def condition_stationary_state_rein_excess_capital(logobj):
    """Stationarity test for total excess capital (reinsurers)"""
    return condition_aux.condition_stationary_state(logobj.history_logs['total_reinexcess_capital'])

def condition_stationary_state_rein_profits_losses(logobj):
    """Stationarity test for total profits and losses (reinsurers)"""
    return condition_aux.condition_stationary_state(logobj.history_logs['total_reinprofitslosses'])

def condition_stationary_state_rein_contracts(logobj):
    """Stationarity test for total number of reinsured contracts"""
    return condition_aux.condition_stationary_state(logobj.history_logs['total_reincontracts'])

def condition_stationary_state_market_premium(logobj):
    """Stationarity test for insurance market premium"""
    return condition_aux.condition_stationary_state(logobj.history_logs['market_premium'])

def condition_stationary_state_rein_market_premium(logobj):
    """Stationarity test for reinsurance market premium"""
    return condition_aux.condition_stationary_state(logobj.history_logs['market_reinpremium'])

def condition_defaults_insurance(logobj):          # TODO: develop this into a non-binary measure
    """Test for number of insurance bankruptcies (non zero, not all insurers)"""
    #series  = logobj.history_logs['total_operational']
    #if series[-1] != 0 and any(series[i]-series[i-1] < 0 for i in range(1,len(series))):
    opseries = [logobj.history_logs["insurance_firms_cash"][-1][i][2] for i in \
                        range(len(logobj.history_logs["insurance_firms_cash"][-1]))]
    if any(opseries) and not all(opseries):
        return 1
    else:
        return 0

def condition_defaults_reinsurance(logobj):        # TODO: develop this into a non-binary measure
    """Test for number of reinsurance bankruptcies (non zero, not all reinsurers)"""
    #series  = logobj.history_logs['total_reinoperational']
    #if series[-1] != 0 and any(series[i]-series[i-1] < 0 for i in range(1,len(series))):
    opseries = [logobj.history_logs["reinsurance_firms_cash"][-1][i][2] for i in \
                        range(len(logobj.history_logs["reinsurance_firms_cash"][-1]))]
    if any(opseries) and not all(opseries):
        return 1
    else:
        return 0

def condition_insurance_coverage(logobj):
    """Test for insurance coverage close to 100%"""
    return logobj.history_logs['total_contracts'][-1] * 1. / isleconfig.simulation_parameters["no_risks"]

def condition_reinsurance_coverage(logobj, minimum=0.6):
    """Test for reinsurance coverage close to some minimum that may be less than 100% (default 60%)"""
    score = logobj.history_logs['total_reincontracts'][-1] * 1. / (minimum * logobj.history_logs['total_contracts'][-1])
    score = 1 if score>1 else score
    return score

def condition_insurance_firm_dist(logobj):                 
    """Empirical calibration test for insurance firm size (total assets; cash)"""
    """filter operational firms"""
    #dist = [logobj.history_logs["insurance_firms_cash"][-1][i][0] for i in range(len(logobj.history_logs["insurance_firms_cash"])) if \
    #           logobj.history_logs["insurance_firms_cash"][-1][i][0] > isleconfig.simulation_parameters["cash_permanency_limit"]]
    dist = [logobj.history_logs["insurance_firms_cash"][-1][i][0] for i in \
                range(len(logobj.history_logs["insurance_firms_cash"][-1])) if \
                      logobj.history_logs["insurance_firms_cash"][-1][i][2]]
    """run two-sided KS test"""
    KS_statistic, p_value = stats.ks_2samp(condition_aux.scaler(condition_aux.insurance_firm_sizes_empirical_2017), 
                                           condition_aux.scaler(dist))
    return p_value

def condition_reinsurance_firm_dist(logobj):                 
    """Empirical calibration test for reinsurance firm size (total assets; cash)"""
    """filter operational firms"""
    #dist = [logobj.history_logs["reinsurance_firms_cash"][-1][i][0] for i in range(len(logobj.history_logs["reinsurance_firms_cash"])) if \
    #           logobj.history_logs["reinsurance_firms_cash"][-1][i][0] > isleconfig.simulation_parameters["cash_permanency_limit"]]
    dist = [logobj.history_logs["reinsurance_firms_cash"][-1][i][0] for i in \
                    range(len(logobj.history_logs["reinsurance_firms_cash"][-1])) if 
                    logobj.history_logs["reinsurance_firms_cash"][-1][i][2]]
    """run two-sided KS test"""
    KS_statistic, p_value = stats.ks_2samp(condition_aux.scaler(condition_aux.reinsurance_firm_sizes_empirical_2017), 
                                           condition_aux.scaler(dist))
    return p_value
