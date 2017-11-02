
class GenericAgent():
    def __init__(self, *args, **kwargs):
        self.init(*args, **kwargs)
    
    def init(*args, **kwargs):
        assert False, "Error: GenericAgent init method should have been overridden but was not."
