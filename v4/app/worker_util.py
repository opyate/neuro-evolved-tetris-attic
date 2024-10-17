import random

from app.tetris_bot import TetrisBot


def crossover_with_fittest(
    bot: TetrisBot, bots: list[TetrisBot], total_fitness: float
) -> tuple[int, int]:
    parent_a_index = weighted_selection(bots, total_fitness)
    parent_b_index = weighted_selection(bots, total_fitness)

    parent_a = bots[parent_a_index]
    parent_b = bots[parent_b_index]

    # Crossover the two parents to produce a new child brain
    bot.crossover(parent_a, parent_b)
    return parent_a_index, parent_b_index


def weighted_selection(bots: list[TetrisBot], total_fitness: float) -> int:
    """Select a fit bot.

    This function uses a relay-race technique for giving a fair shot to
    all members of a population, while still increasing the chances of
    selection for those with higher fitness scores.

    Args:
        bots (list[TetrisBot]): the bot population
        total_fitness (float): the total fitness of the population

    Returns:
        int: the index of the selected bot
    """
    index = 0
    start = random.uniform(0, 1)

    while start > 0:
        normalised_fitness = bots[index].fitness / total_fitness
        start -= normalised_fitness
        index += 1

    index -= 1  # Adjust index because we incremented it at the end of the loop

    return index
