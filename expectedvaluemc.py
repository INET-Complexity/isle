
"""
* Created by Torsten Heinrich
*/
Translated to python by Davoud Taghawi-Nejad
"""
def getEV(dist, sampleSize=1000, min=None, max=None, defaultVal=None, var_tail_probability = None):
    rvs = populateArray(dist, sampleSize, min, max, defaultVal);
    mean = sum(rvs) / len(rvs)
    if var_tail_probability is None:
        return mean
    else:
        assert 0 <= var_tail_probability <= 1
        rvs.sort()
        #var = rvs[int(round(var_tail_probability * len(rvs)))]	    # this would be the next highest sample value beyond the VaR probability
        var = rvs[int(round(var_tail_probability * len(rvs))) - 1 ]	# this would be the next lowest sample value below the VaR probability
        return mean, var

def populateArray(dist, sampleSize, min, max, defaultVal):
    """ Create new instance of RandomEngine with new seed, otherwise
    duplicates in the rvs of successive method calls are possible. """
    if defaultVal is None :
        rvs = []
        while len(rvs) < sampleSize:
                # HELP IntStream.range(0, sampleSize - rvs.size()).forEach($ -> rvs.add(dist.random(randomE)));
            rvs = dist.rvs(sampleSize - len(rvs)) # inefficient
                # If the distribution has boundaries without default
                # value to fall back to, delete rvs outside the
                # boundaries, new ones will be drawn in the next iteration.
            if min is not None:
                rvs = filter(lambda rv: rv < min, rvs)
            if max is not None:
                rvs = filter(lambda rv: rv > max, rvs)
    else:
        rvs = dist.rvs(sampleSize)
        if min is not None:
            rvs = [rv if rv >= min else defaultVal for rv in rvs] # SHOULD THAT NOT BE 0?
        if max is not None:
            rvs = [rv if rv <= max else defaultVal for rv in rvs]
    
    return rvs




