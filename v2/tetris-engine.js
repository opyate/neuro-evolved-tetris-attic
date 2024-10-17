/**
 * TetrisEngine class that handles the game logic for Tetris.
 * 
 * It's decoupled from any rendering logic and game loops bound to a set FPS.
 * 
 * The engine can be initialised with any grid size.
 * 
 * Shapes and scores go hand in hand, where the score is based on the number of lines cleared.
 * So, if one of the shapes' longest side is 6, then the scores array has to
 * have a value at index 6, as it would be possible to clear 6 lines with that shape.
 */
class TetrisEngine {
    shapes = {
        "I": [
            [
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            [
                [0, 0, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 0]
            ],
            [
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0]
            ],
            [
                [0, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 0, 0]
            ]
        ],

        "J": [
            [
                [1, 0, 0],
                [1, 1, 1],
                [0, 0, 0]
            ],
            [
                [0, 1, 1],
                [0, 1, 0],
                [0, 1, 0]
            ],
            [
                [0, 0, 0],
                [1, 1, 1],
                [0, 0, 1]
            ],
            [
                [0, 1, 0],
                [0, 1, 0],
                [1, 1, 0]
            ]
        ],

        "L": [
            [
                [0, 0, 1],
                [1, 1, 1],
                [0, 0, 0]
            ],
            [
                [0, 1, 0],
                [0, 1, 0],
                [0, 1, 1]
            ],
            [
                [0, 0, 0],
                [1, 1, 1],
                [1, 0, 0]
            ],
            [
                [1, 1, 0],
                [0, 1, 0],
                [0, 1, 0]
            ]
        ],

        "O": [
            [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ],
            [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ],
            [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ],
            [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ]
        ],

        "S": [
            [
                [0, 1, 1],
                [1, 1, 0],
                [0, 0, 0]
            ],
            [
                [0, 1, 0],
                [0, 1, 1],
                [0, 0, 1]
            ],
            [
                [0, 0, 0],
                [0, 1, 1],
                [1, 1, 0]
            ],
            [
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0]
            ]
        ],

        "T": [
            [
                [0, 1, 0],
                [1, 1, 1],
                [0, 0, 0]
            ],
            [
                [0, 1, 0],
                [0, 1, 1],
                [0, 1, 0]
            ],
            [
                [0, 0, 0],
                [1, 1, 1],
                [0, 1, 0]
            ],
            [
                [0, 1, 0],
                [1, 1, 0],
                [0, 1, 0]
            ]
        ],

