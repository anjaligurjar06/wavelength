def jaccard_similarity(user_a, user_b):
    set_a = set(user_a)
    set_b = set(user_b)

    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)

    if not union:
        return 0.0

    return len(intersection) / len(union)