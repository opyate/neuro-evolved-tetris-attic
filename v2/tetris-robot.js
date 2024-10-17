importScripts("tetris-engine.js", "libraries/ml5.min.js");

function getNN(width, height) {
    return ml5.neuralNetwork({
        inputs: width * height,
        outputs: ["up", "down", "left", "right", "rotate_cw", "rotate_ccw", "noop"],
        task: "classification",
        neuroEvolution: true,
    });
}

/**
 * A self-playing Tetris game.
 * 
 * It uses a neural network to play the game,
 * by predicting the next move.
 * 
 * Contains game state.
 * 
 * As ml5's underlying TF weights can not be serialised across web workers'
 * postMessage, we have save/load functions which uses IndexedDB.
 */
class TetrisRobot {
    init(id, width, height, brain) {
        this.id = id;
        this.width = width;
        this.height = height;
        this.engine = new TetrisEngine(width, height);
        this.fitness = 0;

        if (brain) {
            this.brain = brain;
        } else {
            this.brain = getNN(width, height);
        }
    }

    getGameStateAsInputs() {
        let inputs = [];
        for (let row = 0; row < this.height; row++) {
            for (let col = 0; col < this.width; col++) {
                let cellValue = this.engine.grid[row][col];
                // cellValue is one of the following:
                // 0: empty cell
                // 1: piece-in-play
                // I/T/S/Z/J/L/O: locked piece

                // Let the locked pieces be 0.5
                // if the cell value is not a number, set it to 0.5
                if (Number.isInteger(cellValue)) {
                    inputs.push(parseFloat(cellValue));
                } else {
                    inputs.push(0.5);
                }
            }
        }
        return inputs;
    }

    thinkThenMove(doTick) {
        if (this.engine.isGameOver) {
            return;
        }

        let inputs = this.getGameStateAsInputs();

        let results = this.brain.classifySync(inputs);

        this.engine.movePiece(results[0].label);

        // incentivise movement
        if (results[0].label !== "noop") {
            this.fitness += 1;
        }

        // uncomment this to see the grids fill up on the right
        // if (results[0].label === "right") {
        //     this.fitness += 1000;
        // }

        if (doTick) {
            // incentivise longevity
            this.fitness += 1;

            this.engine.tick();
            // if a bot learns to press up/down more often,
            // and not wait for game ticks to progress the piece,
            // then it will reach higher fitness sooner.
            this.fitness += this.engine.scoreForCurrentTick;
        }
    }

    getState() {
        return {
            id: this.id,
            width: this.width,
            height: this.height,
            engine: this.engine,
            fitness: this.fitness,
        };
    }

    async save(name) {
        await this.brain.saveIdb(name);
    }

    async crossover(a, b) {
        let brainA = getNN(this.width, this.height);
        await brainA.loadIdb(`robot-${a}`);

        let brainB = getNN(this.width, this.height);
        await brainB.loadIdb(`robot-${b}`);

        let child = brainA.crossover(brainB);
        child.mutate(0.01);

        // re-init with new brain
        // Note that this doesn't affect other crossovers, as init
        // does not save the brains to IndexedDB.
        this.init(this.id, this.width, this.height, child);
    }
}

const robot = new TetrisRobot();

ml5.tf.setBackend("cpu");

self.onmessage = function (e) {
    const { msgType, msgData } = e.data;
    const id = msgData.id;
    if (robot.id !== undefined && id !== robot.id) {
        throw new Error(`worker: robot.id=${robot.id} Received message for wrong robot ${id}`);
    }
    switch (msgType) {
        case "init":
            robot.init(id, msgData.width, msgData.height);
            postMessage({
                msgType: "init",
                msgData: {
                    id: robot.id,
                    state: robot.getState(),
                },
            });
            break;
        case "move":
            robot.thinkThenMove(msgData.doTick);
            postMessage({
                msgType: "move",
                msgData: {
                    id: robot.id,
                    state: robot.getState(),
                }
            });
            break;
        case "save":
            robot.save(`robot-${id}`).then(() => {
                postMessage({
                    msgType: "save",
                    msgData: {
                        id: robot.id,
                    }
                });
            });
            break;
        case "crossover":
            const { idA, idB } = msgData.crossover;
            robot.crossover(idA, idB).then(() => {
                postMessage({
                    msgType: "crossover",
                    msgData: {
                        id: robot.id,
                        state: robot.getState(),
                    }
                });
            });
            break;
        default:
            throw new Error(`worker: robot.id=${robot.id} Unknown message type ${msgType}`);
    }
}
