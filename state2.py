'''
Implementation of State singleton
'''

import ConfigParser
from os import listdir
from helper import *
import re
import RuleFactory
from document import Document
from nameentity import NameEntity
from os.path import isfile, join
import pickle
from nltk import word_tokenize

cfg = ConfigParser.ConfigParser()
cfg.read("config.ini")

corpus = []

# all_* data structures primarity for caching results
all_rules = dict()
# promoted_* data structure for recording promoted entities
promoted_rules = []
all_ne = dict()
promoted_ne = []
# name recognizer
recognizer = None

def init() :
    init_corpus()
    init_recognizer()

    for t in get_types():
        init_dict(t, cfg.get("SeedFiles", t))

def init_corpus() :
    filepath = cfg.get('StateInit','CorpusDir')
    onlyfiles = [ f for f in listdir(filepath) if isfile(join(filepath,f)) ]
    for f in onlyfiles :
        if f[-4:] != '.txt' :
            ''' All our training data is text files'''
            continue
        corpus.append(Document(filepath+"/"+f))

def init_dict(label, filepath) :
    f = open(filepath, "r")
    for line in f :
        name = line.strip()
        #Represent NE as a list of tokens
        name = tuple(word_tokenize(name))
        ne = NameEntity(name, is_seed=True)
        ne.init_seed(label)
        all_ne[ne.name] = ne
        promoted_ne.append(ne.name)

def init_recognizer() :
    global recognizer
    filepath = cfg.get('StateInit', 'ExtractorSeed')
    recognizer = pickle.load(open(filepath, "rb"))
    print "Recognizer:"+str(recognizer)

def get_ne_object(name) :
    if not all_ne.has_key(name) :
        return None
    return all_ne[name]

def new_ne_object(name) :
    if not all_ne.has_key(name) :
        all_ne[name] = NameEntity(name)
    return all_ne[name]

init()
