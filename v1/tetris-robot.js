/**
 * A self-playing Tetris game.
 * 
 * It uses a neural network to play the game,
 * by predicting the next move.
 * 
 * Contains game state.
 */
class TetrisRobot {
    constructor(width, height, brain = null) {
        this.width = width;
        this.height = height;
        this.engine = new TetrisEngine(width, height);
        this.fitness = 0;

        if (brain) {
            this.brain = brain;
        } else {
            this.brain = ml5.neuralNetwork({
                inputs: width * height,
                outputs: ["up", "down", "left", "right", "rotate_cw", "rotate_ccw", "noop"],
                task: "classification",
                neuroEvolution: true,
            });
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

        switch (results[0].label) {
            case "up":
                this.engine.moveUp();
                break;
            case "down":
                this.engine.moveDown();
                break;
            case "left":
                this.engine.moveLeft();
                break;
            case "right":
                this.engine.moveRight();
                break;
            case "rotate_cw":
                this.engine.rotateClockwise();
                break;
            case "rotate_ccw":
                this.engine.rotateCounterClockwise();
                break;
            case "noop":
                break;
        }
        if (doTick) {
            this.engine.tick();
            // if a bot learns to press up/down more often,
            // and not wait for game ticks to progress the piece,
            // then it will reach higher fitness sooner.
            this.fitness = this.engine.score;
        }
    }
}
