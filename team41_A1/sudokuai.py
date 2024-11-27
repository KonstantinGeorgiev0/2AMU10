#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    Use the self.propose move method of the SudokuAI class to propose the move 
    that you want your agent to play in the current turn.
    """

    def init(self):
        super().init()

    def compute_best_move(self, game_state: GameState) -> None:
        N = game_state.board.N
        # scoring for number of completed regions
        regions_score = {0: 0, 1: 1, 2: 3, 3: 7}

        def legal_moves(square, value, board):
            """Check whether move is legal."""
            # check if square is legal by
            # checking if the cell is empty
            # and check if the move is a taboo move
            cell_is_empty = game_state.board.get(square) == SudokuBoard.empty
            move_not_taboo = TabooMove(square, value) not in game_state.taboo_moves
            # if the cell is not empty or the move is taboo, the move is illegal, therefore False is returned
            if not cell_is_empty or not move_not_taboo:
                return False
            # check if move is in allowed squares
            if square not in game_state.player_squares():
                return False
            # check if value is legal
            # take the coordinates of the value
            grid_coords = [square[0] // board.m, square[1] // board.n]
            # take the values in each row, each column and each block
            row_values = [board.get((square[0], c)) for c in range(board.N)]
            col_values = [board.get((r, square[1])) for r in range(board.N)]
            if game_state.current_player == 1:
                block_values = [
                    board.get((board.m * grid_coords[0] + r, board.n * grid_coords[1] + c))
                    for r in range(board.m)
                    for c in range(board.n)
                ]
            else:
                block_values = [
                    board.get((board.m * (grid_coords[0] + 1) - r - 1, board.n * (grid_coords[1] + 1) - c - 1))
                    for r in range(board.m)
                    for c in range(board.n)
                ]
            # The same value shouldn't be in the same row, same column, or same block
            return value not in row_values and value not in col_values and value not in block_values

        def generate_legal_moves(board):
            """Generate all possible legal moves and return them"""
            moves = []
            for i in range(board.N):
                for j in range(board.N):
                    if board.get((i, j)) == SudokuBoard.empty:
                        for value in range(1, board.N + 1):
                            if legal_moves((i, j), value, board):
                                moves.append(Move((i, j), value))
            return moves

        def compute_completed_regions(board, i, j):
            """Compute the number of completed regions in the board."""
            grid_coords = [i // board.m, j // board.n]
            regions = [
                [board.get((i, c)) for c in range(board.N)],
                [board.get((r, j)) for r in range(board.N)],
                [
                    board.get((board.m * grid_coords[0] + r, board.n * grid_coords[1] + c))
                    for r in range(board.m)
                    for c in range(board.n)
                ],
            ]

            # regions that do not contain empty cells
            completed_regions = sum(
                all(cell != SudokuBoard.empty for cell in region)
                for region in regions
            )

            # return score based on the number of completed regions
            return regions_score[completed_regions]

        def evaluation(board):
            """Evaluate the score of the current board based on the number of completed regions."""
            score = 0
            for i in range(board.N):
                for j in range(board.N):
                    if board.get((i, j)) == SudokuBoard.empty:
                        for value in range(1, board.N + 1):
                            if legal_moves((i, j), value, board):
                                new_board = board
                                new_board.put((i, j), value)
                                # update score based on completed regions
                                score += compute_completed_regions(new_board, i, j)
            return score

        def minimax(grid, depth, alpha, beta, is_maximizing_player):
            """Minimax algorithm with alpha-beta pruning."""
            # base case
            if depth == 0:
                return evaluation(grid)

            # recursive case for max player
            if is_maximizing_player:
                max_eval = float('-inf')
                for i in range(grid.N):
                    for j in range(grid.N):
                        for value in range(1, grid.N + 1):
                            new_grid = grid
                            # check if the move is legal
                            if legal_moves((i, j), value, new_grid):
                                new_grid.put((i, j), value)
                                # recursively call minimax to evaluate the move
                                eval = minimax(new_grid, depth - 1, alpha, beta, False)
                                max_eval = max(max_eval, eval)
                                alpha = max(alpha, eval)
                                if beta <= alpha:
                                    break
                return max_eval
            
            # recursive case for min player
            else:
                min_eval = float('+inf')
                for i in range(grid.N):
                    for j in range(grid.N):
                        for value in range(1, grid.N + 1):
                            new_grid = grid
                            if legal_moves((i, j), value, new_grid):
                                new_grid.put((i, j), value)
                                # recursively call minimax to evaluate the move
                                eval = minimax(new_grid, depth - 1, alpha, beta, True)
                                min_eval = min(min_eval, eval)
                                beta = min(beta, eval)
                                if beta <= alpha:
                                    break
                return min_eval

        # list with all legal moves
        all_moves = [Move((i, j), value) for i in range(N) for j in range(N)
                     for value in range(1, N + 1) if legal_moves((i, j), value, game_state.board)]

        best_move = None
        alpha = float('-inf')
        beta = float('+inf')
        depth = 1

        # max possible depth 15
        while depth <= 15:
            for move in all_moves:
                # place and evaluate the move
                game_state.board.put(move.square, move.value)
                move_score = minimax(game_state.board, depth - 1, alpha, beta, False)

                # update alpha
                if move_score > alpha:
                    alpha = move_score
                    best_move = move

            self.propose_move(best_move)
            # update list of moves
            all_moves = generate_legal_moves(game_state.board)
            depth += 1
