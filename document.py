from os import listdir
import re, nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from os.path import isfile, join
from context import Context
from helper import *

def pass_filters(tok) :
    filters = [lambda w : w in stopwords.words('english'),  #Ignore stopwords
                lambda w : len(w) == 0,                     #Empty Token
                lambda w : w == '``' or w == "''",          #Another form of empty token
                lambda w : len(w) == 1 and not str.isalnum(w[0])] #Single punctuation tokens
    for test in filters :
        if test(tok) :
            return False
    return True

def lemmatize(tok_list) :
    lemma = nltk.WordNetLemmatizer()
    return [lemma.lemmatize(t) for t in tok_list]

def init_structs(doc) :
    ''' The indexing structure maps tokens to their contexts = tokenized
    sentences '''
    sentence_list = doc.sentences
    text = doc.text
    #Mapping from the token to the sentence contexts
    context_map = dict()
    context_list = []
    no_punct_tok = []

    for sentence in sentence_list :
        tok_list = word_tokenize(sentence)
        tok_list = lemmatize(tok_list)
        tok_list = [w for w in tok_list if pass_filters(w)]
        no_punct_tok.extend(tok_list)
        context = Context(tok_list)
        context_list.append(context)
        for tok in tok_list :
            if tok not in context_map.keys() :
                context_map[tok] = []
            context_map[tok].append(context)
    return context_map, no_punct_tok, context_list

class Document :
    #Static alloc
    sent_chunker = nltk.data.load('tokenizers/punkt/english.pickle')
    def __init__(self, filepath) :
        f = open(filepath, "r")
        self.text = f.read().strip()
        self.tokens = word_tokenize(self.text)
        #Split sentences and remove terminating period
        self.sentences = [s[:len(s)-1] for s in Document.sent_chunker.tokenize(self.text)]
        self.tok_index, self.tokens_nopunct, self.context_list = init_structs(self)
        self.tokens_nopunct = [t for t in self.tokens_nopunct if t.lower() not in stopwords.words('english')]
        #self.num_tok = len(self.tokens)
        f.close()

    def rule_quickfail(self, rule) :
        ''' Sample the first tokens from the rule and quickly decide if the rule
        will not appear in this document'''
        if len(rule[0]) > 0 :
            tok = rule[0][0]
            if not self.tok_index.has_key(tok) :
                return True
        if len(rule[1]) > 0 :
            tok = rule[1][0]
            if not self.tok_index.has_key(tok) :
                return True
        return False

    def match_one_side(self, rule) :
        #Stub
        return []

    def find_rules(self, ne) :
        if len(ne) == 0 or not self.has_token(ne[0]) :
            return []
        candidates = []
        for context in self.tok_index[ne[0]] :
            rules = context.generate_rules(ne)
            if rules != None or len(rules) > 0 :
                candidates.extend(rules)
        return candidates

    def find_ne_tok(self, rule) :
        ''' Rule is a 2-ple, each element is a list of tokens for the
        matching'''
        #Quickly fail
        if self.rule_quickfail(rule) :
            return []
        #Handle rules with words on one side.
        if len(rule[0]) == 0 or len(rule[1]) == 0 :
            return match_one_side(self, rule)

        #Handle rules with words on both sides.
        candidate_context = match_prefix(rule)
        if candidate_context == False :
            #Failed to match rule
            return []
        ne_list = match_suffix(rule, candidate_context)
        if ne_list != None and len(ne_list) > 0 :
            return ne_list
        return []

    def match_rule(self, rule, rule_index) :
        ''' Matches on half of the rule's, specified by rule_index.
        Returns None if there is nothing defined for the first half.
        Returns False if there are no matches.
        Otherwise returns a list of 2-ples : context and list of hit indicies'''
        if len(rule[rule_index]) == 0 :
            return None
        #Find all contexts which partially matches the rule
        context_list = self.tok_index[rule[rule_index][0]]
        result_set = []
        for context in context_list :
            match_indicies = context.match(rule[rule_index])
            if len(match_indicies) == 0 :
                continue
            result_set.append((context, match_indicies))
        if len(result_set) == 0 :
            return False
        return result_set

    def match_prefix(self, rule) :
        return self.match_rule(rule, 0)

    def match_suffix(self, rule, candidate_context) :
        if len(rule[1]) == 0 :
            #Nothing to match
            return candidate_context 

        #Should not happen since one-side rules are handled in another function
        if candidate_context == None :
            #Only match second half
            return self.match_rule(rule, 1)

        ''' There are results from matching first half of the rule.
            Means the returned results must be subset of candidate_context'''
        discovered_ne = []
        for tup in candidate_context :
            context, prefix_matches = tup[0], tup[1]
            ''' Prefix indicies are used as boundaries to mine NE. Advance the
            index here so the NE we mine do not include the rule's prefix'''
            prefix_matches = [i+len(rule[0]) in prefix_matches]
            suffix_matches = sorted(context.match(rule[1]))
            #Pair the match indicies
            for index in prefix_matches :
                if len(suffix_matches) == 0 :
                    break
                suffix = suffix_matches.pop(0)
                while suffix < index and len(suffix_matches) > 0 :
                    suffix = suffix_matches.pop(0)
                discovered_ne.extend(context.extract_ne(index, suffix))
        return discovered_ne
    
    def has_token(self, tok) :
        return tok in self.tok_index.keys()
