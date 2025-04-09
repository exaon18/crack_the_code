def count_completed_lines(board):
    completed = 0
    size = len(board)  # should be 5 for a 5x5 board

    # Check for complete rows
    for row in board:
        if all(cell == 1 for cell in row):
            completed += 1

    # Check for complete columns
    for col in range(size):
        if all(board[row][col] == 1 for row in range(size)):
            completed += 1

    # Check main diagonal (top-left to bottom-right)
    if all(board[i][i] == 1 for i in range(size)):
        completed += 1

    # Check anti-diagonal (top-right to bottom-left)
    if all(board[i][size - 1 - i] == 1 for i in range(size)):
        completed += 1

    return completed

# Example usage:
bingo_board = [
    [1, 1, 1, 1, 1],  # Complete row (counts as 1)
    [0, 1, 0, 1, 1],
    [1, 1, 1, 1, 1],  # Complete row (counts as 1)
    [1, 1, 1, 1, 1],  # Complete row (counts as 1)
    [1, 1, 1, 1, 1]   # Complete row (counts as 1)
]

# Optionally, if the main diagonal is complete, it adds another count
# and if the anti-diagonal is complete, it adds yet another count.
# In this example, both diagonals are also complete.

result = count_completed_lines(bingo_board)
print("Total completed lines:", result)
