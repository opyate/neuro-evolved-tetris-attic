import random


def weighted_selection(all_fitness: list[float], total_fitness: float) -> int:
    """Select a fit bot.

    This function uses a relay-race technique for giving a fair shot to
    all members of a population, while still increasing the chances of
    selection for those with higher fitness scores.

    The index in all_fitness will be the bot's id.

    Args:
        bots (list[TetrisBot]): the bot population
        total_fitness (float): the total fitness of the population

    Returns:
        int: the index of the selected bot
    """
    index = 0
    start = random.uniform(0, 1)

    while start > 0:
        normalised_fitness = all_fitness[index] / total_fitness
        start -= normalised_fitness
        index += 1

    index -= 1  # Adjust index because we incremented it at the end of the loop

    return index
