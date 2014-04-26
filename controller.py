from state import State

class Controller :
    def __init__(self) :
        self.state = State()

    #Can define halting condition based on extraction count
    def get_ne_types(self) :
        return self.state.get_ne_types()

    def find_rules(self) :
        '''
            Iterate over known NE and generate rules
        '''
        for ne in self.state.ne.keys() :
            rules = []
            for doc in self.state.corpus :
                rules_i = doc.find_rules([ne])
                if len(rules_i) > 0 :
                    rules.extend(rules_i)
            self.state.log_rules(ne, rules)

    def find_rules_tok(self) :
        for doc in self.state.corpus :
            for ne in self.state.ne.keys() :
                candidates = []
                if not doc.has_token(ne[0]) :
                    continue
                for context in doc.tok_index[ne[0]] :
                    rules = context.generate_rules(ne)
                    '''
                        prune rules
                    '''
                    candidates.extend(rules)
            self.state.add_candidate_rules(ne, candidates)

    def find_ne_tok(self) :
        for doc in self.state.corpus :
            for rule in self.state.rules :
                candidates = doc.find_ne(rule)
                if len(candidates) == 0 :
                    continue
                for ne in candidates : 
                    self.insert_candidate_ne(ne, rule)

    def promote_rules(self, threshold, max) :
        return self.state.promote_rules(threshold, max)

    def promote_ne(self, threshold, max) :
        return self.state.promote_ne(threshold, max)

    def find_ne(self):
        self.state.find_ne()

    def end_iteration(self) :
        self.state.candidate_rules = dict()
        self.state.candidate_ne = dict()

    def insert_candidate_ne(self, ne, rule) :
        candidate_dict = self.state.candidate_ne
        rule_dict = self.state.rules
        rule_type = rule_dict[rule].get_type()
        rule_score = rule_dict[rule].get_max_score()
        if ne not in candidate_dict.keys() :
            candidate_dict[ne] = Scorekeeper(self.state.ne_types)
        candidate_dict[ne].positive_scoring(rule_type, rule_score)
