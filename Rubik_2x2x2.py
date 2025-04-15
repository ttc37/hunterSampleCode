#Thomas Cham
#Sample Code in Python for Hunter College Master Program
from hashlib import new
import random
import copy
import sys, getopt
import time
from timeit import default_timer as timer

def get_arg(index, default=None):
    return sys.argv[index] if len(sys.argv) > index else default

def getConfiguration():
    METHOD = { }
    METHOD.update(dict.fromkeys(["b","breadth"], "BREADTH_FIRST"))
    METHOD.update(dict.fromkeys(["d","depth"  ], "IT_DEPTH_FIRST"))
    METHOD.update(dict.fromkeys(["a","best"   ], "BEST_FIRST"))
    METHOD.update(dict.fromkeys(["i","idbacktrack"], "IT_BACKTRACK"))
    METHOD.update(dict.fromkeys(["o","other"], "OTHER"))

    method = "DEPTH_FIRST"   # default method
    MAX_DEPTH = 1            # default maximum depth
    VERBOSE = False
    commandLineErrors = False
              
    goalState = Cube()  # by default, Cube() is the goal state
    
    opts, args = getopt.getopt(sys.argv[1:],"c:m:v",["config=","method=","verbose"])
    for opt, arg in opts:
        if opt in ("-c", "--config"):
            initialState = arg
            if len(arg) < len(goalState.tiles): 
                
                NUM_STEPS = int(arg)
                initialState = goalState.shuffle(NUM_STEPS)
            else:
                initialState = Cube(arg)
            
        elif opt in ("-m", "--method"):
            
            if arg in METHOD.keys():
                method = METHOD[arg]
            else:
                MAX_DEPTH = int(arg)  
                
        elif opt in ("-v", "--verbose"):
            VERBOSE = True
            
        else:
            print("Unknown option, " + opt + " " +  str(arg) )
            commandLineErrors = True
            
    if commandLineErrors:
         sys.exit()
         
    return initialState, method, MAX_DEPTH, VERBOSE



#--------------------------------------------------------------------------------


#============================================================================
# List of possible moves
# https://ruwix.com/online-puzzle-simulators/2x2x2-pocket-cube-simulator.php
#
# Each move permutes the tiles in the current state to produce the new state
#============================================================================

RULES = {
    "U" : [ 2,  0,  3,  1,   20, 21,  6,  7,    4,  5, 10, 11, 
           12, 13, 14, 15,    8,  9, 18, 19,   16, 17, 22, 23],
    "U'": [ 1,  3,  0,  2,    8,  9,  6,  7,   16, 17, 10, 11, 
           12, 13, 14, 15,   20, 21, 18, 19,    4,  5, 22, 23],
    "R":  [ 0,  9,  2, 11,    6,  4,  7,  5,    8, 13, 10, 15, 
           12, 22, 14, 20,   16, 17, 18, 19,    3, 21,  1, 23],
    "R'": [ 0, 22,  2, 20,    5,  7,  4,  6,    8,  1, 10,  3, 
           12, 9, 14, 11,    16, 17, 18, 19,   15, 21, 13, 23],
    "F":  [ 0,  1, 19, 17,    2,  5,  3,  7,   10,  8, 11,  9, 
            6,  4, 14, 15,   16, 12, 18, 13,   20, 21, 22, 23],
    "F'": [ 0,  1,  4,  6,   13,  5, 12,  7,    9, 11,  8, 10, 
           17, 19, 14, 15,   16,  3, 18,  2,   20, 21, 22, 23],
    "D":  [ 0,  1,  2,  3,    4,  5, 10, 11,    8,  9, 18, 19, 
           14, 12, 15, 13,   16, 17, 22, 23,   20, 21,  6,  7],
    "D'": [ 0,  1,  2,  3,    4,  5, 22, 23,    8,  9,  6,  7, 
           13, 15, 12, 14,   16, 17, 10, 11,   20, 21, 18, 19],
    "L":  [23,  1, 21,  3,    4,  5,  6,  7,    0,  9,  2, 11, 
            8, 13, 10, 15,   18, 16, 19, 17,   20, 14, 22, 12],
    "L'": [ 8,  1, 10,  3,    4,  5,  6,  7,   12,  9, 14, 11, 
           23, 13, 21, 15,   17, 19, 16, 18,   20,  2, 22,  0],
    "B":  [ 5,  7,  2,  3,    4, 15,  6, 14,    8,  9, 10, 11, 
           12, 13, 16, 18,    1, 17,  0, 19,   22, 20, 23, 21],
    "B'": [18, 16,  2,  3,    4,  0,  6,  1,    8,  9, 10, 11, 
           12, 13,  7,  5,   14, 17, 15, 19,   21, 23, 20, 22]
}


