
import scipy.stats

def compare_rv_objects(dist1, dist2):
    param1 = (dist1.dist.name, dist1.dist._parse_args(*dist1.args, **dist1.kwds))
    param2 = (dist2.dist.name, dist2.dist._parse_args(*dist2.args, **dist2.kwds))
    return param1 == param2
