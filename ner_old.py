from os import listdir
#from textblob import TextBlob
import re
from os.path import isfile, join
INPUT = "Raw"
LABELS = ["PER", "LOC", "ORG"]

#PARAMETERS
prom_thresh = 0.5 #To check if a rule is promoted or not

CORPUS = []
#DICTIONARIES
PER_DICT = []
ORG_DICT = []
LOC_DICT = []
#PROMOTED RULES
RULES = []
#CANDIDATE RULES
CR_PER = []
CR_ORG = []
CR_LOC = []
#CANDIDATE NE
CNE = dict()
#CANDIDATE NE (Normalized on documents)
CNE_DOC = dict()
#SCORES
NE_SCORES = dict()
RULE_SCORES = dict()
# Entities associated with a rule
rule_entities = dict()
entity_rules = dict()

NE_TYPE = [(PER_DICT,CR_PER,"PER"), (ORG_DICT,CR_ORG,"ORG"), (LOC_DICT,CR_LOC,"LOC")] 
def get_next_word(text, index) :
    buf = []
    #Stop if no following word
    if index+1 >= len(text) or text[index+1] == '.' :
        return ""
    index += 1
    while index < len(text) and unicode.isalnum(text[index]) :
        buf.append(unicode(text[index]))
        index += 1
    return "".join(buf)

def get_prev_word(text, index) :
    buf = []
    #Stop if no previous words
    if text[index-1] == '.' :
        return ""
    index -= 2
    while index > 0 and unicode.isalnum(text[index]) :
        buf.insert(0, unicode(text[index]))
        index -= 1
    return "".join(buf)

def reset() :
    #refresh candidate lists for new iteration
    CR_PER = []
    CR_ORG = []
    CR_LOC = []
    C_NE = dict()
    CNE_DOC = dict()

def subword_filter(text, index, word) :
    if  unicode.isalnum(text[index-1]) or unicode.isalnum(text[index+len(word)]) :
        return False
    return True

class Document :
    def __init__(self, filepath) :
        f = open(filepath, "r")
        self.text = f.read()
        try :
            self.text = self.text.decode('utf-8')
        except UnicodeDecodeError :
            self.text=""
            print "failed"
        f.close()

    def extract_np(self, rule) :
        result_set = []
        #Use this class for noun phrase
        blob = TextBlob(self.text)

        if rule.prefix == "" :
            print "prefix"
            indicies = [m.start() for m in re.finditer(rule.prefix, self.text)]
            '''Filter out matches which are substring matches (not true rule
            match)'''
            indicies = [index for index in indicies if subword_filter(self.text, index, rule.suffix)]
            '''Advance indicies so index = index of candidate NE'''
            indicies = [index + 1 for index in indicies]
            ''' For each noun phrase occurrence, if index corresponds with rule
            occurrence indicies, use np instead of single word in result set'''
            print list(blob.noun_phrases)
            for np in list(blob.noun_phrases) : 
                traverse = 0
                for i in range(0, self.text.count(np)) :
                    np_index = self.text.find(np, traverse)
                    if np_index in indicies :
                        indicies.remove(np_index)
                        result_set.append(np)
                    traverse = np_index + len(np)
            single_ne = [get_prev_word(self.text, index) for index in indicies]
            return result_set.extend(single_ne)

        if rule.suffix == "" :
            indicies = [m.start() for m in re.finditer(rule.prefix, self.text)]
            indicies = [index for index in indicies if subword_filter(self.text, index, rule.prefix)]
            indicies = [index + len(rule.prefix)+ 1 for index in indicies]
            for np in blob.noun_phrases : 
                print np
                traverse = 0
                for i in range(0, self.text.count(np)) :
                    np_index = self.text.find(np, traverse)
                    if np_index in indicies :
                        indicies.remove(np_index)
                        result_set.append(np)
                    traverse = np_index + len(np)
            print indicies
            single_ne = [get_next_word(self.text, index+len(rule.prefix)) for index in indicies]
            print single_ne
            return result_set.extend(single_ne)



    def extract(self, rule) :
        if rule.prefix == "" and rule.suffix == "" :
            return []
        if rule.prefix == "" :
            indicies = [m.start() for m in re.finditer(rule.suffix, self.text)]
            indicies = [index for index in indicies if subword_filter(self.text, index, rule.suffix)]
            return list(set([get_prev_word(self.text, index) for index in indicies]))
        if rule.suffix == "" :
            indicies = [m.start() for m in re.finditer(rule.prefix, self.text)]
            indicies = [index for index in indicies if subword_filter(self.text, index, rule.prefix)]
            return list(set([get_next_word(self.text, index+len(rule.prefix)) for index in indicies]))


    def find_rules(self,gazetteer, label) :
        count = 0
        rules = []
        for word in gazetteer :
            traverse = 0
            while traverse < len(self.text) :
                index = self.text.find(word, traverse)
                if index < 0 :
                    traverse = len(self.text)
                    break
                traverse = index+len(word)
                if  unicode.isalnum(self.text[index-1]) or \
                        unicode.isalnum(self.text[index+len(word)-1]) :
                            continue
                #count += 1
                #print count
                next_word = get_next_word(self.text, index+len(word))
                prev_word = get_prev_word(self.text, index)
                #print "WORD:"+word
                #print prev_word
                #print next_word
                if len(prev_word) > 3 :
                    rules.append(Rule(label, prev_word, ""))
                    add_rule_entity(rules[-1], word)
                if len(next_word) > 3 :
                    rules.append(Rule(label, "", next_word))
                    add_rule_entity(rules[-1], word)
        return rules

