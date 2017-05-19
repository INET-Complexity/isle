from numpy.random import exponential

class GeneralizedExponential:
    def __init__(self, v, seed=None):
        self.v = v
        assert seed is None

    def random(self, size=None):
        return exponential(self.v, size=size)
