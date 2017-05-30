
"""
* Created by Torsten Heinrich
*/
Translated to python by Davoud Taghawi-Nejad

>>> from from generalizedExponential import GeneralizedExponential
>>> getEV(GeneralizedExponential(33.33), None, None, None, None)
>>> getEV(GeneralizedExponential(33.33), 10, None, None, None)
>>> getEV(GeneralizedExponential(33.33), 10, None, 40., 40.)
>>> getEV(GeneralizedExponential(33.33), 10, None, 40., None)
>>> getEV(GeneralizedExponential(33.33), 10, 4., None, 4.)
"""
def getEV(dist, sampleSize=1000, min=None, max=None, defaultVal=None):
    rvs = populateArray(dist, sampleSize, min, max, defaultVal);
    return sum(rvs) / len(rvs)

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