def add_rule_entity(rule, entity):
    if rule not in rule_entities:
        rule_entities[rule] = dict()
    if entity not in rule_entities[rule]:
        rule_entities[rule][entity] = 0
    rule_entities[rule][entity] += 1
    #print 'RULE ENTITIES'
    #print rule_entities

def add_entity_rule(entity, rule):
    if entity not in entity_rules:
        entity_rules[entity] = {}
    if rule not in entity_rules[entity]:
        entity_rules[entity][rule] = 0
    entity_rules[entity][rule] += 1


class Rule :
    def __init__(self, label, prefix, suffix) :
        self.label = label
        self.prefix = prefix if prefix != None else ""
        self.suffix = suffix if suffix != None else ""
        self.application = 0
        self.correct = 0
        self.wrong = 0

    def is_wrong(self) :
        self.wrong += 1
        self.application += 1

    def is_correct(self) :
        self.correct += 1
        self.application += 1

    def print_rule(self) :
        print self.prefix + "<"+self.label+">" + self.suffix

# Candidate rules scored using dictionary entities
def score_rule(rule, rule_label):
    label_total = other_total = 0
    for ne in rule_entities[rule]:
        if get_nelabel(ne) == rule_label:
            label_total += NE_SCORES[ne]
        else:
            other_total += NE_SCORES[ne]

    RULE_SCORES[rule] = (label_total - other_total) / float(len(rule_entities[rule]))
    #print 'Score for ', rule.label + ' ' + rule.prefix + ' ' + rule.suffix + ' ', RULE_SCORES[rule]
    if RULE_SCORES[rule] >= prom_thresh:
        RULES.append(rule)

def get_nelabel(ne):
    for tup in NE_TYPE:
        if ne in tup[0]:
            return tup[2]

# Candidate NEs scored using promoted rules
def score_ne(ne, ne_label):
    label_total = other_total = 0
    for rule in entity_rules[ne]:
        if rule.label == ne_label:
            label_total += 1
        else:
            other_total += 1

    NE_SCORES[ne] = (label_total - other_total) / float(len(entity_rules[ne]))
    if NE_SCORES[ne] > prom_thresh:
        add_to_dict(ne, ne_label)

def add_to_dict(ne, label):
    for pair in NE_TYPE:
        if label == pair[2]:
            pair[0].append(ne)
            #print 'Adding ', ne, 'to ', pair[2], 'with score ', NE_SCORES[ne]

#startalgorithm
# Initialize dictionary
for tup in [(PER_DICT,"PER.txt"),(ORG_DICT,"ORG.txt"),(LOC_DICT,"LOC.txt")] :
    dictionary, f = tup[0], open(tup[1],"r")
    for line in f :
        dictionary.append(line.strip())
        NE_SCORES[line.strip()] = 1.0

#Initialize Corpus
onlyfiles = [ f for f in listdir(INPUT) if isfile(join(INPUT,f)) ]
for f in onlyfiles :
    CORPUS.append(Document(INPUT+"/"+f))
    #print 'Adding size', len(CORPUS[-1].text)


with open('rules.txt', 'w') as fp:
    with open('NEs.txt', 'w') as fp1:
        for i in range(30):
            print 'iteration #', i
            fp.write('iteration '+str(i)+'\n')
            fp1.write('iteration '+str(i)+'\n')
            #generate global set of rules
            for doc in CORPUS :
                for pair in NE_TYPE :
                    dictionary, candidate_rules, label = pair[0], pair[1], pair[2]
                    #Generate candidate rules
            
                    candidate_rules.extend(doc.find_rules(dictionary, label))
                #print len(candidate_rules)
            
            #Rule promotion
            for pair in NE_TYPE:
                candidate_rules = pair[1]
                for rule in candidate_rules:
                    score_rule(rule, rule.label)
        
            print 'Promoted Rules...'
            for rule in RULES:
                s = (rule.label+'\t'+rule.prefix+'\t'+rule.suffix+'\n')#+unicode(RULE_SCORES[rule])
                fp.write(s.encode('utf-8'))
            fp.write('\n\n')
            
            #print 'Promoted rules: ', RULES
            #print '\n\n\n'
            
            
            #generate NE with document-level consistency
            for doc in CORPUS :
                for pair in NE_TYPE :
                    dictionary, candidate_rules, label = pair[0], pair[1], pair[2]
                    #print label
                    # TODO : Change this to use known rules, not candidate
                    #for rule in candidate_rules :
                    for rule in RULES:
                        #list of Names
                        results = doc.extract(rule)
                        results = [r for r in results if len(r) > 0]
                        for r in results :
                            if r not in CNE.keys() :
                                CNE[r] = dict()
                                # Key invariant
                                CNE[r]["PER"] = []
                                CNE[r]["LOC"] = []
                                CNE[r]["ORG"] = []
                            CNE[r][rule.label].append(rule)
                            add_entity_rule(r, rule)
            #Make NE labels consistent across document
            for name in CNE.keys() :
                #Keep track of majority label type and count
                curr = (None, 0)
                for label in LABELS :
                    if len(CNE[name][label]) > curr[1] :
                        curr = (label, len(CNE[name][label]))
                #Reward and punish rules
                for rule in CNE[name][curr[0]] :
                    rule.is_correct()
                for label in LABELS :
                    if label is curr[0] :
                        continue
                    for rule in CNE[name][label] :
                        rule.is_wrong()
                
                CNE_DOC[name] = curr[0]
            print CNE_DOC
            
            #Update NE scores
            print 'Updating NE scores...'
            for ne in CNE:
                for label in CNE[ne]:
                    score_ne(ne, label)
                    s = (ne +'\t'+label+'\n')#+unicode(NE_SCORES[ne])
                    fp1.write(s.encode('utf-8'))
            fp1.write('\n\n')
        
            
            reset()
            print '\n\n\n'
