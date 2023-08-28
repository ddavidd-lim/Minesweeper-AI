# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		David Lim, Esin
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
# ==============================CS-199==================================

from AI import AI
from Action import Action
import decimal
import time
import copy

debugmine = 0
debugprob = 0
debugtime = 0
ddebug = 0
debug = 0
debugFrontier = 0

class MyAI( AI ):

	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
		#initialize board
		#initialize var total tiles needed to be uncovered and total mines
		#add in first uncover move into queue
		self.xDim = colDimension
		self.yDim = rowDimension
		self.totalMines = totalMines
		self.toUncover = (rowDimension * colDimension) - totalMines - 1
		self.totalMinesFound = 0
		self.timeElapsed = 0
		self.totalTime = 5 * 60
		self._startX = startX
		self._startY = startY
		self.board = [[[-2,-1,-1] for k in range(rowDimension)] for i in range(colDimension)]        # -1 = flag, -2 = covered, >=0 label
		# 1:0:0
		# *:_:0
		# [0]=covered/marked, [1]=effectivelabel, [2]=#ofcoveredneighbors
		# effective label=label-numMARKEDneighbors
		# if effectivelabel=numUNmarked, all unmarked are mines
		self.moveQ = set()
		self.lastMove = (startX, startY)
		self.V = [] # [(tuple of coords, set of neighbors)]
		self.C = [] # [(tuple of coords, set of neighbors)]
		self.solutions = []
		
		


		
	def getAction(self, number: int):
		#calculate remaining time: 5 min - elapsed time
		timeStart = time.time() #time stamp in seconds
		if debug == 1:
			print("Start Move:", self._startX, self._startY)
		if debug == 1:
			print("Last Move:", self.lastMove[0], self.lastMove[1])
		#update board w number received
		self.board[self.lastMove[0]][self.lastMove[1]][0] = number
		self.updateEffectiveLabel()
		self.updateCoveredNeighbors()
		if ddebug == 1:
			self.printBoard(self.board)

		remainingTime = self.totalTime - self.timeElapsed
		if remainingTime < 30:
			if debugtime == 1:
				print("Uh oh! Time's running out!\n")
			#If there's only 30 seconds left in game
			if not self.moveQ: #if it's empty (empty lists eval as false)
				#Go through every square and check if it's covered and not marked as a bomb, then add to move queue
				cover = self.FindAllCovered()
				for x,y in cover:
					self.moveQ.add((x,y))
				self.lastMove = self.moveQ.pop() #pop first move out
				timeEnd = time.time()
				self.timeElapsed += timeEnd - timeStart #record time elapsed
				self.toUncover -=1
				return Action(AI.Action.UNCOVER, self.lastMove[0], self.lastMove[1])
			else:
				self.lastMove = self.moveQ.pop() #pop first move out
				timeEnd = time.time()
				self.timeElapsed += timeEnd - timeStart #record time elapsed
				self.toUncover -=1
				return Action(AI.Action.UNCOVER, self.lastMove[0], self.lastMove[1])
		
		else:
			self.ValidActions(self.lastMove[0], self.lastMove[1]) #update queue of actions if valid actions are found (uncover, marking mine)
			
		
		#check if there is an action in queue
			if self.moveQ:    #if there is
				if debug == 1:
					print("Printing current move Queue...\n")
					for move in self.moveQ:
						print(move[0], move[1], "\n")
				self.lastMove = self.moveQ.pop() # update lastmove to be the coords of action in queue
            	# timestamp
				timeEnd = time.time()
				self.timeElapsed += timeEnd - timeStart # record time elapsed
				self.toUncover -= 1
				if debug == 1:
					print("Printing current move:", self.lastMove[0] + 1, self.lastMove[1] + 1)
				return Action(AI.Action.UNCOVER, self.lastMove[0], self.lastMove[1]) #execute action

			else:  #if there isn't, This means there are no valid actions left
				if debug == 1:
					print("To Uncover:", self.toUncover, "\n")

				if self.toUncover == 0:        # uncovered all mines
					return Action(AI.Action.LEAVE)
				else: #for every covered and unflagged tile
					for x in range(self.xDim):
						for y in range(self.yDim):
							if self.board[x][y][0] == -2:
								#find neighbors and comb through validmoves for every one
								neigh = self.FindAllNeighbors(x,y)
								for nX, nY in neigh:
									if self.board[nX][nY][0] >= 0: #if uncovered
										self.ValidActions(nX,nY)
					
					#after all this, check if moveQ is still empty. If it isn't, proceed as normal. If it is, need sophisticated AI
					if self.moveQ:
						self.lastMove = self.moveQ.pop() # update lastmove to be the coords of action in queue
						# timestamp
						timeEnd = time.time()
						self.timeElapsed += timeEnd - timeStart # record time elapsed
						self.toUncover -= 1
						if debug == 1:
							print("Printing current move:", self.lastMove[0] + 1, self.lastMove[1] + 1)
						return Action(AI.Action.UNCOVER, self.lastMove[0], self.lastMove[1]) #execute action
					else:
						#sophisticated ai -----------------------------------
						self.FrontierSearch()
						if debugFrontier == 1:
							for i in self.V:
								print("V:", i, ": ", self.V[i])
							for i in self.C:
								print("C:", i, ": ", self.C[i])
						if ddebug == 1:
							print("============ starting backtracking ===============")
						result = self.backtracking_search(timeStart)
						if len(self.solutions) == 0:
							if ddebug == 1:
								print("NO POSSIBLE MOVE")
							#return random move
							cover = self.FindAllCovered()
							self.lastMove = cover.pop()
							timeEnd = time.time()
							self.timeElapsed += timeEnd - timeStart # record time elapsed
							self.toUncover -= 1
							if ddebug == 1:
								print("Printing current move:", self.lastMove[0] + 1, self.lastMove[1] + 1)
							return Action(AI.Action.UNCOVER, self.lastMove[0], self.lastMove[1]) #execute action
						else:
							# print("Assignment dict: {}".format(result))
							prob = self.CalculateProbability()

							for assignment in prob.keys(): #result is false
								if prob[assignment] == 0:
									self.moveQ.add(assignment)
								if prob[assignment] == 1:
									if debugmine == 1:
										print("Mine found!", assignment)
									self.board[assignment[0]][assignment[1]][0] = -1
							if self.moveQ:
								pass
							else:
								#self.moveQ is empty add min probability 
								self.moveQ.add(min(prob, key=prob.get))
							self.lastMove = self.moveQ.pop()
							timeEnd = time.time()
							self.timeElapsed += timeEnd - timeStart # record time elapsed
							self.toUncover -= 1
							if ddebug == 1:
								print("Printing current move:", self.lastMove[0] + 1, self.lastMove[1] + 1)
							return Action(AI.Action.UNCOVER, self.lastMove[0], self.lastMove[1])


	def CalculateProbability(self):
		#runs through all solutions and tallies the total of solutions with mine for every tile
		prob = self.solutions[0].copy()
		#makes a dict of all tiles and initializes to 0
		if debugprob == 1:
			print(prob.keys())
		for key in prob.keys():
			prob[key] = 0
		for sol in self.solutions:
			for key in sol.keys():
				if debugprob == 1:
					print("Updating key", key, "with", sol[key])
				
				if (key not in prob.keys()):
					if debugprob == 1:
						print("Whoops! Key:", key, "is not in probability!")
						prob[key] = sol[key]
				
				else:
					prob[key] += sol[key] #tally up all mines
		for key in prob.keys():
			prob[key] = decimal.Decimal(prob[key]) / decimal.Decimal(len(self.solutions))
		if debugprob == 1:
			for key in prob.keys():
				print("Probabilities:", key, ":",prob[key])
		return prob



	def printBoard(self, chosen_board):
		row_dimension = len(chosen_board[0])
		col_dimension = len(chosen_board)
		# Print column headers
		print("   ", end="")
		for col in range(row_dimension):
			print(col + 1, end="              ")
		print()

		# Print horizontal line
		print("  ", end="")
		print("------------------------")

		# Print board cells
		for row in range(col_dimension - 1, -1, -1):
			print(row + 1, "|", end=" ")
			for col in range(row_dimension):
				print(chosen_board[col][row], end="  ")
			print()

		# Print horizontal line
		print("  ", end="")
		print("------------------------")

	def FindAllCovered(self):
		cover = set()
		for x in range(self.xDim):
			for y in range(self.yDim):
				if debug == 1:
					print(self.board[x][y][0],":", self.board[x][y][0])
				if self.board[x][y][0] == -2:
					cover.add((x,y))
		return cover
		
	def FindAllNeighbors(self, x, y):
		neigh = set()
		if debug == 1:
			print("x:", x, "y:", y, "\n")
		if (x-1) >= 0:
			neigh.add((x-1, y))
			if (y-1) >= 0:
				neigh.add((x-1, y-1))
				neigh.add((x, y-1))
			if (y+1) < self.yDim:
				neigh.add((x-1, y+1))
				neigh.add((x, y+1))
		if (x+1) < self.xDim:
			neigh.add((x+1, y))
			if (y-1) >= 0:
				neigh.add((x+1, y-1))
				neigh.add((x, y-1))
			if (y+1) < self.yDim:
				neigh.add((x+1, y+1))
				neigh.add((x, y+1))
		return neigh
	
	def ValidActions(self, x, y):	# checks for guaranteed valid actions from rule of thumb
		if debug == 1:
			print("Searching for Valid actions!\n")
		number = self.board[x][y][0]
		valid = self.FindAllNeighbors(x,y)
		numCovered = 0
		mines = 0
		exists = 0

		#check for all valid spaces around the coord
		if debug == 1:
			print("Valid set:\n")
			for move in valid:
				print(move[0], move[1], "\n")
		#go through all valid neighbor tiles and check which are mines and which are covered
		for nX, nY in valid:
			if self.board[nX][nY][0] == -2:
				numCovered += 1
			if self.board[nX][nY][0] == -1:
				mines += 1

		if debug == 1:
			print("numCovered:", numCovered, "\n")
			print("Mines:", mines, "\n")

		#List of valid actions
		if (number - mines) == numCovered: #if the num of unmarked tiles = number, all are mines| Label- mines = numcoveredNeighbors
			for nX, nY in valid:
				if self.board[nX][nY][0] == -2:
					if debugmine == 1:
						print("Mine found! Coords:", nX, nY, "\n")
					self.board[nX][nY][0] = -1 #mark as mine
					self.totalMinesFound += 1
		if (number - mines) == 0:	# all surrounding covered tiles are safe to choose| Label - Marked(mines) = 0
			for nX, nY in valid:
				if debug == 1:
					print("Evaluating", nX, nY, "Current board state:",self.board[nX][nY], "\n")
				if self.board[nX][nY][0] == -2:
					if debug == 1:
						print("Adding valid action:", nX, nY, "\n")
					self.moveQ.add((nX,nY)) #add to moveQ
	
	def MarkedNeighbors(self, x, y, c_board):	# returns set of marked neighbors
		neighbors = self.FindAllNeighbors(x,y)
		for neighbor in neighbors.copy():
			if c_board[neighbor[0]][neighbor[1]][0] != -1:
				neighbors.remove(neighbor)
		return neighbors
	
	def NumMarkedNeighbors(self,x,y, c_board):		# returns int number of marked neighbors
		marked_neigh = self.MarkedNeighbors(x,y, c_board)
		return len(marked_neigh)
	
	def UnMarkedNeighbors(self, x, y, c_board):	# returns set of unmarked neighbors| set of covered neighbors
		neighbors = self.FindAllNeighbors(x,y)
		for neighbor in neighbors.copy():
			if c_board[neighbor[0]][neighbor[1]][0] != -2:
				neighbors.remove(neighbor)
		return neighbors
	
	def NumUnMarkedNeighbors(self,x,y,c_board):	# returns int number of unmarked neighbors OR number of covered neighbors
		marked_neigh = self.UnMarkedNeighbors(x,y, c_board)
		return len(marked_neigh)

	def updateEffectiveLabel(self):
		for x in range(self.xDim):
			for y in range(self.yDim):
				#if covered and unmarked
				label = self.board[x][y][0]
				if label >= 0:
					self.board[x][y][1] = label - self.NumMarkedNeighbors(x,y, self.board)
	
	def updateCoveredNeighbors(self):
		for x in range(self.xDim):
			for y in range(self.yDim):
				#if covered and unmarked
				self.board[x][y][2] = self.NumUnMarkedNeighbors(x,y, self.board)
	# Rules of thumb:
	# if Effectivelabel = num_Unmarked, then all unmarked neighbors are mines: mark these mines
	# effective label = label - num_Marked
	# if effectivelabel = 0, all their neighbors must be safe
	def FrontierSearch(self):
		self.V = dict() # covered nodes and their uncovered neighbors
		self.C = dict()	# uncovered nodes and their covered neighbors
		for x in range(self.xDim):
			for y in range(self.yDim):
				#if covered and unmarked
				if self.board[x][y][0] == -2:
					neigh = self.FindAllNeighbors(x,y)	# all neighbors of all covered tiles
					for nX, nY in neigh.copy():
						# print("coord- ({}, {}) : {}".format(nX, nY, self.board[nY][nX][0]))
						if self.board[nX][nY][0] <= -1: #find all neighbors that are covered or a mine
							neigh.remove((nX,nY))     #and remove them from the neigh set
					if len(neigh) > 0: #if there is anything in neigh
						# appends (coords), {neigh}
						self.V[(x,y)] = neigh
						# self.V.append(((x,y), neigh)) #add the coords of covered tile and the uncovered tiles around it

				#if uncovered
				if self.board[x][y][0] >= 0:
					neigh = self.FindAllNeighbors(x,y)
					for nX, nY in neigh.copy():
						if self.board[nX][nY][0] >= -1: #find all neighbors that are uncovered or a mine
							neigh.remove((nX,nY))     #and remove them from the neigh set
					if neigh: #if there is anything in neigh
						self.C[(x,y)] = neigh
						# self.C.append(((x,y), neigh)) #add the coords of uncovered tile and the covered tiles around it

	def constraintCheck(self, boardCopy):
		# for each uncovered variable, if (numCovered < effectiveLabel < numMarked + numCovered) == False: return false
		for uncovered in self.C:
			printerVar = (uncovered[0] + 1, uncovered[1] + 1)
			x = uncovered[0]
			y = uncovered[1]
			# print("    constraint checking {}".format(printerVar))
			# print("	   #mines <= EL <= #mines + #unmarked:\n 	{} <= {} <= {}".format(self.NumMarkedNeighbors(x,y,boardCopy), 
			# 						 boardCopy[x][y][1], self.NumMarkedNeighbors(x,y,boardCopy) + boardCopy[x][y][2]))
			# if ((self.NumMarkedNeighbors(x,y,boardCopy) <= boardCopy[x][y][1] == False) or (boardCopy[x][y][1] <= self.NumMarkedNeighbors(x,y,boardCopy) + boardCopy[x][y][2] == False)):
			# 	return False
			if not (self.NumMarkedNeighbors(x, y, boardCopy) <= boardCopy[x][y][1] <= self.NumMarkedNeighbors(x, y, boardCopy) + boardCopy[x][y][2]):
				return False
		return True

	def ModelCheck(self, boardCopy, tile, value):
		# V = list of tuples: (tuple coords, {set of coords})
		# print("Tile {} = {}".format(tile, value))
		x = tile[0]
		y = tile[1]
		if value == 1: # is a mine
			boardCopy[x][y][0] = -1
			for adjacent in self.V[tile]:
				# print("Adjacent: {}".format(adjacent))
				boardCopy[adjacent[0]][adjacent[1]][2] -= 1	# numCoveredNeighbors - 1
		if value == 0: # is safe
			boardCopy[x][y][0] = 0
			for adjacent in self.V[tile]:
				# print("Adjacent: {}".format(adjacent))
				boardCopy[adjacent[0]][adjacent[1]][2] -= 1	# numCoveredNeighbors - 1

	def getUnassigned(self, a_dict):
		unassigned = []
		for covered in sorted(self.V.keys()):
			if covered not in a_dict:
				unassigned.append(covered)
		return unassigned

	def recursiveBacktracking(self, assignment_dict, unassigned, boardCopy, startTime):
		#time
		timeEnd = time.time()
		if (self.totalTime - (self.timeElapsed + (timeEnd - startTime)) < 30): # checking time elapsed
			if debugtime == 1:
				print("Uh oh! Time's running out!\n")
			return False
	
		# print(" --- New Call ----")
		# print("LENGTH OF ASSIGNMENT DICT IS: {}".format(len(assignment_dict)))
		# print("LENGTH OF V DICT IS: {}".format(len(self.V)))
		# print("Assignment dict: {}".format(assignment_dict))
		
		if len(assignment_dict) == len(self.V):
			return assignment_dict
		
		# sortedV = sorted(self.V.keys())
		
		for variable in unassigned:
			# print("Covered tile in self.V: {}".format(covered))
			# if covered not in assignment_dict: #selecting unassigned var
			# 	variable = covered
			# else:
			# 	continue
			for value in range(2):	# tests if assigning mine or safe works: 0 = safe, 1 = mine
				# update the board copy assuming that the tile is the mine/safe
				tempBoard = copy.deepcopy(boardCopy)

				printerVar = (variable[0] + 1, variable[1] + 1)
				# print(" !! Assigned: {} = {}".format(printerVar, value))

				self.ModelCheck(tempBoard, variable, value)

				if self.constraintCheck(tempBoard) == True:
					assignment_dict[variable] = value
					unassigned.remove(variable)
					result = self.recursiveBacktracking(assignment_dict, unassigned, tempBoard, startTime)
					if result == False:
						# print(" ~ BACKTRACK - Try new value")
						assignment_dict.pop(variable)
						unassigned.append(variable)
					if type(result) == dict:
						self.solutions.append(assignment_dict.copy())
						assignment_dict.pop(variable)
						unassigned.append(variable) #fake false so it can continue to run
				else:
					pass
					# print(" ~ Try new value")
			# if you get here, no value works, Backtrack
			return False
			
	def backtracking_search(self, startTime):
		self.solutions = []
		empty_dict = dict()
		unassigned = self.getUnassigned(empty_dict)
		return self.recursiveBacktracking(empty_dict, unassigned,  self.board, startTime)

	# python3 Main.pyc -f /home/dlim12/Minesweeper_Student/WorldGenerator/Problems -d
	# cd Minesweeper_Python
	# cd WorldGenerator
	# python3 WorldGenerator.py 1000 medium 16 16 40