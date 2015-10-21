import os
import sys
import json

debug = 0
if "idlelib" in sys.modules:
    sys.argv = ["minkolang_0.9.py", "insertionSort.mkl", "3 5 8 1 2 0 7"]
    debug = 1
    numSteps = 100

##if len(sys.argv) < 2: raise ValueError("Need at least one file name!")
##if len(sys.argv) == 2: sys.argv.append("")

##print(sys.argv)
##print(os.curdir, os.getcwd())

if len(sys.argv) > 1 and sys.argv[1][-4:] == ".mkl":
    file = open(sys.argv[1]).read()
else:
    file = None

class Program:
    global debug
    def __init__(self, code, inputStr="", debugFlag=0, outfile=sys.stdout):
        global debug
        debug = debugFlag
        
        self.code = []
        for layer in filter(bool, code.split("$$$\n")):
            self.code.append([list(s) for s in layer.rstrip("\n").split("\n")])
            
        if debug: print("Code:",self.code)
        self.codeput = {}
        
        self.inputStr = inputStr
        if debug: print("Input:",self.inputStr)

        self.position = [0,0,0] #[x,y,z]
        self.velocity = [1,0,0] #[dx,dy,dz]
        self.oldposition = self.position[:]

        self.stack = []
        self.array = [[]]
        self.loops = []

        self.strLiteral = ""
        self.strMode = 0
        
        self.numLiteral = 0
        self.numMode = 0
        
        self.fallable = 1
        self.toggleFlag = 0
        self.oldToggle = 0
        self.fallFlag = 0
        self.stuckFlag = 0
        
        self.bounds = [[0,max([ max(map(len,layer)) for layer in self.code])],
                       [0,max(map(len,self.code))],
                       [0,len(self.code)]]
        if debug: print(self.bounds)
        for layer in self.code:
            for row in layer:
                row.extend([" "]*(self.bounds[0][1]-len(row)))
                if debug: print(row)
            while len(layer) < self.bounds[1][1]:
                layer.append([" "]*self.bounds[0][1])
            
        self.currChar = ""
        self.output = ""
        if outfile == None:
            self.outfile = open(os.devnull, 'w')
        else:
            self.outfile = outfile

        self.stopNow = False
        self.isDone = False

    def run(self, steps=-1): #steps = -1 for run-until-halt
        self.stopNow = False
        
        while steps != 0 and self.stopNow == False and not self.isDone:
            steps -= 1
            self.getCurrent()
            movedir = ""
            arg2 = None
            stack = self.loops[-1][3] if self.loops else self.stack
            self.oldToggle = self.toggleFlag

            if self.currChar == '"':
                self.fallable = not self.fallable
                self.strMode = not self.strMode

                if not self.strMode:
##                    self.push(self.strLiteral)
                    stack.extend(list(map(ord,self.strLiteral[::-1])))
                    self.strLiteral = ""
            if self.currChar == "'":
                self.fallable = not self.fallable
                self.numMode = not self.numMode

                if not self.numMode:
