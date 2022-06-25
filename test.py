


import random
import string


old = []
def getrandom(x):
    res = ''.join(random.choice(string.ascii_uppercase) for _ in range(x))
    if res in old:
        return getrandom(x)
    old.append(res)
    return res
def get_random_ids(count):
    return [
        getrandom(7) for _ in range(count)
    ]