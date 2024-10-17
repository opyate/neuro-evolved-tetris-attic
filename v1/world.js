let robots = [];

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
    createCanvas(COLS * WIDTH * BLOCK_SIZE_PIXELS, ROWS * HEIGHT * BLOCK_SIZE_PIXELS);

    ml5.tf.setBackend("cpu");

    for (let i = 0; i < NUMBER_OF_GAMES; i++) {
        robots[i] = new TetrisRobot(WIDTH, HEIGHT);
    }

    // clear the canvas
    background(255);
}

var frameCount = 0;
function draw() {
    let doTick = false;
    frameCount++;
    if (frameCount === FRAMES_UNTIL_TICK) {
        frameCount = 0;
        doTick = true;
    }

    let countAlive = 0;
    let robotIdx = 0;
    for (let robot of robots) {
        if (!robot.engine.isGameOver) {
            robot.thinkThenMove(doTick);
            countAlive++;

            // draw the game
            drawGame(robot, robotIdx);
        }

        robotIdx++;
    }

    if (countAlive === 0) {
        startNewRound()
    }
}

function getColour(cellValue, robot) {
    if (robot.engine.score > 0) {
        if (cellValue === 0) {
            // highlight the scoring workers with a light pink background
            return color("#fee6fa");
        }
    }
    if (robot.engine.isGameOver) {
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

function drawGame(robot, robotIdx) {
    // clear this portion of the canvas
    fill(255);
    noStroke();
    rect((robotIdx % COLS) * WIDTH * BLOCK_SIZE_PIXELS, Math.floor(robotIdx / COLS) * HEIGHT * BLOCK_SIZE_PIXELS, WIDTH * BLOCK_SIZE_PIXELS, HEIGHT * BLOCK_SIZE_PIXELS);

    for (let row = 0; row < robot.height; row++) {
        for (let col = 0; col < robot.width; col++) {
            let cellValue = robot.engine.grid[row][col];
            // calculate x and y so all games are packed according to the grid
            let x = (robotIdx % COLS) * WIDTH * BLOCK_SIZE_PIXELS + col * BLOCK_SIZE_PIXELS;
            let y = Math.floor(robotIdx / COLS) * HEIGHT * BLOCK_SIZE_PIXELS + row * BLOCK_SIZE_PIXELS;
            fill(getColour(cellValue, robot));

            stroke(127 + 64);
            rect(x, y, BLOCK_SIZE_PIXELS, BLOCK_SIZE_PIXELS);
        }
    }

    // draw bounding rectangle
    stroke(0);
    noFill();
    rect((robotIdx % COLS) * WIDTH * BLOCK_SIZE_PIXELS, Math.floor(robotIdx / COLS) * HEIGHT * BLOCK_SIZE_PIXELS, WIDTH * BLOCK_SIZE_PIXELS, HEIGHT * BLOCK_SIZE_PIXELS);
}

function startNewRound() {
    console.log("Starting new round");
    normalizeFitness();
    reproduction();

    // clear the canvas
    background(255);
}

function reproduction() {
    let nextRobots = [];
    for (let i = 0; i < robots.length; i++) {
        let parentA = weightedSelection();
        let parentB = weightedSelection();
        let child = parentA.crossover(parentB);
        child.mutate(0.01);
        nextRobots[i] = new TetrisRobot(WIDTH, HEIGHT, child);
    }

    // garbage collect robots
    for (let robot of robots) {
        robot.brain = null;
        robot = null;
    }

    robots = nextRobots;
}

// Normalize all fitness values
function normalizeFitness() {
    let sum = 0;
    for (let robot of robots) {
        sum += robot.fitness;
    }
    for (let robot of robots) {
        robot.fitness = robot.fitness / sum;
    }
}

function weightedSelection() {
    // Start with the first element
    let index = 0;
    // Pick a starting point
    let start = random(1);
    // At the finish line?
    while (start > 0) {
        // Move a distance according to fitness
        start = start - robots[index].fitness;
        // Next element
        index++;
    }
    // Undo moving to the next element since the finish has been reached
    index--;
    // Instead of returning the entire Robot object, just the brain is returned
    return robots[index].brain;
}
