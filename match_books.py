class Matcher():
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def jaccard_distance(set1:set, set2:set):
        symm_diff = set1.symmetric_difference(set2)
        union = set1.union(set2)
        return len(symm_diff)/len(union)
 

    def contains_query(self, query, candidate: list) -> bool:
        return query in candidate \
            # or self.jaccard_distance(set(query.split(" ")), {candidate}) > 0.99
            
