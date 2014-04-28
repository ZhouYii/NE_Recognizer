class NamedEntity :
    def __init__(self, name, score) :
        self.name = str(name)
        self.score = float(score)
        self.len = len(self.name)

class Scorekeeper :
    def __init__(self, type_list=['LOC','ORG','PER']) :
        self.dictionary = dict()
        self.max = (-1, None)
        self.total = 0.0

        '''Initialize a score for each type so negative examples are punished
        evenly'''
        for t in type_list :
            self.positive_scoring(t, 0)

    def __getitem__(self, query) :
        if query in self.dictionary.keys() :
            return self.dictionary[query]
        return 0

    def __eq__(self, other) :
        ret = True
        ret &= self.max == other.max
        ret &= self.total == other.total
        ret &= self.dictionary == other.dictionary
        return ret

    def negative_scoring(self, correct_type, punishment) :
        for type in self.dictionary.keys() :
            if type == correct_type :
                continue
            self.dictionary[type] -= punishment

    def positive_scoring(self, key, value=1) :
        if key not in self.dictionary.keys() :
            self.dictionary[key] = value
            val = value
        else :
            self.dictionary[key] += value
            val = self.dictionary[key]

        self.negative_scoring(key, value)

        if val > self.max[0] :
            self.max = (val, key)
        self.total += 1.0*value

    def merge(self, other) :
        for key in other.dictionary.keys() :
            self.positive_scoring(key, other[key])

    def get_max_score(self) :
        return self.max[0]/self.total

    def get_type(self) :
        return self.max[1]

def subword_filter(text, index, word) :
    term1 = index-1 > 0 and str.isalnum(text[index-1])
    term2 = index+len(word) < len(text) and str.isalnum(text[index+len(word)])
    if term1 or term2 :
        return False
    return True

def sort_by_score(score_dict) :
    obj_list = score_dict.keys()
    return sorted(obj_list, \
            key=lambda x:score_dict[x].get_max_score(), reverse=True)

def get_score(rule, score_dict) :
    return score_dict[rule].get_max_score()

def is_token_cap(tok) :
    if len(tok) <= 0 :
        return False
    return str.isupper(tok[0])

def extract_entity(tok_list) :
    def is_cap(tok) :
        return str.isupper(tok[0])
    result = []
    agg = []
    #Are we recording a NE?
    recording = False
    #Allow one interruption between capital words
    interrupted = False
    #First token is always capitalized
    popfront = False
    if len(tok_list) < 1 :
        return []

    for i in range(0, len(tok_list)) :
        ''' Don't consider the first token : that is always capital '''
        tok = tok_list[i]
        if len(tok) == 0 :
            continue
        if is_cap(tok) :
            #if i == 0 :
            #    popfront = True
            agg.append(tok)
            recording = True
            interrupted = False
        else :
            if len(tok) > 2 or interrupted :
                ''' Stop NE '''
                recording = False
                interrupted = False
                if len(agg) > 0 :
                    if not agg[len(agg)-1].isupper() :
                        ''' Chop off the last item if it is lowercase'''
                        agg = agg[:-1]
                    result.append(" ".join(agg))
                    agg = []
            else :
                interrupted = True
                agg.append(tok)
        if popfront :
            result = result[1:]
    return result

def merge_name_dict(dict1, dict2) :
    for k in dict2.keys() :
        if dict1.has_key(k) :
            dict1[k] += dict2[k]
        else :
            dict1[k] = dict2[k]
    return dict1


def build_tok_index(tok_list) :
    tok_index = dict()
    for i in range(0, len(tok_list)) :
        tok = tok_list[i]
        if tok not in tok_index.keys() :
            tok_index[tok] = []
        tok_index[tok].append(i)
    return tok_index

def get_types() :
    return ["PER", "ORG", "LOC"]
