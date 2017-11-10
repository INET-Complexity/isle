import scipy.stats
import numpy as np
import matplotlib.pyplot as plt
from math import ceil
import scipy.integrate

class TruncatedDistWrapper():
    def __init__(self, dist, lower_bound=0, upper_bound=1):
        self.dist = dist
        self.normalizing_factor = dist.cdf(upper_bound) - dist.cdf(lower_bound)
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        assert self.upper_bound > self.lower_bound
 
    def pdf(self, x):
        x = np.array(x, ndmin=1)
        r = map(lambda Y: self.dist.pdf(Y) / self.normalizing_factor \
                            if (Y >= self.lower_bound and Y <= self.upper_bound) else 0, x)
        r = np.array(list(r))
        if len(r.flatten()) == 1:
            r = float(r)
        return r
        
    def cdf(self, x):
        x = np.array(x, ndmin=1)
        r = map(lambda Y: 0 if Y < self.lower_bound else 1 if Y > self.upper_bound \
                            else (self.dist.cdf(Y) - self.dist.cdf(self.lower_bound))/ self.normalizing_factor, x)
        r = np.array(list(r))
        if len(r.flatten()) == 1:
            r = float(r)
        return r
        
    def ppf(self, x):
        x = np.array(x, ndmin=1)
        assert (x >= 0).all() and (x <= 1).all()
        return self.dist.ppf(x * self.normalizing_factor + self.dist.cdf(self.lower_bound))

    def rvs(self, size=1):
        init_sample_size = int(ceil(size / self.normalizing_factor * 1.1))
        sample = self.dist.rvs(size=init_sample_size)
        sample = sample[sample>=self.lower_bound]
        sample = sample[sample<=self.upper_bound]
        while len(sample) < size:
            sample = np.append(sample, self.rvs(size - len(sample)))
        return sample[:size]    
    
    def mean(self):
        mean_estimate, mean_error = scipy.integrate.quad(lambda Y: Y*self.pdf(Y), self.lower_bound, self.upper_bound)
        return mean_estimate

if __name__ == "__main__":
    non_truncated = scipy.stats.pareto(b=2, loc=0, scale=0.5)
    truncated = TruncatedDistWrapper(lower_bound=0.55, upper_bound=1., dist=non_truncated)

    x = np.linspace(non_truncated.ppf(0.01), non_truncated.ppf(0.99), 100)
    x2 = np.linspace(truncated.ppf(0.01), truncated.ppf(0.99), 100)

    fig, ax = plt.subplots(1, 1)
    ax.plot(x, non_truncated.pdf(x), 'k-', lw=2, label='non-truncated pdf')
    ax.plot(x2, truncated.pdf(x2), 'r-', lw=2, label='truncated pdf')
    ax.plot(x, non_truncated.cdf(x), 'b-', lw=2, label='non-truncated cdf')
    ax.plot(x2, truncated.cdf(x2), 'g-', lw=2, label='truncated cdf')
    sample = truncated.rvs(size=1000)
    ax.hist(sample, normed=True, histtype='stepfilled', alpha=0.4)
    ax.legend(loc='best', frameon=False)
    plt.show()
    
    print(truncated.mean())
