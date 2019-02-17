"""Auxiliary function to transform dicts into lists and back for transfer
   from cloud (sandman2) to local."""

def listify(d):
    """Function to convert dict to list with keys in last list element.
        Arguments:
            d: dict - input dict
        Returns:
            list with dict values as elements [:-1] and dict keys as 
                last element."""
                    
    """extract keys"""
    keys = list(d.keys())
    
    """create list"""
    l = [d[key] for key in keys]
    l.append(keys)
    
    return l

def delistify(l):
    """Function to convert listified dict back to dict.
        Arguments:
            l: list - input listified dict. This must be a list of dict 
                        elements as elements [:-1] and the corresponding
                        dict keys as list in the last element.
        Returns:
            dict - The restored dict."""
            
    """extract keys"""
    keys = l.pop()
    assert len(keys) == len(l)
    
    """create dict"""
    d = {key: l[i] for i,key in enumerate(keys)}
    
    return d
