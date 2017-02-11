"""This file contains all the classes you must complete for this project.

You can use the test cases in agent_test.py to help during development, and
augment the test suite with your own test cases to further test your code.

You must test your agent's strength against a set of agents with known
relative strength using tournament.py and include the results in your report.
"""
import logging
import time
import sys
import random

logging.basicConfig(level=logging.ERROR)
# logging.basicConfig(level=logging.DEBUG)


class Timeout(Exception):
	"""Subclass base exception for code clarity."""
	pass


def possible_moves(loc):
	"""
	possible moves for knight like player
	:param loc:
	:return:
	"""
	directions = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
	              (1, -2), (1, 2), (2, -1), (2, 1)]
	return [(loc[0] + x, loc[1] + y) for x, y in directions]


def longest_path(start_loc, path, empty_set, time_left, timeout=10.):
	"""
	Find the longest path traversable from the starting position using depth first search.

	:param start_loc:
	:param path:
	:param empty_set:
	:return:
	"""
	if time_left() < timeout:
		raise Timeout()

	if start_loc not in empty_set:
		return path
	empty_set.remove(start_loc)
	path.append(start_loc)
	max_path = list()
	for loc in possible_moves(start_loc):
		child_empty_grid = empty_set.copy()
		child_path = path.copy()
		next_path = longest_path(loc, child_path, child_empty_grid, time_left, timeout)
		if len(next_path) > len(max_path):
			max_path = next_path
	return max_path

def longest_path_score(game, player):
	"""
	Calculate longest path of both players and return (my longest path -
	opponent longest path). This does not guarantee a win since opponent can
	cross the path anytime.
	"""
	t0 = time.process_time()
	# find my own longest path
	my_loc = game.get_player_location(player)
	blank_set = {loc for loc in game.get_blank_spaces()}
	my_blank_set = blank_set.copy()
	my_blank_set.add(my_loc)
	my_longest_path = longest_path(my_loc, list(), my_blank_set, player.time_left, player.TIMER_THRESHOLD)

	# find opponent longest path
	opp_loc = game.get_player_location(game.get_opponent(player))
	opp_blank_set = blank_set
	opp_blank_set.add(opp_loc)
	opp_longest_path = longest_path(opp_loc, list(), opp_blank_set, player.time_left, player.TIMER_THRESHOLD)
	t1 = time.process_time()
	logging.info('longest_path_score time to calculate score:%.3fms' % ((t1 - t0) * 1000))
	return float(len(my_longest_path) - len(opp_longest_path))

def flood_fill(start_loc, empty_set, time_left, timeout=10.):
	""" Given a start location and set of empty spaces. Recursively fill all
	space reachable from location and return unreachable spaces in empty_set.

	:param start_loc:
	:param empty_grids: input and output, values are modified in place
	"""
	if time_left() < timeout:
		raise Timeout()

	if start_loc not in empty_set:
		return
	empty_set.discard(start_loc)
	for loc in possible_moves(start_loc):
		flood_fill(loc, empty_set, time_left, timeout)

def find_open_space(game, player):
	""" Find the number of reachable spaces for both players

	:param game:
	:param player:
	:return: (own_open_space, opp_open_space)
	"""
	blank_set = {loc for loc in game.get_blank_spaces()}

	player_loc = game.get_player_location(player)
	own_unreachable_spaces = blank_set.copy()
	own_unreachable_spaces.add(player_loc)
	flood_fill(player_loc, own_unreachable_spaces, player.time_left, player.TIMER_THRESHOLD)

	opp_loc = game.get_player_location(game.get_opponent(player))
	opp_unreachable_space = blank_set.copy()
	opp_unreachable_space.add(opp_loc)
	flood_fill(opp_loc, opp_unreachable_space, player.time_left, player.TIMER_THRESHOLD)
	return (blank_set - own_unreachable_spaces, blank_set - opp_unreachable_space)


def reachable_space_score(game, player):
	"""Find the number of reachable spaces for both players and subtract the lengths

	:param game:
	:param player:
	:return:
	"""
	t0 = time.process_time()
	own_open_space, opp_open_space = find_open_space(game, player)
	t1 = time.process_time()
	logging.info('reachable_space_score time to calculate score:%.3fms' % ((t1 - t0) * 1000))
	return float(len(own_open_space) - len(opp_open_space))

def custom_score(game, player):
	"""
	Parameters
	----------
	game : `isolation.Board`
		An instance of `isolation.Board` encoding the current state of the
		game (e.g., player locations and blocked cells).

	player : object
		A player instance in the current game (i.e., an object corresponding to
		one of the player objects `game.__player_1__` or `game.__player_2__`.)

	Returns
	----------
	float
		The heuristic value of the current game state to the specified player.
	"""

	# test for end game first
	utility = game.utility(player)
	if utility != 0:
		return utility
	return variable_heuristic_score(game, player)

