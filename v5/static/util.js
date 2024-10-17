/**
 * Attempts to calculate the grid size that will fit the given number of elements
 * into a grid that adheres to the given viewports' dimensions as per
 * screenWidth and screenHeight.
 * 
 * @param {*} numElements 
 * @param {*} screenWidth 
 * @param {*} screenHeight 
 * @returns 
 */
function calculateGridSize(numElements, screenWidth, screenHeight) {
    const screenAspectRatio = screenWidth / screenHeight;

    // Start with a square-like grid
    let gridWidth = Math.floor(Math.sqrt(numElements));
    let gridHeight = Math.ceil(numElements / gridWidth);

    // Adjust the grid dimensions to match the screen aspect ratio
    let gridAspectRatio = gridWidth / gridHeight;
    if (gridAspectRatio > screenAspectRatio) {
        // Grid is wider than the screen, reduce width and increase height
        while (gridAspectRatio > screenAspectRatio && gridWidth > 1) {
            gridWidth--;
            gridHeight = Math.ceil(numElements / gridWidth);
            gridAspectRatio = gridWidth / gridHeight;
        }
    } else if (gridAspectRatio < screenAspectRatio) {
        // Grid is taller than the screen, increase width and reduce height
        while (gridAspectRatio < screenAspectRatio && gridHeight > 1) {
            gridHeight--;
            gridWidth = Math.ceil(numElements / gridHeight);
            gridAspectRatio = gridWidth / gridHeight;
        }
    }

    return { gridWidth, gridHeight };
}
