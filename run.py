import state2
def mine_rules() :
    result_set = set()
    for doc in state2.corpus :
        for ne in state2.promoted_ne :
            ne_obj = state2.get_ne_object(ne)
            if ne_obj != None and ne_obj.mined_rules != None:
                #Calculation already been done
                precomputed_rules = [r for r in ne_obj.mined_rules \
                        if r not in state2.promoted_rules]
                rules_hashes = [r.get_id() for r in precomputed_rules]
                result_set.union(rules_hashes)
            else :
                found_rules = doc.find_rules(ne)
                if len(found_rules) == 0 :
                    continue
                ne_obj = state2.new_ne_object(ne)
                ne_obj.mined_rules = found_rules
                for r in found_rules :
                    if not state2.all_rules.has_key(r.get_id()) :
                        state2.all_rules[r.get_id()] = r
                    state2.all_rules[r.get_id()].incr_score(ne)
                    result_set.add(r.get_id())
                
    # Only consider new rules for promotion
    result_set = [r for r in result_set if r not in state2.promoted_rules]
    return result_set

def mine_ne() :
    all_ne = set()
    for rule_id in state2.promoted_rules :
        rule_obj = state2.all_rules[rule_id]
        names = rule_obj.extracted_ne
        names = [n for n in names if n not in state2.promoted_ne]
        for n in names :
            all_ne.add(n)
    return list(all_ne)


def score_rules(rule_ids) :
    '''
        Calculate score based on ratio of rule hits in the document.
        Caches extracted name entities as well.
    '''
    for doc in state2.corpus :
        # Match rule to each sentence
        for context in doc.context_list :
            tokens = context.tok_list
            for i in rule_ids :
                rule = state2.all_rules[i]
                hits = rule.match_rule(tokens, context.word_map)
                for hit in hits :
                    rule.total_matches += 1
                    ne_list = state2.recognizer.extract_names(tokens[hit[0]:hit[1]])
                    ne_list = [n for n in ne_list if n not in state2.promoted_ne]
                    if len(ne_list) == 0 :
                        continue
                    rule.extracted_ne = ne_list
                    rule.matches_with_ne += 1

def promote_ne(ne_list, max_to_promote=10) :
    promoted_ids = []
    min_purity = float(state2.cfg.get("Promotion", "PurityMin"))
    
    for i in ne_list :
        print state2.get_ne_object(i).get_score()
    ne_list = [ne for ne in ne_list\
            if state2.get_ne_object(ne).get_score() > min_purity]

    ne_list = sorted(ne_list,\
            key=lambda x:state2.get_ne_object(x).get_score(), reverse=True)
    for i in range(0, min(len(ne_list), max_to_promote)) :
        state2.promoted_ne.append(ne_list[i])
        promoted_ids.append(ne_list[i])
    return promoted_ids


def promote_rules(rule_ids, max_to_promote=10) :
    promoted_ids = []
    promotion_min = float(state2.cfg.get("Promotion", "PromotionThreshold"))
    candidates = [i for i in rule_ids if \
            state2.all_rules[i].promotion_score() > promotion_min]
    candidates = sorted(candidates, \
            key=lambda x: state2.all_rules[i].promotion_score(), reverse=True)
    for i in range(0, min(len(candidates), max_to_promote)):
        state2.all_rules[candidates[i]].score_candidate_ne()
        state2.promoted_rules.append(candidates[i])
        promoted_ids.append(candidates[i])
    return promoted_ids

rule_ids = mine_rules()
score_rules(rule_ids)
promote_ids = promote_rules(rule_ids)
print promote_ids
ne_candidates = mine_ne()
print ne_candidates
promoted_ne = promote_ne(ne_candidates)
print promoted_ne

