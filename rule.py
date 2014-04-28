from helper import *
import state2
from scorable import *

class Rule(Scorable) :
    def __init__(self, fwd=None, rev=None) :
        ''' Sets all parameters to None, to distinguish between never-set and
        set-to-empty '''

        Scorable.__init__(self)
        self.found_by = set()
        self.fwd_window = fwd
        self.rev_window = rev

        self.matches_with_ne = 0
        self.total_matches = 0

        self.extracted_ne = None

    def __str__(self) :
        return "Rule :"+str(self.fwd_window)+"/"+str(self.rev_window)

    def __eq__(self, other) :
        if other == None :
            return False
        ret = True
        ret &= self.fwd_window == other.fwd_window
        ret &= self.rev_window == other.rev_window
        return ret

    def __hash__(self) :
        ''' Hash by constant and unique identifiers : meaning not any form of
        purity score '''
        h = (tuple(self.fwd_window), tuple(self.rev_window))
        return h.__hash__()

    def get_id(self) :
        ''' More memory efficient than just tuple '''
        return self.__hash__()

    def __ne__(self, other) :
        return not self == other

    def blank_rule(self) :
        r = Rule()
        return self == r

    def incr_score(self, name) :
        ''' Prevent double counting from the same named entity '''
        ne_obj = state2.all_ne[name]
        if name in self.found_by :
            return 
        self.add_score(ne_obj.get_type(), ne_obj.get_score())

    def match_rev(self, seq, index) :
        if self.rev_window == None or len(self.rev_window) == 0 :
            return range(len(seq))

        if not index.has_key(self.rev_window[0]) :
            return []

        return self.match_seq(self.rev_window, seq, index)

    def match_fwd(self, seq, index) :
        if self.fwd_window == None or len(self.fwd_window) == 0 :
            return range(len(seq))

        if not index.has_key(self.fwd_window[0]) :
            return []

        candidates = self.match_seq(self.fwd_window, seq, index)
        # advance index point past the matched sequence
        candidates = [c+len(self.fwd_window) for c in candidates]
        return candidates

    def match_rule(self, seq, index) :
        fwd_matches = self.match_fwd(seq, index)
        rev_matches = self.match_rev(seq, index)
        boundary_pairs = []
        for f in fwd_matches :
            cont = False
            for r in rev_matches :
                if f < r :
                    boundary_pairs.append((f,r))
                    cont = True
                    break
            if not cont :
                break
        return boundary_pairs
    
    def match_seq(self, target, seq, index) :
        candidates = index[target[0]]
        for i in range(1, len(target)) :
            tmp = index[target[i]]
            candidates = [c for c in candidates if c+i in target]
        return candidates

    def promotion_score(self) :
        purity_min = float(state2.cfg.get("Promotion","PurityMin"))
        extract_min = float(state2.cfg.get("Promotion","ExtractPercentage"))

        if purity_min > self.get_score() or \
                self.extracted_ne == None or \
                extract_min > self.matches_with_ne/float(self.total_matches) :
            return 0

        return self.get_score()

    def score_candidate_ne(self) :
        ne_list = self.extracted_ne
        if ne_list == None or len(ne_list) == 0 :
            return
        for ne in ne_list :
            ne_obj = state2.new_ne_object(ne)
            ne_obj.add_score(self.get_type(),self.get_score())
