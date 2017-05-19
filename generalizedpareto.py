from scipy.stats import genpareto


class GeneralizedPareto:
    def __init__(self, loc, scale, shape, seed=None):
        self.loc = loc
        self.scale = scale
        self.shape = shape
        assert seed is None

    def random(self, size=None):
        return genpareto.rvs(loc=self.loc, scale=self.scale, c=self.shape, size=size)