##                    self.push(self.numLiteral)
                    stack.append(self.numLiteral)
                    self.numLiteral = 0

            if self.currChar not in "'\"":
                if not self.strMode and not self.numMode:

                    if self.currChar != " " and not self.fallable and not self.fallFlag:
                        self.fallable = 1
                    
                    if self.currChar == ".": #stop execution
                        self.oldposition = self.position
                        self.isDone = True
                        return
                    elif self.currChar == "$": #toggle functionality
                        if self.stuckFlag:
                            self.toggleFlag = 0
                            self.stuckFlag = 0
                        else:
                            self.toggleFlag = 1
                    elif self.currChar == "V":
                        if self.fallFlag:
                            self.fallable = 1
                            self.fallFlag = 0
                        else:
                            self.fallable = 0
                            self.fallFlag = self.toggleFlag
                    elif self.currChar == "#": #net
                        pass
                    
                    elif self.fallable and self.currChar == " ":
                        movedir = "fall"
                    elif self.currChar in "v<>^":
                        movedir = {"v":"down","<":"left",">":"right","^":"up"}[self.currChar]

                    elif self.currChar in "/\\_|":
                        if self.currChar == "/":
                            self.velocity = [-self.velocity[1],
                                             -self.velocity[0],
                                             self.velocity[2]]
                        elif self.currChar == "\\":
                            self.velocity = [self.velocity[1],
                                             self.velocity[0],
                                             self.velocity[2]]
                        elif self.currChar == "_":
                            self.velocity = [self.velocity[0],
                                             -self.velocity[1],
                                             self.velocity[2]]
                        elif self.currChar == "|":
                            self.velocity = [-self.velocity[0],
                                             self.velocity[1],
                                             self.velocity[2]]

                    elif self.currChar in "0123456789":
                        stack.append(int(self.currChar))

                    elif self.currChar in "+-*:;%=`": #operators and comparators
                        if self.toggleFlag and self.currChar in "+*":
                            if self.currChar == "+":
                                result = sum(stack)
                            elif self.currChar == "*":
                                result = 1
                                for s in stack: result *= s
                                
                            stack.clear()

                        else:
                            b = stack.pop() if stack else 0
                            a = stack.pop() if stack else 0
                            
                            if self.currChar == "+":
                                result = a+b
                            elif self.currChar == "-":
                                result = a-b if not self.toggleFlag else b-a
                            elif self.currChar == "*":
                                result = a*b
                            elif self.currChar == ":":
                                result = a//b if not self.toggleFlag else a/b
                            elif self.currChar == ";":
                                result = a**b if not self.toggleFlag else b**a
                            elif self.currChar == "%":
                                result = a%b if not self.toggleFlag else b%a
                            elif self.currChar == "=":
                                result = int(a==b if not self.toggleFlag else a!=b)
                            elif self.currChar == "`":
                                result = int(a>b if not self.toggleFlag else b>a)

                        stack.append(result)

                    elif self.currChar in "~,": #negation and not
                        if len(stack) < 1:
                            stack = [0]*(1-len(stack)) + stack

                        b = stack.pop()

                        if self.currChar == "~":
                            stack.append(-b if not self.toggleFlag else abs(b))
                        elif self.currChar == ",":
                            stack.append(int(not b if not self.toggleFlag else bool(b)))

                    elif self.currChar in "!?@&":
                        movedir = "jump"
                        if self.currChar == "!":
                            arg2 = 1
                        else:
                            tos = stack.pop() if stack else 0
                            if self.currChar == "?" and tos:
                                arg2 = 1
                            elif self.currChar == "@":
                                arg2 = tos
                            elif self.currChar == "&" and (stack.pop() if stack else 0):
                                arg2 = tos
                            else:
                                movedir = ""

                    elif self.currChar in "no": #input
                        if self.currChar == "n":
                            beg = 0
                            while beg < len(self.inputStr) and not self.inputStr[beg].isdecimal():
                                if debug: print(beg, self.inputStr[beg])
                                beg += 1

                            if beg >= len(self.inputStr):
                                stack.append(-1)
                                self.inputStr = ""
                            else:
                                end = beg+1
                                num = 0.0
                                
                                while end <= len(self.inputStr):
                                    try:
                                        num = float(self.inputStr[beg:end])
                                        end += 1
                                    except ValueError:
                                        break

                                if num.is_integer(): num = int(num)

                                if self.inputStr[beg-1] == "-": num *= -1

                                stack.append(num)
                                self.inputStr = self.inputStr[end-1:]
                                
                        elif self.currChar == "o":
                            if not len(self.inputStr):
                                stack.append(0)
                            else:
                                stack.append(ord(self.inputStr[0]))
                                self.inputStr = self.inputStr[1:]
                            
                    elif self.currChar in "NO": #output
                        tos = stack.pop() if stack else 0
                        
                        if self.currChar == "N":
                            print(tos, end=' ', flush=True, file=self.outfile)
                            self.output += str(tos) + ' '
                        elif self.currChar == "O":
                            try:
                                c = chr(int(tos))
                            except ValueError:
                                c = ""
                            print(c, end='', flush=True, file=self.outfile)
                            self.output += c

                    elif self.currChar in "dD": #duplication
                        if not self.toggleFlag:
                            tos = stack.pop() if stack else 0
                            
                            if self.currChar == "d":
                                stack.extend([tos]*2)
                            elif self.currChar == "D":
                                n = stack.pop() if stack else 0
                                stack.extend([n]*(tos+1))
                        else:
                            if self.currChar == "d":
                                stack.extend(stack)
                            elif self.currChar == "D":
                                n = stack.pop() if stack else 0
                                stack.extend(stack*n)

                    elif self.currChar in "bB": #branches
                        tos = stack.pop() if stack else 0
                        if self.toggleFlag: tos = not tos
                        
                        if self.currChar == "b":
                            if not tos: self.velocity = [-v for v in self.velocity]
                        if self.currChar == "B":
                            self.velocity = [self.velocity[1],self.velocity[0],self.velocity[2]]
                            if not tos: self.velocity = [-v for v in self.velocity]

                    elif self.currChar in "wW": #wormhole
                        nz = stack.pop() if stack and self.currChar == "W" else 0
                        ny = stack.pop() if stack else 0
                        nx = stack.pop() if stack else 0
                        
                        movedir = "wormhole"
                        arg2 = [[nx,ny,nz],self.velocity]

                    elif self.currChar in "gG": #stack index/insert
                        tos = stack.pop() if stack else 0

                        if self.currChar == "g" and stack:
                            stack.append(stack.pop(tos))
                        elif self.currChar == "G" and stack:
                            toput = stack.pop() if stack else 0
                            stack.insert(tos, toput)

                    elif self.currChar in "c": #stack copy/slice
                        tos = stack.pop() if stack else 0

                        if self.currChar == "c":
                            if not self.toggleFlag:
                                try:
                                    stack.append(stack[tos])
                                except IndexError:
                                    stack.append(0)
                            else:
                                tos2 = stack.pop() if stack else 0
                                stack.extend(stack[tos2:tos])
