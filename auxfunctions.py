"""
 Auxiliary functions for ISLE.
 
 Created by Torsten Heinrich.
"""

# import general python modules
import scipy.stats

def compare_rv_objects(dist1, dist2):
    """Function to compare two rv frozen distribution objects
       Positional arguments:
         dist1 (rv frozen distribution): first distribution
         dist2 (rv frozen distribution): second distribution
       Returns (boolean): whether the two distributions are the same"""
    param1 = (dist1.dist.name, dist1.dist._parse_args(*dist1.args, **dist1.kwds))
    param2 = (dist2.dist.name, dist2.dist._parse_args(*dist2.args, **dist2.kwds))
    return param1 == param2
