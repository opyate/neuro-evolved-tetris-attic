let workers = [];
let workerStates = []
let roundsCount = 0;

// counts that let us track when all workers have done a task
let count_crossover = new Set();
let count_save = new Set();
let isDone_evolved = true;

let count_init = new Set();
let isDone_init = false;


/**
 * Given NUMBER_OF_GAMES = 100 and BLOCK_SIZE_PIXELS = 5:
 * - the canvas will render all the Tetris games
 * - there will be 100 Tetris games in a 10x10 grid
 * - each cell in this grid will be a Tetris game
 * - each game will be 10x10 blocks
 * - each block will be 5x5 pixels
 * - the width of one game will be 50 pixels
 * - the height of one game will be 50 pixels
 * - the width of the canvas will be 500 pixels
 * - the height of the canvas will be 500 pixels
 */
function setup() {
    console.log("🎲 Starting simulation...")
    createCanvas(COLS * WIDTH * BLOCK_SIZE_PIXELS, ROWS * HEIGHT * BLOCK_SIZE_PIXELS);

    for (let id = 0; id < NUMBER_OF_GAMES; id++) {
        workers[id] = new Worker('tetris-robot.js');
        workerStates[id] = null;

        workers[id].onmessage = function (e) {
            const { msgType, msgData } = e.data;
            if (id !== msgData.id) {
                throw new Error(`world: worker.id=${id} Received message from wrong worker ${msgData.id}`);
            }
            switch (msgType) {
                case "init":
                    workerStates[id] = msgData.state;
                    count_init.add(id);
                    console.log("⏳ init worker...");
                    if (count_init.size === NUMBER_OF_GAMES) {
                        isDone_init = true;
                        count_init = new Set();
                        console.log("🎉 init workers DONE");
                        console.log(`🕹️ Starting round ${roundsCount}`);
                    }
                    break;
                case "move":
                    workerStates[id] = msgData.state;
                    break;
                case "crossover":
                    workerStates[id] = msgData.state;
                    count_crossover.add(id);
                    console.log("⏳ evolving brain...");
                    if (count_crossover.size === NUMBER_OF_GAMES) {
                        count_crossover = new Set();
                        console.log("🤯 evolving brains DONE")
                        evolve_stage3();
                    }
                    break;
                case "save":
                    count_save.add(id);
                    // all workers have to save their ml5 brains to IndexedDB
                    // before we start the crossover step, which reads those
                    // brains back out from IndexedDB
                    console.log("⏳ persisting brain...");
                    if (count_save.size === NUMBER_OF_GAMES) {
                        count_save = new Set();
                        console.log("🖫 persisting brains DONE")
                        evolve_stage2();
                    }
                    break;
                default:
                    throw new Error(`world: worker.id=${id} Unknown message type ${msgType}`);
            }
        }
    }

    for (let id = 0; id < NUMBER_OF_GAMES; id++) {
        workers[id].postMessage({ msgType: "init", msgData: { id, width: WIDTH, height: HEIGHT } });
        // workers[id].postMessage({ msgType: "move", msgData: { id } });
    }

    // clear the canvas
    background(255);
}

var frameCount = 0;
function draw() {
    if (!isDone_init) {
        return;
    }
    if (!isDone_evolved) {
        return;
    }

    let doTick = false;
    frameCount++;
    // A tick moves the piece down outside of the player's control,
    // and FRAMES_UNTIL_TICK should give the player enough cycles to
    // move the piece to the desired location. Adjust as desired.
    if (frameCount >= FRAMES_UNTIL_TICK) {
        frameCount = 0;
        doTick = true;
    }

    let countAlive = 0;
    let workerIndex = 0;
    for (let id = 0; id < NUMBER_OF_GAMES; id++) {
        const workerState = workerStates[id];

        if (!workerState.engine.isGameOver) {
            workers[id].postMessage({ msgType: "move", msgData: { id, doTick } });
            countAlive++;

            // TODO wait for everyone to move?
        }

        // draw the game
        drawGame(workerState, workerIndex);

        workerIndex++;
    }

    if (countAlive === 0) {
        startNewRound()
    }
}

