from helper import *

class Scorable :
    def __init__(self) :
        self.is_seed = False
        self.dictionary = dict()
        # Max : (max score, type responsible)
        self.max_type = None
        self.max_stale = True
        self.total = 0.0

        for t in get_types() :
            self.dictionary[t] = 0

    def add_score(self, key, val=1) :
        ''' Potentially skip all call where value (confidence) is within epsilon
        of 1/#types, to get rid of noise '''
        if self.is_seed : #Seed confidence is immutable
            return
        val = float(val)
        if not self.dictionary.has_key(key) :
            print("Adding score to unknown key: "+str(key) )
            return
        self.max_stale = True
        self.dictionary[key] += val
        val = self.dictionary[key]
        self.total += val

        #Lower score for negative examples
        for t in get_types() :
            if t == key :
                continue
            self.dictionary[t] -= val

    def recalc_max_type(self) :
        ordered = sorted(self.dictionary.items(), key=lambda x:x[1], reverse=True)
        self.max_type = ordered[0][0]
        self.max_stale = False

    def merge_scores(self, other) :
        self.max_stale=True
        self.total += other.total
        for k in other.dictionary.keys() :
            self.dictionary[k] += other.dictionary[k]

    def get_score(self) :
        if self.max_stale :
            self.recalc_max_type()
        return self.dictionary[self.max_type]/self.total

    def get_type(self) :
        if self.max_stale :
            self.recalc_max_type()
        return self.max_type