'''
sticker indices:

        0  1
        2  3
16 17   8  9   4  5  20 21
18 19  10 11   6  7  22 23
       12 13
       14 15

face colors:

    0
  4 2 1 5
    3

rules:
[ U , U', R , R', F , F', D , D', L , L', B , B']
'''

#--------------------------------------------------------------------------------

class Cube:


    def __init__(self, config="WWWW RRRR GGGG YYYY OOOO BBBB"):
            
        self.tiles = config.replace(" ","")
    
        chunks = [self.tiles[i:i+4] + " " for i in range(0, len(self.tiles), 4)]
        self.config = "".join(chunks)
        
        self.depth = 0
        self.rule = ""
        self.parent = None


    def __str__(self):
        return self.config

        
    def __eq__(self,state):
        return (self.tiles == state.tiles) or (self.config == state.config)

    
    def toGrid(self):

        def part(face,portion):
            #============================================================================
            # This routine converts the string corresponding to a single face to a 
            # 2x2 grid
            #    face is in [0..5] if it exists, -1 if not
            #    portion is either TOP (=0) or BOTTOM (=1)
            # Example:
            # If state.config is "RWGG YOYG WOOO BBBY BRWW GYRR". 
            #   part(0,TOP) is GW , part(0,BOTTOM) is WR, ...
            #   part(5,TOP) is BR , part(5,BOTTOM) is BB
            #===========================================================================git=
        
            result = "   "
            if face >=0 :	
                offset = 4*face + 2*portion
                result = self.tiles[offset] + self.tiles[offset+1] + " "
            return result
            
        TOP    = 0
        BOTTOM = 1
        
        str = ""
        for row in [TOP,BOTTOM]:
            str += part(-1,row) + part(0,row) + \
                  part(-1,row) + part(-1,row) + "\n"
            
        for row in [TOP,BOTTOM]:
            str += part(4,row) + part(2,row) + \
                  part(1,row) + part(5,row) + "\n"
        
        for row in [TOP,BOTTOM]:
            str += part(-1,row) + part(3,row) + \
                  part(-1,row) + part(-1,row) + "\n"
            
        return str


    def applicableRules(self):
        return list( RULES.keys() )

    def applyRule(self, rule):
        s = copy.deepcopy(self)
        currRule = RULES.get(rule)
        currState = self.tiles
        newState = [currState[currRule[i]] for i in range(len(currRule))]

        newState.insert(20, " ")
        newState.insert(16, " ")
        newState.insert(12, " ")
        newState.insert(8, " ")
        newState.insert(4, " ")
        s.config = "".join(newState)
       
        s.tiles = s.config.replace(" ", "")

        s.depth += 1
        s.rule = rule
        s.parent = self
        return s
    
    def shuffle(self, n):
        
        newState = copy.deepcopy(self)
        currRULES = newState.applicableRules()

        for i in range(n):
            randomShuffle = random.randint(0,11)
            move = currRULES[randomShuffle]
            newState = newState.applyRule(move)

        return newState

    def goal(self):

        goalList = list(self.tiles)

        goalList.insert(20, " ")
        goalList.insert(16, " ")
        goalList.insert(12, " ")
        goalList.insert(8, " ")
        goalList.insert(4, " ")
        
        tempStr  = "".join(goalList)
        faceList = tempStr.split(" ")

        face_counter = 0
        for face in faceList:
            x = list(face)
            if len(set(x)) == 1:
                face_counter += 1
            else:
                return False

        if face_counter == 6:
            return True

failOne = 0
failTwo = 0
failThree = 0
failFour = 0
failFive = 0
backtrackCount = 0

def increment(errorNum):
    global backtrackCount
    global failOne 
    global failTwo
    global failThree
    global failFour
    global failFive
    if errorNum == 1:
        failOne += 1
    elif errorNum == 2:
        failTwo += 1
    elif errorNum == 3:
        failThree += 1
    elif errorNum == 4:
        failFour += 1
    elif errorNum == 5:
        failFive += 1
    elif errorNum == 0:
        backtrackCount += 1