##                        elif self.currChar == "G" and stack:
##                            toput = stack.pop() if stack else 0
##                            stack.insert(tos, toput)

                    elif self.currChar in "xX": #dump
                        if self.currChar == "x":
                            stack.pop() if not self.toggleFlag else stack.pop(0)
                        if self.currChar == "X":
                            tos = stack.pop() if stack else 0
                            for i in range(min([tos,len(stack)])): stack.pop() if not self.toggleFlag else stack.pop(0)

                    elif self.currChar in "i": #loop counter
                        if self.toggleFlag: #for loop iters
                            stack.append(self.loops[-1][5] if self.loops and self.loops[-1][0] == "for" else -1)
                        else:
                            stack.append(self.loops[-1][4] if self.loops else -1)
                    elif self.currChar == "I":
                        if self.toggleFlag: #input length
                            stack.append(len(self.inputStr))
                        else: #stack length
                            stack.append(len(stack))

                    elif self.currChar == "r": #reverse stack
                        if self.toggleFlag: #swap top two
                            if len(stack) == 1:
                                stack.append(0)
                            else:
                                y = stack.pop()
                                x = stack.pop()
                                stack.append(y)
                                stack.append(x)
                        else:
                            stack.reverse()
                    elif self.currChar == "R": #rotates stack
                        tos = stack.pop() if stack else 0
                        mod = tos % len(stack)
                        
                        newstack = stack[-mod:] + stack[:-mod]
                        stack.clear()
                        stack.extend(newstack)

                    elif self.currChar == "s": #sort
                        if self.toggleFlag:
                            tos = stack.pop() if stack else 0
                            newstack = stack[-tos:]
                            for n in newstack: stack.pop()
                            newstack.sort()
                            stack.extend(newstack)
                        else:
                            stack.sort()
                    elif self.currChar == "S": #set (removes duplicates)
                        tos = stack.pop() if stack and self.toggleFlag else 0
                        newstack = stack[-tos:]
                        for n in newstack: stack.pop()

                        j = len(newstack)-1
                        seen = []
                        while j >= 0:
                            if newstack[j] not in seen: seen.append(newstack[j])
                            j -= 1

                        stack.extend(seen[::-1])

                    elif self.currChar == "m": #merge/interleave
                        if not self.toggleFlag:
                            L = len(stack)//2 + (len(stack)%2)
                        else:
                            tos = stack.pop() if stack else 0
                            L = len(stack) - tos
                            
                        former, latter = stack[:L], stack[L:]
                        stack.clear()
                        
                        newstack = []
                        while former and latter:
                            newstack.append(former.pop(0))
                            newstack.append(latter.pop(0))
                        newstack.extend(former)

                        stack.extend(newstack)

                    elif self.currChar in "pP": #code put
                        if self.currChar == "P":
                            z = stack.pop() if stack else 0
                        else:
                            z = self.position[2]
                        y = stack.pop() if stack else 0
                        x = stack.pop() if stack else 0

                        n = stack.pop() if stack else 0
                        b = self.bounds

                        if b[0][0] <= x < b[0][1] and b[1][0] <= y < b[1][1] and b[2][0] <= z < b[2][1]:
                            self.code[z][y][x] = n
                        else:
                            self.codeput[(x,y,z)] = n

                    elif self.currChar in "qQ": #code get
                        if self.currChar == "Q":
                            z = stack.pop() if stack else 0
                        else:
                            z = self.position[2]
                        y = stack.pop() if stack else 0
                        x = stack.pop() if stack else 0

                        b = self.bounds

                        if b[0][0] <= x < b[0][1] and b[1][0] <= y < b[1][1] and b[2][0] <= z < b[2][1]:
                            q = self.code[z][y][x]
                            stack.append(ord(q) if type(q) == str else q)
                        else:
                            if (x,y,z) in self.codeput:
                                q = self.codeput[(x,y,z)]
                                stack.append(ord(q) if type(q) == str else q)
                            else:
                                stack.append(0)

                    elif self.currChar in "aA": #array get/put
                        k = stack.pop() if stack and self.currChar == "A" else 0
                        y = stack.pop() if stack else 0
                        x = stack.pop() if stack else 0
                        
                        if x>=0 and y>=0:
                            
                            if self.currChar == "a":
                                if 0 <= y < len(self.array) and 0 <= x < len(self.array[0]):
                                    stack.append(self.array[y][x])
                                else:
                                    stack.append(0)
                                    
                            elif self.currChar == "A":
                                if debug: print(*self.array)
                                if 0 <= y < len(self.array) and 0 <= x < len(self.array[0]):
                                    pass
                                else:
                                    for line in self.array:
                                        line.extend([0]*(x-len(line)+1))
                                    while len(self.array) <= y:
                                        self.array.append([0]*(x+1))
                                if debug: print(*self.array)
                                        
                                self.array[y][x] = k

                    elif self.currChar == "u":
                        print(stack, file=self.outfile)
                    elif self.currChar == "U":
                        print(*self.code, file=self.outfile)
                        print(*self.loops, file=self.outfile)

                    elif self.currChar == "k": #break
                        if self.loops:
                            lastLoop = self.loops.pop()
                            parent = self.loops[-1][3] if self.loops else self.stack
                            parent.extend(lastLoop[3])
                            
                    elif self.currChar in "()": #while loop
                        if self.currChar == "(":
                            tos = stack.pop() if stack and self.toggleFlag else 0

                            newstack = stack[-tos:]
                            self.loops.append(["while",
                                               self.position,
                                               self.velocity,
                                               newstack,
                                               0])
                            
                            if self.toggleFlag:
                                for n in newstack: stack.pop()
                            else:
                                stack.clear()
                            
                        elif self.currChar == ")":
                            if self.loops[-1][0] != "while":
                                raise ValueError("Expected a while loop. Got a %s loop."%self.loops[-1][0])

                            finishLoop = 0

                            if self.toggleFlag:
                                tos = stack.pop() if stack else 0
                                if not tos: finishLoop = 1
                            else:
                                if len(self.loops[-1][3]) == 0: finishLoop = 1

                            if finishLoop:
                                lastLoop = self.loops.pop()
                                parent = self.loops[-1][3] if self.loops else self.stack
                                parent.extend(lastLoop[3])
                            else:
                                self.loops[-1][4] += 1 #increment loop counter
                                movedir = "teleport"
                                arg2 = self.loops[-1][1:3]
                                if debug: print(self.loops[-1][3])
                            
                    elif self.currChar in "[]": #for loop
                        if self.currChar == "[":
                            iters = stack.pop() if stack else 0                        
                            tos = stack.pop() if stack and self.toggleFlag else 0

                            newstack = stack[-tos:]
                            self.loops.append(["for",
                                               self.position,
                                               self.velocity,
                                               newstack,
                                               0,
                                               iters])
                            
                            if self.toggleFlag:
                                for n in newstack: stack.pop()
                            else:
                                stack.clear()
                            
                        elif self.currChar == "]":
                            if self.loops[-1][0] != "for":
                                raise ValueError("Expected a for loop. Got a %s loop."%self.loops[-1][0])

                            if self.loops[-1][4] >= self.loops[-1][5]-1:
                                lastLoop = self.loops.pop()
                                parent = self.loops[-1][3] if self.loops else self.stack
                                parent.extend(lastLoop[3])
                            else:
                                self.loops[-1][4] += 1 #increment loop counter
                                movedir = "teleport"
                                arg2 = self.loops[-1][1:3]


                    elif self.currChar in "{}": #recursion
                        if self.currChar == "{":
                            if not self.loops or self.loops[-1][0] != "recursion" or self.toggleFlag: #new function
                                parentR = None
                                num = stack.pop() if stack else 0
                            else: #child recursion
                                i = -1
                                while self.loops[i][5]: i -= 1 #get parent recursion
                                parentR = self.loops[i]
                                num = self.loops[i][6]
                                
                                movedir = "teleport"
                                arg2 = self.loops[i][1:3]

                            newstack = stack[len(stack)-num:]
                            for i in range(min([num,len(stack)])): stack.pop()
                                
                            self.loops.append(["recursion",
                                               self.position,
                                               self.velocity,
                                               newstack,
                                               0,
                                               parentR,
                                               num])
                            
                        elif self.currChar == "}":
                            if self.loops[-1][0] != "recursion":
                                raise ValueError("Expected recursion. Got a %s loop."%self.loops[-1][0])

                            lastLoop = self.loops.pop()
                            parent = self.loops[-1][3] if self.loops else self.stack
                            parent.extend(lastLoop[3])

                            if lastLoop[5]:
                                movedir = "teleport"
                                arg2 = lastLoop[1:3]

                    else:
                        pass
                else: #if in string or number mode
                    if self.strMode:
                        self.strLiteral += self.currChar
                    elif self.numMode:
                        if self.currChar == "-":
                            self.numLiteral *= -1
                        elif self.currChar.isdigit():
                            self.numLiteral = 10*self.numLiteral + int(self.currChar)

            if self.toggleFlag and self.currChar != "$" and not self.stuckFlag: self.toggleFlag = 0

            if debug: print(stack)
            self.move(movedir, arg2)

    def getCurrent(self):
        if debug: print(self.position)
        self.currChar = self.code[self.position[2]][self.position[1]][self.position[0]]
        if type(self.currChar) != str:
            try:
                self.currChar = chr(self.currChar)
            except [ValueError, TypeError]:
                self.currChar = ""
        if debug: print("Current character:",self.currChar)

    def move(self, direction="", arg2=None):
        from math import copysign
        self.oldposition = self.position[:]

