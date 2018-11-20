import numpy as np

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

def condition_stationary_state(series):
    mean_reference = np.mean(series[int(len(series)*.25):int(len(series)*.75)])
    std_reference = np.std(series[int(len(series)*.25):int(len(series)*.75)])
    mean_test = np.mean(series[int(len(series)*.75):int(len(series)*1.)])
    score = 1 + (np.abs(mean_test - mean_reference) - std_reference) / std_reference
    score = 1 if score>1 else score
    score = 0 if score<0 else score
    return score
    

def scaler(series): # TODO: find a better way to scale heavy-tailed distributions than to use standard score scaling on logs 
    series = np.asarray(series)
    assert (series>1).all()
    logseries = np.log(series)
    mean = np.mean(logseries)
    std = np.std(logseries)
    z = (logseries - mean)/std
    newseries = np.exp(z)
    return newseries
