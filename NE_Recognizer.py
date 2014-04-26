from helper import *
NAME_WINDOW=5
NODE_MIN_OBSERVATIONS=4
class Node :
    def __init__(self, tok) :
        self.tok = tok
        self.count = 0
        self.children = dict()
        self.pending = []

    def incr(self) :
        self.count += 1

    def get_tok(self) :
        return self.tok

    def get_count(self) :
        return self.count

    def has_child(self, tok) :
        return self.children.has_key(tok)

    def get_child(self, tok) :
        if not self.children.has_key(tok) :
            self.children[tok] = Node(tok)
        return self.children[tok]

    def get_score(self, tok_seq, conditioned_denom) :
        if len(tok_seq) == 0 :
            ''' This is the destination node. Return Score '''
            return float(self.count)/float(conditioned_denom)
        child = tok_seq.pop(0)
        if not self.children.has_key(child) :
            return 0
        else :
            node = self.children[child]
            return node.get_score(tok_seq, float(self.count))

    def printme(self, num_tab=0) :
        print '\t\t'*num_tab+self.tok+" - "+str(self.count)
        for c in self.children.values() :
            c.printme(num_tab+1)

    def count_seq(self, tok_seq) :
        if len(tok_seq) == 0 or self.tok != tok_seq[0] :
            return
        tok_seq.pop(0)
        self.incr()
        if len(tok_seq) == 0 :
            return
        if self.count < NODE_MIN_OBSERVATIONS :
            self.pending.append(tok_seq)
        else :
            self.pending.append(tok_seq)
            for seq in self.pending :
                if len(seq) == 0 :
                    continue
                c = self.get_child(seq[0])
                c.count_seq(seq)

class CounterTrie :
    ''' Corresponds to a candidate word for he start of a name '''
    def __init__(self, root_token) :
        self.root = Node(root_token) 
        self.root.incr()

    def invalid_seq(self, seq) :
        ''' Check if the sequence is 0-length or is not rooted at the same root
        as this structure '''
        return len(seq) == 0 or seq[0] != self.root.get_tok()

    def count_seq(self, tok_seq) :
        if self.invalid_seq(tok_seq) :
            return
        else :
            self.root.count_seq(tok_seq)
            '''
            curr_node = self.root
            curr_node.incr()
            tok_seq.pop(0)

        for tok in tok_seq :
                Do not allow un-cap words with long length. Definitely not in
                proper name
            if len(tok) == 0 : 
                continue
            if not is_token_cap(tok) and len(tok) > 2 :
                return
            curr_node = curr_node.get_child(tok)
            curr_node.incr()
            '''

    def get_seq_score(self, seq) :
        if self.invalid_seq(seq) or len(seq) == 1:
            ''' 1-length sequence should not contribute score'''
            return 0
        else :
            seq.pop(0)
            score = self.root.get_score(seq, self.root.get_count())
            return score

    def printme(self) :
        self.root.printme()

