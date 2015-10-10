import sys
import os

debug = 0
if "idlelib" in sys.modules:
    sys.argv = ["minkolang_0.1.py", "helloworld.mkl"]
    debug = 1

if len(sys.argv) < 2: raise ValueError("Need at least one file name!")

##print(sys.argv)
##print(os.curdir, os.getcwd())

files = [open(fname).read() for fname in sys.argv[1:]]

class Program:
    global debug
    def __init__(self, code, debugFlag=0):
        global debug
        debug = debugFlag
        
        self.code = [ [list(s) for s in code.split("\n")] ]
        if debug: print(self.code)

        self.position = [0,0,0] #[x,y,z]
        self.velocity = [1,0,0] #[dx,dy,dz]

        self.stack = []
        self.array = [[]]
        self.loops = []

        self.strLiteral = ""
        self.strMode = 0
        
        self.numLiteral = 0
        self.numMode = 0
        
        self.fallable = 1
        self.bounds = [[0,max(map(len,self.code[0]))],
                       [0,len(self.code)],
                       [0,0]]
        if debug: print(self.bounds)
        self.currChar = ""

    def run(self, steps=-1): #steps = -1 for run-until-halt
        while steps != 0:
            steps -= 1
            self.getCurrent()
            movedir = ""
            arg2 = None

            if self.currChar == '"':
                self.fallable = not self.fallable
                self.strMode = not self.strMode

                if not self.strMode:
                    self.push(self.strLiteral)
                    self.strLiteral = ""
            if self.currChar == "'":
                self.fallable = not self.fallable
                self.numMode = not self.numMode

                if not self.numMode:
                    self.push(self.numLiteral)
                    self.numLiteral = 0

            if self.currChar not in "'\"":
                if not self.strMode and not self.numMode:
                    if self.currChar == ".": #stop execution
                        return
                    
                    elif self.fallable and self.currChar == " ":
                        movedir = "fall"
                    elif self.currChar in "v<>^":
                        movedir = {"v":"down","<":"left",">":"right","^":"up"}[self.currChar]
                        
                    elif self.currChar in "NO":
                        if len(self.loops):
                            tos = self.loops[-1][3].pop()
                            if debug: print(tos, self.loops[-1][3])
                        else:
                            tos = self.stack.pop()
                            
                        if self.currChar == "N":
                            print(tos, end='', flush=True)
                        elif self.currChar == "O":
                            print(chr(tos), end='', flush=True)
                            
                    elif self.currChar in "()": #while loop
                        if self.currChar == "(":
                            if self.loops:
                                stack = self.loops[-1][3]
                            else:
                                stack = self.stack
                                
                            self.loops.append(["while",
                                               self.position,
                                               self.velocity,
                                               stack[:]])
                            
                            if debug: print(self.loops[-1])
                            stack = []
                            
                        elif self.currChar == ")":
                            if self.loops[-1][0] != "while":
                                raise ValueError("Expected a while loop. Got a %s loop."%self.loops[-1][0])
                            
                            if len(self.loops[-1][3]) == 0 or self.loops[-1][3] == 0:
                                self.push(self.loops[-1][3])
                                self.loops.pop()
                            else:
                                movedir = "teleport"
                                arg2 = self.loops[-1][1:3]
                                if debug: print(self.loops[-1][3])
                                
                    else:
                        pass
                else:
    ##                if debug: print(self.strMode,self.numMode)
                    if self.strMode:
                        self.strLiteral += self.currChar
                    elif self.numMode:
                        self.numLiteral = 10*self.numLiteral + int(self.currChar)

            self.move(movedir, arg2)

    def getCurrent(self):
        self.currChar = self.code[self.position[2]][self.position[1]][self.position[0]]
        if debug: print("Current character:",self.currChar)

    def move(self, direction="", arg2=None):
        if direction == "fall": self.velocity = [0,0,1]
        if direction == "down": self.velocity = [0,1,0]
        if direction == "left": self.velocity = [-1,0,0]
        if direction == "right": self.velocity = [1,0,0]
        if direction == "up": self.velocity = [0,-1,0]
        if direction == "jump": self.velocity = [arg2*v for v in self.velocity]

        if direction == "teleport":
            self.position, self.velocity = arg2
##        else:
        self.position = [a+b for a,b in zip(self.position, self.velocity)]
##        if debug: print("Old position:",self.position)
            
        for i in range(3):
            while self.position[i] < self.bounds[i][0]:
                self.position[i] += (self.bounds[i][1]-self.bounds[i][0])
            while self.position[i] > self.bounds[i][1]:
                self.position[i] -= (self.bounds[i][1]-self.bounds[i][0])
##        if debug: print("New position:",self.position)

        if direction == "jump":
            self.velocity = [math.copysign(1,v) for v in self.velocity] #resets after a jump

    def push(self, L):
        if type(L) == list:
            self.stack.extend(L)
        elif type(L) == str:
            self.stack.extend(map(ord,L[::-1]))
        elif type(L) == int:
            self.stack.append(L)

if debug:
    prog = Program(files[0], 1)
    prog.run(20)

else:
    Program(files[0]).run()
    print()