def backtrack(stateList: list, MAX_DEPTH):
    increment(0)

    step = stateList[0];

    if VERBOSE:
        print("[%d] ===============================\nCurrent State: %s" %(backtrackCount, step))


    if step in stateList[1:]:
        if VERBOSE:
            print("\n")
            print("Already visited this state... BACKTRACKING")
        increment(1)
        return 'FAILED-1'
    else: 
        if VERBOSE:
            print("NEW STATE... CONTINUING")

    # deadend = False
    # Rubiks Cubes can go infinitely with no deadends
    ruleSet = step.applicableRules()

    # if deadend and not step.goal():
    #     if VERBOSE:
    #         print("reached a deadend...BACKTRACKING")
    #     increment(2)
    #     return 'FAILED-2'
    
    if step.goal():
        if VERBOSE:
            print ("GOAL REACHED!!!! Terminating....")
            print("Printing Solution Path......")
            #print ("step:", step)
        return []

    if len(stateList) > MAX_DEPTH:
        if VERBOSE:
            print("Exceeded the MAX DEPTH: ", MAX_DEPTH, "... BACKTRACKING")
        increment(3)
        return 'FAILED-3'

    # newState = copy.deepcopy(step)
    # Always has Rules
    # if ruleSet == None:
    #     if VERBOSE:
    #         print("No more eligible rules left... BACKTRACKING")
    #     increment(4)
    #     return 'FAILED-4'

    for r in ruleSet:
        if VERBOSE:
            print("Trying Rule:", r)
            print("Rule Applied...\n")
        newState = step.applyRule(r)
        newStateList = copy.deepcopy(stateList)
        newStateList.insert(0, newState)
        path = backtrack(newStateList, MAX_DEPTH)
        #print("pathhh: ", path)
        if not "FAILED" in path:
            #print("path:", path)
            path.append(r)
            return path

    if VERBOSE:
        print("Rules Failed: .... BACKTRACKING")
    increment(5)
    return "FAILED-5"

def iterative_deep(stateList: list, depthBound):
    while True:
        path = backtrack(stateList, depthBound)
        if isinstance(path, list) and len(path) != 0:
            break
        else:
            depthBound += 1
    return path
     


total_OpenNodes = 0
total_Closed = 0
def inc_NodeCount(type):
    global total_OpenNodes
    global total_Closed
    if type == "open":
        total_OpenNodes += 1
    if type == "closed":
        total_Closed += 1
        

def graphsearch(state: Cube, h):
    #Will build a search tree of problem graph, with start at its root
    openStateList = [state] #OPEN: list of all nodes that have been seen but not expanded
    closedStateList = [] #CLOSED: list of all nodes that have been seen and expanded
    while len(openStateList) != 0: 
        s = openStateList[0]   #Take first node from OPEN
        openStateList = openStateList[1:]
        closedStateList.append(s) #add it to CLOSED
        inc_NodeCount("closed")
        if s.goal():    #Will iterate until entire graph explored, or 
            if VERBOSE:
                print("GOAL REACHED!")
            break       #goal is reached
        for r in state.applicableRules():
            sPrime = s.applyRule(r)
            if VERBOSE:
                print("Current Node:\n", s.toGrid())
                print("Applying Rule: ", r)
                print("New State:\n", sPrime.toGrid())
            if sPrime not in openStateList and sPrime not in closedStateList: #If a child has not yet been seen, put it on OPEN. Its parent is s, depth is one more than its parent's depth
                sPrime.parent = s       #parent(s’) ← s
                sPrime.depth = s.depth + 1 #depth(s’) ← depth(s) + 1
                openStateList.append(sPrime)
                inc_NodeCount("open")
            elif sPrime in openStateList: 
                #Child is already on OPEN. Decide whether parent should change to s, adjust depth if so.
                if sPrime.parent.depth is None: 
                    tempDepth = 0
                else:
                    tempDepth = sPrime.parent.depth
                if s.depth < tempDepth:
                    sPrime.parent = s
                else:
                    sPrime.parent = sPrime.parent 
                sPrime.depth = sPrime.parent.depth + 1
            elif sPrime in closedStateList:
                # Child is already on CLOSED. Decide whether parent should change to s, adjust depth if so.
                # And adjust depth for all of its descendants.
                if sPrime.parent.depth is None:
                    tempDepth = 0
                else:
                    tempDepth = sPrime.parent.depth
                if s.depth < tempDepth:
                    sPrime.parent = s
                else:
                    sPrime.parent = sPrime.parent 
                sPrime.depth = sPrime.parent.depth + 1
                descendants = []
                for c in closedStateList:
                    if not c.parent is None and c.parent == sPrime:
                        descendants.append(c)
                for d in descendants:
                    d.depth = d.parent.depth + 1
        openStateList.sort(key=h, reverse=False)
    # if goal(s),
    # path is { s → parent(s) → parent(parent(s)) → ... → start }
    if s.goal():
        path = [s]
        while isinstance(s.parent, Cube):
            path.append(s.parent)
            s = s.parent
        return path
    else:
        return "Failed, unable to find solution"           



#--------------------------------------------------------------------------------
#  MAIN PROGRAM
#--------------------------------------------------------------------------------