function getColour(cellValue, workerState) {
    if (workerState.engine.score > 0) {
        if (cellValue === 0) {
            // highlight the scoring workers with a light pink background
            return color("#fee6fa");
        }
    }
    if (workerState.engine.isGameOver) {
        if (cellValue === 0) {
            return color(255);
        } else {
            // game over is grayed out
            return color(127 + 64);
        }
    }
    switch (cellValue) {
        case 0:
            return color(255);
        case 1:
            return color(64);
        case "I":
            return color(153, 255, 255);  // Soft Cyan
        case "J":
            return color(153, 204, 255);  // Soft Blue
        case "T":
            return color(204, 153, 255);  // Soft Purple
        case "S":
            return color(153, 255, 153);  // Soft Green
        case "Z":
            return color(255, 153, 153);  // Soft Red
        case "O":
            return color(255, 255, 153);  // Soft Yellow
        case "L":
            return color(255, 204, 153);  // Soft Orange
        default:
            // shouldn't happen
            console.error("Unknown cell value: " + cellValue);
            return color(255);
    }
}

function drawGame(workerState, workerIndex) {
    // clear this portion of the canvas
    fill(255);
    noStroke();
    rect((workerIndex % COLS) * WIDTH * BLOCK_SIZE_PIXELS, Math.floor(workerIndex / COLS) * HEIGHT * BLOCK_SIZE_PIXELS, WIDTH * BLOCK_SIZE_PIXELS, HEIGHT * BLOCK_SIZE_PIXELS);

    for (let row = 0; row < workerState.height; row++) {
        for (let col = 0; col < workerState.width; col++) {
            let cellValue = workerState.engine.grid[row][col];
            // calculate x and y so all games are packed according to the grid
            let x = (workerIndex % COLS) * WIDTH * BLOCK_SIZE_PIXELS + col * BLOCK_SIZE_PIXELS;
            let y = Math.floor(workerIndex / COLS) * HEIGHT * BLOCK_SIZE_PIXELS + row * BLOCK_SIZE_PIXELS;
            fill(getColour(cellValue, workerState));

            stroke(127 + 64);
            rect(x, y, BLOCK_SIZE_PIXELS, BLOCK_SIZE_PIXELS);
        }
    }

    // draw bounding rectangle
    stroke(0);
    noFill();
    rect((workerIndex % COLS) * WIDTH * BLOCK_SIZE_PIXELS, Math.floor(workerIndex / COLS) * HEIGHT * BLOCK_SIZE_PIXELS, WIDTH * BLOCK_SIZE_PIXELS, HEIGHT * BLOCK_SIZE_PIXELS);
}

function startNewRound() {
    console.log(`🛑 Stopping round ${roundsCount}`);
    roundsCount++;
    isDone_evolved = false;
    evolve_stage1();
}

let totalFitness = 0;
function evolve_stage1() {
    // calculate total fitness, and as we're looping, take the
    // opportunity to serialise all brains
    totalFitness = 0;
    for (let id = 0; id < NUMBER_OF_GAMES; id++) {
        totalFitness += workerStates[id].fitness;
        workers[id].postMessage({ msgType: "save", msgData: { id } });
    }
}

function evolve_stage2() {
    const crossovers = [];
    for (let id = 0; id < NUMBER_OF_GAMES; id++) {
        let idA = weightedSelection(totalFitness);
        let idB = weightedSelection(totalFitness);
        crossovers.push({ idA, idB });
    }

    for (let id = 0; id < NUMBER_OF_GAMES; id++) {
        const crossover = crossovers[id];
        workers[id].postMessage({ msgType: "crossover", msgData: { id, crossover } });
    }
}

function evolve_stage3() {
    // reset all flags
    isDone_evolved = true;

    // clear the canvas
    background(255);

    console.log(`🕹️ Starting round ${roundsCount}`);
}

/**
 * Returns the index of the worker with the highest fitness
 * as per a relay-race technique for giving a fair shot to
 * all members of a population.
 * 
 * @param {*} totalFitness 
 * @returns 
 */
function weightedSelection(totalFitness) {
    // Start with the first element
    let index = 0;
    // Pick a starting point
    let start = random(1);
    // At the finish line?
    while (start > 0) {
        const normalisedFitness = workerStates[index].fitness / totalFitness;
        // Move a distance according to fitness
        start = start - normalisedFitness;
        // Next element
        index++;
    }
    // Undo moving to the next element since the finish has been reached
    index--;

    return index;
}
