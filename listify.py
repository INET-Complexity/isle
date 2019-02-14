
def listify(d):
    
    print(d)
    """extract keys"""
    keys = list(d.keys())
    
    """create list"""
    l = [d[key] for key in keys]
    l.append(keys)
    print(l)
    
    return l

def delistify(l):
    
    print(l)
    """extract keys"""
    keys = l.pop()
    assert len(keys) == len(l)
    
    """create dict"""
    d = {key: l[i] for i,key in enumerate(keys)}
    print(d)
    
    return d
