from helper import *
from scorable import Scorable

class NameEntity(Scorable) :
    def __init__(self, tok_tuple, is_seed=False) :
        Scorable.__init__(self)
        self.name = tok_tuple
        self.mined_rules = None
    
    def init_seed(self, type) :
        self.is_seed = True
        self.total = 1
        for k in self.dictionary.keys() :
            if k == type :
                self.dictionary[k] = 1
            else :
                self.dictionary[k] = 0


