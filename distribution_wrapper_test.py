import scipy.stats
import numpy as np
from distributiontruncated import TruncatedDistWrapper
from distributionreinsurance import ReinsuranceDistWrapper
import pdb

non_truncated_dist = scipy.stats.pareto(b=2, loc=0, scale=0.5)
truncated_dist = TruncatedDistWrapper(lower_bound=0.6, upper_bound=1., dist=non_truncated_dist)
reinsurance_dist = ReinsuranceDistWrapper(lower_bound=0.85, upper_bound=0.95, dist=truncated_dist)

x1 = np.linspace(non_truncated_dist.ppf(0.01), non_truncated_dist.ppf(0.99), 100)
x2 = np.linspace(truncated_dist.ppf(0.01), truncated_dist.ppf(1.), 100)
x3 = np.linspace(reinsurance_dist.ppf(0.01), reinsurance_dist.ppf(1.), 100)
x_val_1 = reinsurance_dist.lower_bound
x_val_2 = truncated_dist.upper_bound - (reinsurance_dist.upper_bound - reinsurance_dist.lower_bound)
x_val_3 = reinsurance_dist.upper_bound
x_val_4 = truncated_dist.upper_bound

pdb.set_trace()
