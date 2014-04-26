from document import Document
from helper import *
from os import listdir
import re
from NE_Recognizer import NE_Recognizer
from nltk import word_tokenize
from os.path import isfile, join

class State :
    def __init__(self) :
        self.ne_types = set()
        self.corpus = []
        #self.add_corpus("text_extracted")
        self.add_corpus("Raw")
        print "Load Corpus Done"

        #From all iteration
        self.ne = dict()
        self.rules = dict()

        #Find inconsistent rules
        self.candidate_rules = dict()
        self.candidate_ne = dict()

        self.init_dict("PER", "PER.txt")
        self.init_dict("ORG", "ORG.txt")
        self.init_dict("LOC", "LOC.txt")

        #Promote new things
        self.promoted = []

        self.ne_r = NE_Recognizer()
        for doc in self.corpus :
            self.ne_r.train_document(doc)
        self.name_dict = dict()
        for i in range(0, len(self.corpus)) :
            new_dict = self.ne_r.extract_names(self.corpus[i].tokens)
            self.name_dict = merge_name_dict(self.name_dict, new_dict)
        by_score = sorted(self.name_dict.items(), key=lambda x:x[1], reverse=True)
        by_score = [b for b in by_score if b[1] > 0.5 ]
        f = open("Out", "w")
        for entry in by_score :
            f.write(str(entry[0])+'\t'+str(entry[1])+'\n')
        self.ne_r.trie_dict["The"].printme()
        self.ne_r.trie_dict["Internal"].printme()
        self.ne_r.trie_dict["Revenue"].printme()


    def get_type_and_score(self,rule) :
        if rule not in self.rules :
            return ("None", -1)
        maj_map = self.rules[rule]
        return (maj_map.get_type(), maj_map.get_max_score())

    def init_dict(self, label, filepath) :
        f = open(filepath, "r")
        for line in f :
            name = line.strip()
            #Represent NE as a list of tokens
            name = tuple(word_tokenize(name))
            self.ne[name] = Scorekeeper(self.ne_types)
            # Put some large weight for the label since it's seed
            self.ne[name].positive_scoring(label, 99)

    def add_corpus(self, filepath) :
        onlyfiles = [ f for f in listdir(filepath) if isfile(join(filepath,f)) ]
        for f in onlyfiles :
            if f[-4:] != '.txt' :
                ''' All our training data is text files'''
                continue
            self.corpus.append(Document(filepath+"/"+f))

    def get_corpus(self) :
        return self.corpus

    def get_ne_types(self) :
        return list(self.ne_types)

    def add_candidate_rules(self, ne, rules) :
        for rule in rules :
            ne_type = self.ne[ne].get_type()
	    ne_score = self.ne[ne].get_max_score()
            if rule not in self.candidate_rules.keys() :
                self.candidate_rules[rule] = Scorekeeper(self.ne_types)
            self.candidate_rules[rule].positive_scoring(ne_type, ne_score)

    def promotion_filter(self, item, dictionary, threshold) :
        # If any filter is true, ignore rule
        filters = [ # Do not promote suspiciously pure items
                    #lambda r : dictionary[r].get_max_score() == 1.0,
                    # Must meet certain support threshold
                    #lambda r : dictionary[r].total < 100,
                    # Must meet purity threshold
                    lambda r : dictionary[r].get_max_score() < threshold,
                    # Not previously promoted
                    lambda r : r in self.promoted
                    ]
        if filters[0](item) or filters[1](item):
            return False
        return True

    def promote_rules(self, threshold, max_to_promote) :
        def promote(rule_list) :
            for rule in rule_list :
                if rule in self.rules.keys() : 
                    self.rules[rule].merge(self.candidate_rules[rule])
                else :
                    self.rules[rule] = self.candidate_rules[rule]
                self.promoted.append(rule)
            return rule_list

        rule_dict = self.candidate_rules
        print "Rule Promotion Candidates :"+str(self.candidate_rules)
        rules = sort_by_score(rule_dict)
        rules = [r for r in rules if self.promotion_filter(r, rule_dict, threshold)]
        rules = [r for r in rules if r not in self.promoted]
        print "Filtered Rules :"+str(rules)
        ret = promote(rules[:max_to_promote])
        #Clear candidate rules
        self.candidate_rules = dict()
        return ret

    def promote_ne(self, threshold, max_to_promote) :
        def promote(ne_list) :
            for name in ne_list :
                if name in self.ne.keys() :
                    self.ne[name].merge(self.candidate_ne[name])
                else :
                    self.ne[name] = self.candidate_ne[name]
                self.promoted.append(name)
            return ne_list

        ne_dict = self.candidate_ne
        print ne_dict.keys()
        ne_list = sort_by_score(ne_dict)
        ne = [ne for ne in ne_list if self.promotion_filter(ne, ne_dict, threshold)]
        ne = [ne for ne in ne_list if ne not in self.ne.keys()]
        ret = promote(ne_list[:max_to_promote])
        for item in ret :
            if item in self.promoted :
                print "repromote"
        self.candidate_ne = dict()
        return ret

    def find_ne(self) :
        def insert_candidate_ne(ne, rule_type, rule_score) :
            if len(ne) == 0 :
                return
            if ne not in self.candidate_ne.keys() :
                self.candidate_ne[ne] = Scorekeeper(self.ne_types)
            self.candidate_ne[ne].positive_scoring(rule_type, rule_score)

        def distance_close(text, l_bound, r_bound) :
            if -1 == text[l_bound:r_bound].find('.') :
                return True
            return False
        def search_substring(text, query, traverse) :
            if query == "" :
                #Empty rule
                return traverse, traverse
            while traverse < len(text) :
                candidate_index = text.find(query, traverse)
                '''New traverse pointer should not point to same index
                as query to prevent infinite loop'''
                traverse = candidate_index+len(query)
                if candidate_index == -1 :
                    return -1, len(text)
                if subword_filter(text, candidate_index, query) : 
                    return candidate_index, traverse
            return -1, len(text)
        self.candidate_ne = dict()
        #You only find new NE from newly promoted rules
        rule_list = self.rules
        for rule in rule_list :
            info = self.get_type_and_score(rule)
            rule_score, rule_type = info[1], info[0]
            for doc in self.corpus : 
                text = doc.text
                traverse = 0
                while traverse < len(text) :
                    l_bound, traverse= search_substring(text,rule[0],traverse)
                    if l_bound == -1 :
                        break
                    r_bound, traverse = search_substring(text,rule[1],traverse)
                    if r_bound == -1 :
                        traverse = len(text)
                        break
                    ''' If rule parts are too distance or different sentences, do
                    not count '''
                    if not distance_close(text, l_bound, r_bound) :
                        break
                    ''' If the rule only specifies previous token, seek forward
                    word. Otherwise, you find the wrong NE'''
                    if len(rule[1]) == 0:
                        ne = get_next_word(text, r_bound)
                    else :
                        ne = get_prev_word(text, r_bound)
                    insert_candidate_ne(ne, rule_type, rule_score)

