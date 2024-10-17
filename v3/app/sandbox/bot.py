from app.tetris_bot import TetrisBot


bot0 = TetrisBot(bot_id=0)
# bot0.brain.fc1.weight
# bot0.brain.fc1.bias
bot1 = TetrisBot(bot_id=1)

# make a few moves
# [bot0.think_then_move()] * 40
# [bot1.think_then_move()] * 40
count = 0
while bot0.think_then_move():
    count += 1
    if count > 40:
        break
    pass
count = 0
while bot1.think_then_move():
    count += 1
    if count > 40:
        break
    pass


# final tick
print(bot0.think_then_move(True))
print(bot1.think_then_move(True))

# do crossover
bot0.crossover(bot0, bot1)
bot1.crossover(bot1, bot0)

# re-init
bot0.reinit()
bot1.reinit()

# make a few moves
[bot0.think_then_move()] * 40
[bot1.think_then_move()] * 40