class NE_Recognizer :

    def __init__(self) :
        self.cap_token_stats = dict()
        self.trie_dict = dict()

    def train_document(self, doc) :
        ''' Train the Trie data structures using windows of works from the
        document, where each window starts with some capitalized word '''
        tok_punct = doc.tokens
        sent_list = partition_by_punct(tok_punct)
        for tok_seq in sent_list :
            #Collect statistics for only the capitalized tokens
            for i in range(0, len(tok_seq)) :
                tok = tok_seq[i]
                if not is_token_cap(tok) :
                    continue
                if not self.trie_dict.has_key(tok) :
                    self.trie_dict[tok] = CounterTrie(tok)
                seq = tok_seq[i:min(i+NAME_WINDOW,len(tok_seq))]
                self.trie_dict[tok].count_seq(seq)

    def extract_names(self, tok_list) :
        def merge_into_dict(src, dest) :
            for i in src :
                name = i[1][1]
                score = i[1][0]
                if not dest.has_key(name) :
                    dest[name] = score
                else :
                    dest[name] += score
            return dest

        name_dict = dict()
        tok_chunks = partition_by_punct(tok_list)
        for seq in tok_chunks :
            if len(seq) == 0 :
                continue
            tok_scores = self.extract_names_(seq)
            name_dict = merge_into_dict(tok_scores, name_dict)
        return name_dict

    def extract_names_(self, tok_list) :
        ''' Assumes the token list has punctuation.
        General extraction rules : Name starts with a capitalized word.
        Names do not cross punctuation boundaries : [',' , '.', '()'].
        Last word of a name is capitalized.
        '''
        result_set = dict()
        for i in range(0, len(tok_list)) :
            print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@New Iteration"
            if is_token_cap(tok_list[i]) :
                tok_seq = tok_list[i:min(i+NAME_WINDOW, len(tok_list))]
                found, score = self.extract_names_from_seq(tok_seq)
                print "Found:"+str(found) + "score:"+str(score)
                #Do not give score to any 1-length tokens
                found = [f for f in found if len(f) > 1]
                for name in found :
                    print "NAME:"+str(name)
                    if not result_set.has_key(name) :
                        result_set[name] = [score, " ".join(list(name))]
                    else :
                        prev_score = result_set[name][0]
                        result_set[name] = [prev_score+score, " ".join(list(name))]
        tok_scoring =  sorted(result_set.items(), key=lambda x:x[1][0], reverse=True)
        return tok_scoring

    def extract_names_from_seq(self, tok_seq) :
        ''' Extract NE from a sequence of tokens '''

        def add_score(score_dict, candidate_name, other_names, total_score) :
            print "Score Dict:"+str(score_dict.items())
            print "Other Names:"+str(other_names)
            print "Candidate_name"+str(candidate_name)
            if other_names == None or len(other_names) == 0 :
                name_list = [candidate_name]
            else :
                name_list = [candidate_name]
                name_list.extend(other_names)
                name_list = sorted(name_list)
            print "Name Tuple"+str(tuple(name_list))
            #Needs to be hashable.
            name_tuple = tuple(name_list)
            if score_dict.has_key(name_tuple) :
                score_dict[name_tuple] = max(total_score, score_dict[name_tuple])
            else :
                score_dict[name_tuple] = total_score
            return score_dict

        def cut_trailing_lowercase(seq) :
            i = len(seq)-1
            while i > 0 and not is_token_cap(seq[i]) :
                i -= 1
            return seq[:i+1]

        if len(tok_seq) == 0 or not self.trie_dict.has_key(tok_seq[0]) :
            ''' Score is 0 is the token does not have a trie structure or token
            sequence is empty'''
            return [], 0

        root = tok_seq[0]
        if len(tok_seq) == 1 and self.trie_dict.has_key(root) :
            ''' Base case for 1-len word '''
            return [root], 0

        scores = dict()
        for i in range(1, len(tok_seq)+1) :
            tokens = cut_trailing_lowercase(tok_seq[:i])
            candidate_name = tuple(tokens)
            #print "---- Entire Tok Seq:"+str(tok_seq)
            #print "i="+str(i)
            #print "TokSeq:"+str(tokens)
            #print "CandidateName:"+candidate_name
            candidate_score = self.trie_dict[root].get_seq_score(tokens)
            #print "CandidateScore:"+str(candidate_score)
            remaining = tok_seq[i:]
            #print "Remaining:"+str(remaining)
            rem_names, rem_score = self.extract_names_from_seq(remaining)
            #print "rem names:"+str(rem_names) + " rem score:"+str(rem_score)
            total_score = candidate_score+float(rem_score)
            #print "What's the candidate name now?:"+candidate_name
            scores = add_score(scores, candidate_name, rem_names, total_score)
        #print "-------SEQ Ret:"+str( max(scores.items(), key=lambda x: x[1]))
        return max(scores.items(), key=lambda x: x[1])


def partition_by_punct(tok_list) :
    ''' Wrapper to extract_names '''
    punct_blacklist = [',','(',')','.','!','?']
    #Split the original token list by punctuation
    tok_chunks = []
    agg = []
    for tok in tok_list :
        if tok[len(tok)-1] in punct_blacklist :
            agg.append(tok[:-1])
            agg = [t for t in agg if len(t) > 0]
            tok_chunks.append(agg)
            agg = []
        else :
            agg.append(tok)
    return tok_chunks


