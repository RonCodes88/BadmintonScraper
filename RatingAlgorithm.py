import math

# calculate & return the probability of player1 to win
def winProbability(rating1: float, rating2: float) -> float:
    winChance = 1.0 / (1.0 + math.pow(10, ((rating2 - rating1) / 400)))
    return winChance

# calculate & return the points added/deducted to player1, based on his match result
def findEloRating(rating1: float, rating2: float, k: float, matchResult: bool) -> float:
    P1 = winProbability(rating1, rating2)
    # Case1: player1 wins
    if (matchResult):
        eloPoint = k * (1.0 - P1)
    # Case2: player1 loses
    else:
        eloPoint = k * (0.0 - P1)
    return eloPoint

'''test code:
print(winProbability(2679.990027, 2705.394285))
print(findEloRating(2679.990027, 2705.394285, 32, True)/2)'''