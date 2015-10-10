import sys
import os

if __name__ == "__main__": sys.argv = ["minkolang_0.1.py", "helloworld.mkl"]

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

    def run(self, steps=1): #steps = -1 for run-until-halt
        while steps > 0:
            steps -= 1
            self.getCurrent()
            movedir = ""

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
                    if self.fallable and self.currChar == " ":
                        movedir = "fall"
                    elif self.currChar in "v<>^":
                        movedir = {"v":"down","<":"left",">":"right","^":"up"}[self.currChar]
                    elif self.currChar in "NO":
                        if self.currChar == "N":
                            print(self.stack.pop())
                        elif self.currChar == "O":
                            print(chr(self.stack.pop()))
                    elif self.currChar == ".": #stop execution
                        return
                    else:
                        pass
                else:
    ##                if debug: print(self.strMode,self.numMode)
                    if self.strMode:
                        self.strLiteral += self.currChar
                    elif self.numMode:
                        self.numLiteral = 10*self.numLiteral + int(self.currChar)

            self.move(movedir)

    def getCurrent(self):
        self.currChar = self.code[self.position[2]][self.position[1]][self.position[0]]
        if debug: print("Current character:",self.currChar)

    def move(self, direction="", spaces=0):
        if direction == "fall": self.velocity = [0,0,1]
        if direction == "down": self.velocity = [0,1,0]
        if direction == "left": self.velocity = [-1,0,0]
        if direction == "right": self.velocity = [1,0,0]
        if direction == "up": self.velocity = [0,-1,0]
        if direction == "jump": self.velocity = [spaces*v for v in self.velocity]
        
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
            self.stack.extend(L[::-1])
        elif type(L) == str:
            self.stack.extend(map(ord,L[::-1]))
        elif type(L) == int:
            self.stack.append(L)

prog = Program(files[0], 1)
prog.run(20)
