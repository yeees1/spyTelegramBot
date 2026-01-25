import random

def generateSpyCount(usersCount):
    first_end = int(usersCount * 0.34)
    second_end = int(usersCount * 0.67)
    r = random.random()
    if r < 0.50:
        return random.randint(0, first_end)
    elif r < 0.50 + 0.35:
        return random.randint(first_end + 1, second_end)
    else:
        return random.randint(second_end + 1, usersCount)
