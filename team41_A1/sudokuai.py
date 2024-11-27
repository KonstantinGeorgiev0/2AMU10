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
    def __init__(self):
        super().__init__()

    def compute_best_move(self, game_state: GameState) -> None:
        N = game_state.board.N
        
        def legal_moves(square, value, board):
            square = tuple(square)
            cell_is_empty = game_state.board.get(square) == SudokuBoard.empty
            move_not_taboo = TabooMove(square, value) not in game_state.taboo_moves
            if not cell_is_empty or not move_not_taboo:
                return False
            grid_coords = [square[0] // board.m, square[1] // board.n]
            row_values = [board.get((square[0], c)) for c in range(board.N)]
            col_values = [board.get((r, square[1])) for r in range(board.N)]
            # check player 
            if game_state.current_player == 1:
                # We start at the top-left corner
                block_values = [
                    board.get((r, board.n * grid_coords[1] + c))
                    for r in range(board.m)
                    for c in range(board.n)
                ]
            else:
                # We start at the bottom corner
                block_values = [
                    board.get((board.m * grid_coords[0] + r, c))
                    for r in range(board.m)
                    for c in range(board.n)
                ]
            # It shouldn't be in the same row, same column, or same block
            return value not in row_values and value not in col_values and value not in block_values

        def generate_legal_moves(board):
            moves = []
            for i in range(board.N):
                for j in range(board.N):
                    if board.get((i, j)) == SudokuBoard.empty:
                        for value in range(1, board.N + 1):
                            if legal_moves((i, j), value, board):
                                moves.append(Move((i, j), value))
                                
            # print("Legal moves: ", moves)
            return moves

        # scoring for number of completed regions
        regions_score = {0:0, 1:1, 2:3, 3:7}
        
        def compute_completed_regions(board, i, j):
            """Compute the number of completed regions in the board."""
            grid_coords = [i // board.m, j // board.n]
            regions = [
                    [board.get(i, c) for c in range(board.N)],
                    [board.get(r, j) for r in range(board.N)],
                    [
                        board.get(board.m * grid_coords[0] + r, board.n * grid_coords[1] + c)
                        for r in range(board.m)
                        for c in range(board.n)
                    ],
                ]
            
            # compute number of completed regions by checking if the sum of the values in region is 45
            completed_regions = sum(
                sum(cell for cell in region if cell != SudokuBoard.empty) == 45
                for region in regions
            )

            # return number of completed regions
            return completed_regions
        
        def evaluate_move(board, move):
            # determine if move is legal
            if move not in generate_legal_moves(board):
                return False
            
            # compute number of regions before move
            completed_regions = compute_completed_regions(board, move.square[0], move.square[1])
            i, j = move.square
            value = move.value
            new_board = board
            # make move on new board
            new_board.put(i, j, value)
            
            # calculate score for the move
            return regions_score[compute_completed_regions(new_board, i, j) - completed_regions]
        
        def minimax(grid, depth, alpha, beta, is_maximizing_player, move):
            if depth == 0:
                return evaluate_move(grid, move)

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
                                eval = minimax(new_grid, depth - 1, alpha, beta, False, move)
                                max_eval = max(max_eval, eval)
                                alpha = max(alpha, eval)
                                if beta <= alpha:
                                    break
                return max_eval

            else:
                min_eval = float('+inf')
                for i in range(grid.N):
                    for j in range(grid.N):
                        for value in range(1, grid.N + 1):
                            new_grid = grid
                            if legal_moves((i, j), value, new_grid):
                                new_grid.put((i, j), value)
                                # recursively call minimax to evaluate the move
                                eval = minimax(new_grid, depth - 1, alpha, beta, True, move)
                                min_eval = min(min_eval, eval)
                                beta = min(beta, eval)
                                if beta <= alpha:
                                    break 
                return min_eval

        all_moves = [Move((i, j), value) for i in range(N) for j in range(N)
                     for value in range(1, N+1) if legal_moves((i, j), value, game_state.board)]
        
        best_move = None
        alpha = float('-inf')
        beta = float('+inf')
        depth = 1
        
        while depth <= 15:
            for move in all_moves:
                game_state.board.put(move.square, move.value)
                move_score = minimax(game_state.board, depth - 1, alpha, beta, is_maximizing_player=False, move=move)
                print("Move: ", move, "Score: ", move_score)
                game_state.board.put(move.square, SudokuBoard.empty) 
                
                if move_score > alpha:
                    alpha = move_score
                    best_move = move
                    # remove the move from the list of all moves
                    all_moves.remove(move)
            
            self.propose_move(best_move)
            depth += 1
        # best_move = Move((0, 0), 2)
        # depth = 1
        # while depth <= 15:
        #     alpha = float('-inf')
        #     beta = float('+inf')
        #     for i in range(N):
        #         for j in range(N):
        #             for value in range(1, N + 1):
        #                 board = game_state.board
        #                 # check if move is legal
        #                 if legal_moves((i, j), value, board):
        #                     board.put((i, j), value)
        #                     eval = minimax(board, depth - 1, alpha, beta, False, best_move)
        #                     if eval > alpha:
        #                         alpha = eval
        #                         best_move = Move((i, j), value)
        #     self.propose_move(best_move)
        #     depth += 1
        # while True:
        #     time.sleep(0.2)
        #     self.propose_move(random.choice(all_moves))