##        if debug: print("Old velocity:",self.velocity)
        if direction == "fall": self.velocity = [0,0,1]
        if direction == "down": self.velocity = [0,1,0]
        if direction == "left": self.velocity = [-1,0,0]
        if direction == "right": self.velocity = [1,0,0]
        if direction == "up": self.velocity = [0,-1,0]
        if direction == "jump": self.velocity = [(arg2+1)*v for v in self.velocity]
##        if debug: print("New velocity:",self.velocity)

        if direction in ["teleport","wormhole"]:
            self.position, self.velocity = arg2

        if debug: print("Old position:",self.position)
        if direction != "wormhole":
            self.position = [a+b for a,b in zip(self.position, self.velocity)]
        if debug: print("New position:",self.position)

        
        for i in range(3):
            while self.position[i] < self.bounds[i][0]:
                self.position[i] += (self.bounds[i][1]-self.bounds[i][0])
            while self.position[i] >= self.bounds[i][1]:
                self.position[i] -= (self.bounds[i][1]-self.bounds[i][0])
        if debug: print("New position:",self.position)

        if direction == "jump":
            self.velocity = [bool(v)*int(copysign(1,v)) for v in self.velocity] #resets after a jump

    def push(self, L):
        if type(L) == list:
            self.stack.extend(L)
        elif type(L) == str:
            self.stack.extend(map(ord,L[::-1]))
        elif type(L) == int:
            self.stack.append(L)

    def getCode(self): return self.code
    def getArray(self): return self.array
    def getLoops(self): return self.loops
    def getStack(self): return self.stack
    def getModes(self): return [self.strMode,self.numMode]
    def getIsDone(self): return self.isDone
    def getOutput(self): return self.output
    def getCurrChar(self): return self.currChar
    def getPosition(self): return self.position
    def getVelocity(self): return self.velocity
    def getOldToggle(self): return self.oldToggle
    def getOldPosition(self): return self.oldposition

    def getVars(self):
        return vars(self)
    def getVarsJson(self):
        V = vars(self).copy()
        V.pop('outfile')
        return json.dumps(V)

    def stop(self): self.stopNow = True

if file:
    if debug:
        prog = Program(file, sys.argv[2], debugFlag=1)
        prog.run(numSteps)

    else:
        Program(file, sys.argv[2]).run()
        print()
