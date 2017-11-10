import scipy.stats
import numpy as np
import matplotlib.pyplot as plt
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

fig, ax = plt.subplots(1, 1)
ax.plot(x1, non_truncated_dist.pdf(x1), 'k-', lw=2, label='non-truncated pdf')
ax.plot(x1, non_truncated_dist.cdf(x1), 'g-', lw=2, label='non-truncated cdf')
ax.plot(x2, truncated_dist.pdf(x2), 'r-', lw=2, label='truncated pdf')
ax.plot(x2, truncated_dist.cdf(x2), 'm-', lw=2, label='truncated cdf')
ax.plot(x3, reinsurance_dist.pdf(x3), 'b-', lw=2, label='reinsurance pdf')
ax.plot(x3, reinsurance_dist.cdf(x3), 'c-', lw=2, label='reinsurance cdf')
ax.set_xlim(0.45, 1.25)
ax.set_ylim(0, 5)
ax.arrow(x_val_1, reinsurance_dist.cdf(x_val_1), x_val_3 - x_val_1, truncated_dist.cdf(x_val_3) - reinsurance_dist.cdf(x_val_1), head_width=0, head_length=0, fc='m', ec='m', ls=':')
ax.arrow(x_val_2, reinsurance_dist.cdf(x_val_2), x_val_4 - x_val_2, truncated_dist.cdf(x_val_4) - reinsurance_dist.cdf(x_val_2), head_width=0, head_length=0, fc='m', ec='m', ls=':')
ax.arrow(x_val_1, reinsurance_dist.pdf(x_val_1+0.00001), x_val_3 - x_val_1, truncated_dist.pdf(x_val_3) - reinsurance_dist.pdf(x_val_1+0.00001), head_width=0, head_length=0, fc='r', ec='r', ls=':')
ax.arrow(x_val_2, reinsurance_dist.pdf(x_val_2), x_val_4 - x_val_2, truncated_dist.pdf(x_val_4) - reinsurance_dist.pdf(x_val_2), head_width=0, head_length=0, fc='r', ec='r', ls=':')
sample = reinsurance_dist.rvs(size=100000)
#sample = sample[sample < scipy.percentile(sample, 90)]
ax.hist(sample, normed=True, histtype='stepfilled', alpha=0.4)
ax.legend(loc='best', frameon=False)
plt.show()

pdb.set_trace()