def variable_heuristic_score(game, player):
	# choose the heuristic according to percentage of empty spaces left
	remaining_game = len(game.get_blank_spaces()) / (game.width * game.height)
	if remaining_game > 0.3:
		return random_score(game, player)
	elif remaining_game  >  0.2:
		return reachable_space_score(game, player)
	return longest_path_score(game, player)


def improved_reachable_space_score(game, player):
	remaining_game = len(game.get_blank_spaces()) / (game.width * game.height)
	if remaining_game < 2 / 3:
		return reachable_space_score(game, player)
	return improved_score(game, player)


def random_score(game, player):
	"""Random score heuristic: If not end game return random value between (0,1],
	else return game utility for player
	:param game:
	:param player:
	:return:
	"""
	import random
	return random.random()



def improved_score(game, player):
	"""The "Improved" evaluation function discussed in lecture that outputs a
	score equal to the difference in the number of moves available to the
	two players.
	"""
	own_moves = len(game.get_legal_moves(player))
	opp_moves = len(game.get_legal_moves(game.get_opponent(player)))
	return float(own_moves - opp_moves)


def imp_score_w_neg_dist(game, player):
	"""Improved score with negative euclidean distance heuristic
	If not end game return (current player move count - opponent move count - euclidean distance of players
	else return game utility for player
	"""
	import math
	own_moves = len(game.get_legal_moves(player))
	opp_moves = len(game.get_legal_moves(game.get_opponent(player)))
	player_loc = game.get_player_location(player)
	opponent_loc = game.get_player_location(game.get_opponent(player))
	# find euclidean distance between opponents
	dist = math.hypot(player_loc[0] - opponent_loc[0], player_loc[1] - opponent_loc[1])
	return float(own_moves - opp_moves - dist)


def imp_score_w_neg_legal_moves_int(game, player):
	"""Improved score with negative legal moves intersection heuristic:
	If not end game return (current player move count - opponent move count - intersection of legal moves
	else return game utility for player

	"""
	own_moves = game.get_legal_moves(player)
	opp_moves = game.get_legal_moves(game.get_opponent(player))
	intersection = list(set(own_moves) & set(opp_moves))
	logging.debug('imp_score_w_neg_legal_moves_int own:%s, opp:%s, int:%s' % (own_moves, opp_moves, intersection))
	return float(len(own_moves) - len(opp_moves) - len(intersection))