if __name__ == '__main__':

    initialState, method, MAX_DEPTH, VERBOSE = getConfiguration()
    
    print("initialState=" + str(initialState))
            
    parameter = ""
    if method=="DEPTH_FIRST":
        parameter=", with MAX_DEPTH=" + str(MAX_DEPTH)
        
    print("method=" + method + parameter)

    if not VERBOSE:
        print("Non-", end="")
    print("Verbose mode.\n")
    
    random.seed() # use clock to randomize RNG

    if method == "DEPTH_FIRST":
       
        state = Cube(str(initialState))
        temp_List = list(state.tiles)
        temp_List.insert(20, " ")
        temp_List.insert(16, " ")
        temp_List.insert(12, " ")
        temp_List.insert(8, " ")
        temp_List.insert(4, " ")
        temp_Str  = "".join(temp_List)
        face_List = temp_Str.split(" ")

        f_counter = 0
        for face in face_List:
            x = list(face)
            if len(set(x)) == 1:
                f_counter += 1
        
        startTime = timer()
        path = graphsearch(state, h=lambda a: f_counter)
        endTime = timer()
        print("\nSolution Path: ")
        for i in range(len(path), 0 , -1):
            indexState = path[i-1]
            print("Rule: ", indexState.rule)
            print("State: ")
            print(indexState.toGrid())
        print("---- Program Statistics ----")
        print("# of nodes that were generated: ", total_OpenNodes)
        print("# of nodes that were expanded: ", total_Closed)
        print("Total Runtime: ", endTime - startTime)

    if method == "IT_DEPTH_FIRST":
        
        state = Cube(str(initialState))
        temp_List = list(state.tiles)
        temp_List.insert(20, " ")
        temp_List.insert(16, " ")
        temp_List.insert(12, " ")
        temp_List.insert(8, " ")
        temp_List.insert(4, " ")
        temp_Str  = "".join(temp_List)
        face_List = temp_Str.split(" ")

        f_counter = 0
        for face in face_List:
            x = list(face)
            if len(set(x)) == 1:
                f_counter += 1
        
        startTime = timer()
        path = graphsearch(state, h=lambda a: f_counter)
        endTime = timer()
        print("\nSolution Path: ")
        for i in range(len(path), 0 , -1):
            indexState = path[i-1]
            print("Rule: ", indexState.rule)
            print("State: ")
            print(indexState.toGrid())
        print("---- Program Statistics ----")
        print("# of nodes that were generated: ", total_OpenNodes)
        print("# of nodes that were expanded: ", total_Closed)
        print("Total Runtime: ", endTime - startTime)

    if method == "BREADTH_FIRST":
        
        state = Cube(str(initialState))
        startTime = timer()
        path = graphsearch(state, h=lambda a: 0)
        endTime = timer()
        print("\nSolution Path: ")
        for i in range(len(path), 0 , -1):
            indexState = path[i-1]
            print("Rule: ", indexState.rule)
            print("State: ")
            print(indexState.toGrid())
        print("---- Program Statistics ----")
        print("# of nodes that were generated: ", total_OpenNodes)
        print("# of nodes that were expanded: ", total_Closed)
        print("Total Runtime: ", endTime - startTime)

    if method == "BEST_FIRST":
        
        state = Cube(str(initialState))

        temp_List = list(state.tiles)
        temp_List.insert(20, " ")
        temp_List.insert(16, " ")
        temp_List.insert(12, " ")
        temp_List.insert(8, " ")
        temp_List.insert(4, " ")
        temp_Str  = "".join(temp_List)
        face_List = temp_Str.split(" ")

        f_counter = 0
        for face in face_List:
            x = list(face)
            if len(set(x)) == 1:
                f_counter += 1

        startTime = timer()
        path = graphsearch(state, h=lambda a: f_counter)
        endTime = timer()
        print("\nSolution Path: ")
        for i in range(len(path), 0 , -1):
            indexState = path[i-1]
            print("Rule: ", indexState.rule)
            print("State: ")
            print(indexState.toGrid())
        print("---- Program Statistics ----")
        print("# of nodes that were generated: ", total_OpenNodes)
        print("# of nodes that were expanded: ", total_Closed)
        print("Total Runtime: ", endTime - startTime)

    if method == "IT_BACKTRACK":
        
        backTrackState = Cube(str(initialState))
    
        startTime = timer()
        path = iterative_deep([backTrackState], 2)
        endTime = timer()
        print("\nSolution Path: ")
        for i in range(len(path), 0 , -1):
            indexState = path[i-1]
            print("Rule: ", indexState.rule)
            print("State: ")
            print(indexState.toGrid())
        print("---- Program Statistics ----")
        print("# of nodes that were generated: ", total_OpenNodes)
        print("# of nodes that were expanded: ", total_Closed)
        print("# of calls to BackTrack: ", backtrackCount)
        print("---- Number of Failures ----")
        print("# of FAILED-1 : ", failOne)
        print("# of FAILED-2 : ", failTwo)
        print("# of FAILED-3 : ", failThree)
        print("# of FAILED-4 : ", failFour)
        print("# of FAILED-5 : ", failFive)
        print("Runtime of Backtrack: ", endTime - startTime)
        print("\n")
        



