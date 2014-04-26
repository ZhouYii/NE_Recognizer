def print_log(promote_set,dic) :
    for item in promote_set :
        print str(item) +" purity:" + str(dic[item].get_max_score())+ " type :" + \
                str(dic[item].get_type())
        for type in dic[item].dictionary.keys() :
            print "type:"+str(type) +" : " +str(dic[item].dictionary[type])
            
from controller import Controller
NER = Controller()
'''
#Specify number of iterations
for i in range(9): 
    print "-------------------Iteration:"+str(i)+"-------------------"

    NER.find_rules_tok()
    promote_set = NER.promote_rules(0.6, 9) #Args : threshold [0,1], max promotions
    print "Rules:"
    print_log(promote_set, NER.state.rules)

    NER.find_ne()
    promote_set = NER.promote_ne(0.6, 9)
    print "NE:"
    print_log(promote_set, NER.state.ne)

    NER.end_iteration()
    '''