class CustomPlayer:
	"""Game-playing agent that chooses a move using your evaluation function
	and a depth-limited minimax algorithm with alpha-beta pruning. You must
	finish and test this player to make sure it properly uses minimax and
	alpha-beta to return a good move before the search time limit expires.

	Parameters
	----------
	search_depth : int (optional)
		A strictly positive integer (i.e., 1, 2, 3,...) for the number of
		layers in the game tree to explore for fixed-depth search. (i.e., a
		depth of one (1) would only explore the immediate sucessors of the
		current state.)

	score_fn : callable (optional)
		A function to use for heuristic evaluation of game states.

	iterative : boolean (optional)
		Flag indicating whether to perform fixed-depth search (False) or
		iterative deepening search (True).

	method : {'minimax', 'alphabeta'} (optional)
		The name of the search method to use in get_move().

	timeout : float (optional)
		Time remaining (in milliseconds) when search is aborted. Should be a
		positive value large enough to allow the function to return before the
		timer expires.
	"""

	def __init__(self, search_depth=3, score_fn=custom_score,
	             iterative=True, method='minimax', timeout=10.):
		self.search_depth = search_depth
		self.iterative = iterative
		self.score = score_fn
		self.method = method
		self.time_left = None
		self.TIMER_THRESHOLD = timeout
		self.total_depth = 0
		self.total_move = 0
		self.total_branch = 0
		self.total_end_of_tree = 0

	def get_move(self, game, legal_moves, time_left):

		"""Search for the best move from the available legal moves and return a
		result before the time limit expires.

		This function must perform iterative deepening if self.iterative=True,
		and it must use the search method (minimax or alphabeta) corresponding
		to the self.method value.

		**********************************************************************
		NOTE: If time_left < 0 when this function returns, the agent will
			  forfeit the game due to timeout. You must return _before_ the
			  timer reaches 0.
		**********************************************************************

		Parameters
		----------
		game : `isolation.Board`
			An instance of `isolation.Board` encoding the current state of the
			game (e.g., player locations and blocked cells).

		legal_moves : list<(int, int)>
			A list containing legal moves. Moves are encoded as tuples of pairs
			of ints defining the next (row, col) for the agent to occupy.

		time_left : callable
			A function that returns the number of milliseconds left in the
			current turn. Returning with any less than 0 ms remaining forfeits
			the game.

		Returns
		----------
		(int, int)
			Board coordinates corresponding to a legal move; may return
			(-1, -1) if there are no available legal moves.
		"""
		self.time_left = time_left
		time_given = time_left()

		# initial best move
		best_move = (-1, -1)
		if len(legal_moves) > 0:
			# if get_move timeouts moving random maximises the win rate
			best_move = legal_moves[random.randint(0,len(legal_moves)-1)]

		# keeping an eye on deepest depth visited for logging
		best_search_depth = 0
		reached_end_of_tree = False
		search_method = self.minimax if self.method == 'minimax' else self.alphabeta
		# depending on the iterative flag, we either call the search one time with the given search_depth or
		# we start with depth one and increment depth till we time out our hit the bottom of the tree
		search_range = (1, sys.maxsize) if self.iterative else (self.search_depth, self.search_depth + 1)
		try:
			for depth in range(*search_range):
				best_score, best_move = search_method(game, depth)
				best_search_depth = depth
				# check if we are at the bottom of search tree, we don't have to go any further after that
				if best_score == float("+inf") or best_score == float("-inf"):
					reached_end_of_tree = True
					logging.debug(
						'get_move(time_given=%d, time_left=%d, iterative=%r, search_depth=%d, method=%s) end game found(%f) breaking ID depth:%d' % (
							time_given, time_left(), self.iterative, self.search_depth, self.method, best_score,
							best_search_depth))
					break
		except Timeout:
			logging.debug('get_move(time_given=%d, iterative=%r, search_depth=%d, method=%s) TIMEOUT depth:%d' % (
				time_given, self.iterative, self.search_depth, self.method, best_search_depth))
		# keep these for reporting average depth, branching and end of tree
		self.total_depth += best_search_depth
		self.total_move += 1
		self.total_branch += len(legal_moves)
		if reached_end_of_tree:
			self.total_end_of_tree += 1
		return best_move

	def minimax(self, game, depth, maximizing_player=True):
		"""Implement the minimax search algorithm as described in the lectures.

		Parameters
		----------
		game : isolation.Board
			An instance of the Isolation game `Board` class representing the
			current game state

		depth : int
			Depth is an integer representing the maximum number of plies to
			search in the game tree before aborting

		maximizing_player : bool
			Flag indicating whether the current search depth corresponds to a
			maximizing layer (True) or a minimizing layer (False)

		Returns
		----------
		float
			The score for the current search branch

		tuple(int, int)
			The best move for the current branch; (-1, -1) for no legal moves
		"""
		if self.time_left() < self.TIMER_THRESHOLD:
			raise Timeout()

		legal_moves = game.get_legal_moves(player=game.active_player)
		# return if maximum depth is found or game has ended
		if depth == 0 or game.utility(self) != 0:
			return self.score(game, self), legal_moves[0] if legal_moves else (-1, -1)
		# get scores from legal moves
		move_scores = [(self.minimax(game.forecast_move(move), depth - 1, not maximizing_player), move) for move in
		               legal_moves]
		# get the best move for the agent
		((score, _), move) = max(move_scores) if maximizing_player else min(move_scores)
		return score, move

	def alphabeta(self, game, depth, alpha=float("-inf"), beta=float("inf"), maximizing_player=True):
		"""Implement minimax search with alpha-beta pruning as described in the
		lectures.

		Parameters
		----------
		game : isolation.Board
			An instance of the Isolation game `Board` class representing the
			current game state

		depth : int
			Depth is an integer representing the maximum number of plies to
			search in the game tree before aborting

		alpha : float
			Alpha limits the lower bound of search on minimizing layers

		beta : float
			Beta limits the upper bound of search on maximizing layers

		maximizing_player : bool
			Flag indicating whether the current search depth corresponds to a
			maximizing layer (True) or a minimizing layer (False)

		Returns
		----------
		float
			The score for the current search branch

		tuple(int, int)
			The best move for the current branch; (-1, -1) for no legal moves
		"""
		if self.time_left() < self.TIMER_THRESHOLD:
			raise Timeout()
		legal_moves = game.get_legal_moves(player=game.active_player)
		# return if maximum depth is found or game has ended
		if depth == 0 or game.utility(self) != 0:
			return self.score(game, self), legal_moves[0] if legal_moves else (-1, -1)
		# keep child scores
		move_scores = list()
		# iterate on legal moves, prune unnecessary branches
		for move in legal_moves:
			score, _ = self.alphabeta(game.forecast_move(move), depth - 1, alpha, beta, not maximizing_player)
			move_scores.append((score, move))
			if maximizing_player:
				alpha = max(score, alpha)
			else:
				beta = min(score, beta)
			if beta <= alpha:
				logging.debug('alphabeta pruned leaf a:%.2f, b:%.2f, depth:%d' % (alpha, beta, depth))
				break
		# return the best move for the agent
		return max(move_scores) if maximizing_player else min(move_scores)