        "Z": [
            [
                [1, 1, 0],
                [0, 1, 1],
                [0, 0, 0]
            ],
            [
                [0, 0, 1],
                [0, 1, 1],
                [0, 1, 0]
            ],
            [
                [0, 0, 0],
                [1, 1, 0],
                [0, 1, 1]
            ],
            [
                [0, 1, 0],
                [1, 1, 0],
                [1, 0, 0]
            ]
        ]
    };
    scores = [0, 100, 300, 500, 800];

    constructor(width = 10, height = 20) {
        this.width = width;
        this.height = height;
        this.grid = Array.from({ length: this.height }, () => Array(this.width).fill(0));
        this.currentPiece = null;
        this.nextPiece = null;
        this.bag = []; // For "bag of seven" piece generation
        this.scoreForCurrentTick = 0;
        this.totalScore = 0;
        this.isGameOver = false;
        this.movesMade = [];
        this.countTicks = 0;
        this.wallKickCache = {}; // to prevent hovering pieces
        this.generateNewPiece(); // Start with a piece
        this.updateGrid();
    }

    getPieceFromBag() {
        // ensure bag is not empty
        if (this.bag.length === 0) {
            this.bag = Object.keys(this.shapes); // Fill the bag
            this.shuffleBag();
        }

        const shapeType = this.bag.pop();

        const pieceShape = this.getPieceShape(shapeType, 0);
        const topRowOffset = pieceShape.findIndex(row => row.some(cell => cell === 1));

        // Calculate center column of the piece
        let leftmostCol = pieceShape[0].length; // Assume the piece is full width initially
        let rightmostCol = 0;
        for (let row = 0; row < pieceShape.length; row++) {
            for (let col = 0; col < pieceShape[0].length; col++) {
                if (pieceShape[row][col]) {
                    leftmostCol = Math.min(leftmostCol, col);
                    rightmostCol = Math.max(rightmostCol, col);
                }
            }
        }
        const centerCol = Math.floor((leftmostCol + rightmostCol) / 2);

        const piece = {
            type: shapeType,
            rotation: 0,
            x: Math.floor(this.width / 2) - centerCol, // Center horizontally
            y: -topRowOffset, // Adjust the y position
        };

        return piece;
    }

    generateNewPiece() {
        this.currentPiece = this.getPieceFromBag()

        if (!this.nextPiece) {
            this.generateNextPiece();
        }
    }

    generateNextPiece() {
        this.nextPiece = this.getPieceFromBag();
        this.wallKickCache = {}; // Reset wall kick cache
    }

    shuffleBag() {
        // Fisher-Yates shuffle for randomness
        for (let i = this.bag.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.bag[i], this.bag[j]] = [this.bag[j], this.bag[i]];
        }
    }

    hasSingleRepetitions() {
        const N = 20;

        // Ensure there are at least N moves to check
        if (this.movesMade.length < N) {
            return false;
        }

        // we don't care if the last move was up or down,
        // because those moves progresses the game
        const lastMove = this.movesMade.slice(-1);
        if (lastMove === "up" || lastMove === "down") {
            return false;
        }

        const lastNMoves = this.movesMade.slice(-N);

        // Check for single repetition (e.g., right,right,right)
        return lastNMoves.every(move => move === lastNMoves[0]);
    }

    hasDoubleRepetitions() {
        const N = 30;

        // Ensure there are at least N moves to check
        if (this.movesMade.length < N) {
            return false;
        }

        // we don't care if the last move was up or down,
        // because those moves progresses the game
        const lastMove = this.movesMade.slice(-1);
        if (lastMove === "up" || lastMove === "down") {
            return false;
        }

        const lastNMoves = this.movesMade.slice(-N);

        // for l,r,l,r,l,r, get first = l,l,l and second = r,r,r
        const firstMoves = lastNMoves.filter((_, i) => i % 2 === 0);
        const secondMoves = lastNMoves.filter((_, i) => i % 2 === 1);

        const firstMoveRepetition = firstMoves.every(move => move === firstMoves[0]);
        const secondMoveRepetition = secondMoves.every(move => move === secondMoves[0]);

        return firstMoveRepetition && secondMoveRepetition;
    }

    /**
     * Some bots get stuck in an endless loop of making the same moves.
     * This method checks for repetitions in the last few moves.
     * 
     * @returns true or false
     */
    hasRepetitions() {
        return this.hasSingleRepetitions() || this.hasDoubleRepetitions();
    }

    tick() {
        if (this.isGameOver) return;
        if (!this.currentPiece) return; // No piece in play
        this.countTicks++;
        this.scoreForCurrentTick = 0; // Reset score for this tick

        // Attempt to move down
        if (this.isValidMove(this.currentPiece.x, this.currentPiece.y + 1, this.currentPiece.rotation)) {
            this.currentPiece.y++;
        } else {
            // Piece landed, lock it in
            this.lockPiece();
            this.clearLines();
            this.currentPiece = this.nextPiece;
            this.generateNextPiece();

            if (!this.isValidMove(this.currentPiece.x, this.currentPiece.y, this.currentPiece.rotation)) {
                // Game over if new piece can't spawn
                // Handle game over logic here
                this.isGameOver = true;
            }
        }

        this.updateGrid();
    }

    /**
     * Move the piece up, down, left, or right.
     * 
     * Up/down effects are instant drop and soft drop as per
     * https://tetris.wiki/Drop
     * 
     * @param {*} move
     * @returns 
     */
    movePiece(move) {
        if (this.isGameOver) return;
        if (!this.currentPiece) return;
        this.movesMade.push(move);

        if (this.hasRepetitions()) {
            this.isGameOver = true;
            this.updateGrid();
            return;
        }

        switch (move) {
            case "up":  // Instant Drop
                while (this.isValidMove(this.currentPiece.x, this.currentPiece.y + 1, this.currentPiece.rotation)) {
                    this.currentPiece.y++;
                }
                this.lockPiece();
                this.clearLines();
                this.currentPiece = this.nextPiece;
                this.generateNextPiece();
                if (!this.isValidMove(this.currentPiece.x, this.currentPiece.y, this.currentPiece.rotation)) {
                    this.isGameOver = true;
                }
                this.updateGrid();
                break;
            case "down":  // Soft Drop
                if (this.isValidMove(this.currentPiece.x, this.currentPiece.y + 1, this.currentPiece.rotation)) {
                    this.currentPiece.y++;
                    this.updateGrid();
                }
                break;
            case "left":

                if (this.isValidMove(this.currentPiece.x - 1, this.currentPiece.y, this.currentPiece.rotation)) {
                    this.currentPiece.x--;
                    this.updateGrid();
                }
                break;
            case "right":
                if (this.isValidMove(this.currentPiece.x + 1, this.currentPiece.y, this.currentPiece.rotation)) {
                    this.currentPiece.x++;
                    this.updateGrid();
                }
                break;
            case "rotate_cw":
                this.rotatePiece(1); // calls updateGrid()
                break;
            case "rotate_ccw":
                this.rotatePiece(-1); // calls updateGrid()
                break;
            default:
                break;
        }
    }

    /**
     * Checks if a potential move is valid by iterating through 
     * the piece's shape and ensuring no out-of-bounds or 
     * overlapping positions occur.
     * 
     * @param {*} x 
     * @param {*} y 
     * @param {*} rotation 
     * @returns 
     */
    isValidMove(x, y, rotation) {
        const piece = this.getPieceShape(this.currentPiece.type, rotation);

        for (let row = 0; row < piece.length; row++) {
            for (let col = 0; col < piece[0].length; col++) {
                if (piece[row][col]) {
                    const newX = x + col;
                    const newY = y + row;

                    // Check if out of bounds or overlapping existing blocks
                    if (newX < 0 || newX >= this.width || newY >= this.height || (newY >= 0 && ![0, 1].includes(this.grid[newY][newX]))) { // Check for any non-zero value
                        return false;
                    }
                }
            }
        }

        return true;
    }

    /**
     * Places the current piece onto the grid by
     * marking the corresponding cells as occupied.
     */
    lockPiece() {
        const piece = this.getPieceShape(this.currentPiece.type, this.currentPiece.rotation);

        for (let row = 0; row < piece.length; row++) {
            for (let col = 0; col < piece[0].length; col++) {
                if (piece[row][col]) {
                    const x = this.currentPiece.x + col;
                    const y = this.currentPiece.y + row;

                    if (y >= 0) { // Ensure it's within the grid
                        // Mark cell as occupied
                        this.grid[y][x] = this.currentPiece.type;
                    }
                }
            }
        }
    }

    /**
     * Scans the grid from bottom to top, removing any full rows 
     * and shifting the remaining rows down. It also keeps 
     * track of the number of lines cleared.
     * 
     * Then it assigns a score based on the number of lines cleared, 
     * as per https://tetris.wiki/Scoring
     */
    clearLines() {
        const fullRowIndices = []; // Array to store indices of full rows

        for (let row = this.height - 1; row >= 0; row--) { // Start from the bottom
            if (this.grid[row].every(cell => cell !== 0)) { // Full row
                fullRowIndices.push(row);
            }
        }

        if (fullRowIndices.length === 0) return; // No lines to clear

        // Remove full rows and shift down
        for (const rowIndex of fullRowIndices) {
            this.grid.splice(rowIndex, 1); // Remove the row at the specific index
            this.grid.unshift(Array(this.width).fill(0)); // Add empty row at the top
        }

        // Update score based on linesCleared
        this.scoreForCurrentTick = this.scores[fullRowIndices.length];
        this.totalScore += this.scoreForCurrentTick;
    }

    getPieceShape(type, rotation) {
        return this.shapes[type][rotation];
    }

    /**
     * Rotate piece using the SRS strategy (Super Rotation System).
     * https://tetris.wiki/Super_Rotation_System
     * 
     * @param {*} direction 
     * @returns 
     */
    rotatePiece(direction) { // direction: 1 for clockwise, -1 for counterclockwise
        if (this.isGameOver) return;
        if (!this.currentPiece) return;

        const newRotation = (this.currentPiece.rotation + direction + 4) % 4;
        const pieceType = this.currentPiece.type;

        if (pieceType === "O") return; // O piece doesn't rotate

        // Wall Kick Data (excluding Arika)
        const wallKickDataForJLSZT = {
            '0->R': [[0, 0], [-1, 0], [-1, 1], [0, -2], [-1, -2]],
            'R->0': [[0, 0], [1, 0], [1, -1], [0, 2], [1, 2]],
            'R->2': [[0, 0], [1, 0], [1, -1], [0, 2], [1, 2]],
            '2->R': [[0, 0], [-1, 0], [-1, 1], [0, -2], [-1, -2]],
            '2->L': [[0, 0], [1, 0], [1, 1], [0, -2], [1, -2]],
            'L->2': [[0, 0], [-1, 0], [-1, -1], [0, 2], [-1, 2]],
            'L->0': [[0, 0], [-1, 0], [-1, -1], [0, 2], [-1, 2]],
            '0->L': [[0, 0], [1, 0], [1, 1], [0, -2], [1, -2]]
        };
        const wallKickData = {
            "O": {}, // No rotations needed for O piece
            "I": {
                '0->R': [[0, 0], [-2, 0], [1, 0], [-2, -1], [1, 2]],
                'R->0': [[0, 0], [2, 0], [-1, 0], [2, 1], [-1, -2]],
                'R->2': [[0, 0], [-1, 0], [2, 0], [-1, 2], [2, -1]],
                '2->R': [[0, 0], [1, 0], [-2, 0], [1, -2], [-2, 1]],
                '2->L': [[0, 0], [2, 0], [-1, 0], [2, 1], [-1, -2]],
                'L->2': [[0, 0], [-2, 0], [1, 0], [-2, -1], [1, 2]],
                'L->0': [[0, 0], [1, 0], [-2, 0], [1, -2], [-2, 1]],
                '0->L': [[0, 0], [-1, 0], [2, 0], [-1, 2], [2, -1]]
            },
            "J": wallKickDataForJLSZT,
            "L": wallKickDataForJLSZT,
            "S": wallKickDataForJLSZT,
            "T": wallKickDataForJLSZT,
            "Z": wallKickDataForJLSZT,
        };

        const startRotationState = this.currentPiece.rotation === 1 ? 'R' : (this.currentPiece.rotation === 3 ? 'L' : this.currentPiece.rotation);
        const endRotationState = newRotation === 1 ? 'R' : (newRotation === 3 ? 'L' : newRotation);
        const currentRotationState = startRotationState + '->' + endRotationState;

        // Try each wall kick test
        for (const test of wallKickData[pieceType][currentRotationState]) {
            const newX = this.currentPiece.x + test[0];
            const newY = this.currentPiece.y + test[1];

            // Check if this wall kick has been used at this position before
            const cacheKey = `${pieceType}-${this.currentPiece.x}-${this.currentPiece.y}-${currentRotationState}-${test[0]}-${test[1]}`;
            if (this.wallKickCache[cacheKey]) {
                continue; // Skip this wall kick if it's been used at this position
            }

            if (this.isValidMove(newX, newY, newRotation)) {
                this.currentPiece.x = newX;
                this.currentPiece.y = newY;
                this.currentPiece.rotation = newRotation;

                // Store the successful wall kick in the cache
                this.wallKickCache[cacheKey] = true;

                this.updateGrid();

                return; // Rotation successful
            }
        }

        // All tests failed, rotation not possible
    }

    updateGrid() {
        // Create a temporary grid to store the updated state
        const newGrid = Array.from({ length: this.height }, () => Array(this.width).fill(0));

        // Copy existing locked pieces to the new grid
        for (let row = 0; row < this.height; row++) {
            for (let col = 0; col < this.width; col++) {
                if (typeof this.grid[row][col] === 'string') { // If it's a locked piece (a letter)
                    newGrid[row][col] = this.grid[row][col];
                }
            }
        }

        // Place the current piece on the new grid
        if (this.currentPiece) {
            const pieceShape = this.getPieceShape(this.currentPiece.type, this.currentPiece.rotation);
            for (let row = 0; row < pieceShape.length; row++) {
                for (let col = 0; col < pieceShape[0].length; col++) {
                    if (pieceShape[row][col]) {
                        const x = this.currentPiece.x + col;
                        const y = this.currentPiece.y + row;
                        if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
                            newGrid[y][x] = 1; // Piece in play
                        }
                    }
                }
            }
        }

        // Update the main grid with the new state
        this.grid = newGrid;
    }

}
