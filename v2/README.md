# Intro

v2 of web app which runs many Tetris bots.

Runs each bot in a web worker, but since binary weights can not be serialised, each bot saves its weights (using Tensorflow's internal `tf.save("indexeddb://...`) and reads other bots' weights before doing cross-over.

It uses a custom ml5 which has support for persisting to IndexedDB: https://github.com/opyate/ml5-next-gen/tree/feature/nn-indexeddb

For many workers, check `about:config` then `dom.workers.maxPerDomain` is at least a few points more than the number of workers you want to spawn.
 
Possibly also max out your soft ulimit to be the same as your hard ulimit:

```
ulimit -Sn $(ulimit -Hn)
```

However, I suspect having too many web workers, and/or making parallel reads/writes to IndexedDB introduces new overheads/bottlenecks.

# Run

A dedicated web server is needed for loading web worker code:

```
python3 serve.py -u
```

Then go to `http://localhost:8080/index.html`

Add `?games=100` to run 100 bots.

