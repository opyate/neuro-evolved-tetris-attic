# Intro

Neuro-evolutionary bots that learn to play Tetris, by spawning thousands of bots, then doing crossover on weighted selections of nets (virtual coin flip whether a weight comes from parent A or B), then mutation (a small percent chance that any given weight will mutate, mimicking real-world genetic mutations, which typically introduce minor changes rather than entirely new traits).

[Video](https://www.youtube.com/watch?v=Q1aHP5IODUs):

[![Video](https://img.youtube.com/vi/Q1aHP5IODUs/0.jpg)](https://www.youtube.com/watch?v=Q1aHP5IODUs)

# Versions

## v1

Single-threaded static index.html

See [v1/README.md](v1/README.md)

## v2

One web worker per bot, static HTML, however with a simple web server so web worker code can load properly.

See [v2/README.md](v2/README.md)

## v3

Client/server setup, with ported PyTorch code.

See [v3/README.md](v3/README.md)

## v4

Using Celery for workers.

See [v4/README.md](v4/README.md)

## v5

**Use this one!**

Docker scaled workers, with light-weight Redis-backed coordinator. (Experiment v4 slowed down too much when the results were aggregated in the Celery chord.)

See [v5/README.md](v5/README.md)

