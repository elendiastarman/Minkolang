import os
import sys
import json
import math
import cmath
import random
import itertools
from copy import deepcopy

debug = 0
if "idlelib" in sys.modules:
    sys.argv = ["minkolang_0.14.py", ".", "c2"]
    debug = 1
    numSteps = 100

if len(sys.argv) > 1 and sys.argv[1][-4:] == ".mkl":
    file = open(sys.argv[1], encoding="utf-8").read()
    if '\ufeff' in file: file = file[1:]
elif len(sys.argv) > 1 and "idlelib" in sys.modules:
    file = sys.argv[1]
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
        self.codeChanged = 0
        
        self.inputStr = inputStr
        if debug: print("Input:",self.inputStr)

        self.position = [0,0,0] #[x,y,z]
        self.velocity = [1,0,0] #[dx,dy,dz]
        self.oldposition = self.position[:]

        self.stack = []
        self.array = [[]]
        self.loops = []
        self.gosub = []

        self.strLiteral = ""
        self.strMode = 0
        
        self.numLiteral = ""
        self.numMode = 0

        self.register = 0
        
        self.fallable = 1
        self.toggleFlag = 0
        self.oldToggle = 0
        self.fallFlag = 0
        self.stuckFlag = 0
        self.ignoreFlag = ""
        self.ternaryFlag = ""
        self.escapeFlag = 0
        
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
            self.outfile = None #open(os.devnull, 'w')
        else:
            self.outfile = outfile

        self.stopNow = False
        self.isDone = False
        self.errorType = ""
        self.caught = 0

    def runCatch(self, steps=-1):
        self.errorType = ""
        try:
            self.run(steps)
        except Exception as e:
            self.errorType = e.args[0]

            tempPosition = self.position
            tempVelocity = self.velocity
            tempCurrChar = self.currChar

            self.move()
            self.getCurrent()

            if self.currChar == "E":
                self.caught = 1
                self.run(self.steps)
            else:
                self.position = tempPosition
                self.velocity = tempVelocity
                self.currChar = tempCurrChar

    def run(self, steps=-1): #steps = -1 for run-until-halt
        self.stopNow = False
        self.codeChanged = 0
        self.arrayChanged = 0
        
        while steps != 0 and self.stopNow == False and not self.isDone:
            steps -= 1
            self.steps = steps
            self.getCurrent()
            movedir = ""
            arg2 = None
            stack = self.loops[-1][3] if self.loops else self.stack
            self.oldToggle = self.toggleFlag

            if self.currChar == '"' and not self.numMode:
                self.fallable = not self.fallable
                self.strMode = not self.strMode
                if not self.escapeFlag: self.escapeFlag = self.toggleFlag

                if not self.strMode:
                    if self.escapeFlag: self.strLiteral = bytes(self.strLiteral, "utf-8").decode("unicode_escape")
                    if not self.ignoreFlag: stack.extend(list(map(ord,self.strLiteral[::-1])))
                    self.strLiteral = ""
                    self.escapeFlag = 0
                    
            if self.currChar == "'" and not self.strMode:
                self.fallable = not self.fallable
                if not self.numMode:
                    self.numMode = stack.pop() if self.toggleFlag and stack else 10
                    if self.numMode == 0: self.numMode = 16
                else:
                    self.numMode = 0

                if not self.numMode:
                    result = 0
                    if debug: print(self.numLiteral)

                    try:
                        result = int(self.numLiteral)
                    except ValueError:
                        try:
                            result = float(self.numLiteral)
                        except ValueError:
                            try:
                                result = complex(self.numLiteral)
                            except ValueError:
                                pass

                    if not self.ignoreFlag: stack.append(result)
                    self.numLiteral = ""

            if self.currChar not in "'\"":
                if not self.strMode and not self.numMode and not self.ignoreFlag:

                    if self.currChar != " " and not self.fallable and not self.fallFlag:
                        self.fallable = 1
                    
                    if self.currChar == ".": #stop execution
                        if not self.toggleFlag: #'$.' is a soft halt (breakpoint)
                            self.oldposition = self.position
                            self.isDone = True
                            return
                        else:
                            self.stopNow = True
                    elif self.currChar == "$": #toggle functionality
                        if self.stuckFlag:
                            self.toggleFlag = 0
                            self.stuckFlag = 0
                        elif self.toggleFlag:
                            self.stuckFlag = 1
                        else:
                            self.toggleFlag = 1
                    elif self.currChar == "e": #throw exception
                        raise Exception("'e'")
                    elif self.currChar == "E":
                        stack.append(self.caught)
                        self.caught = 0

                    elif self.currChar == "C": #comments
                        self.ignoreFlag = " C"

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

                    elif self.currChar == "K":
                        n = 3 + self.toggleFlag
                        direc = random.randint(0,n)
                        if direc == 0: #down
                            self.velocity = [0,1,0]
                        elif direc == 1: #left
                            self.velocity = [-1,0,0]
                        elif direc == 2: #right
                            self.velocity = [1,0,0]
                        elif direc == 3: #up
                            self.velocity = [0,-1,0]
                        elif direc == 4: #forward
                            self.velocity = [0,0,1]
                        else:
                            pass

                    elif self.currChar in "0123456789" and not self.toggleFlag:
                        stack.append(int(self.currChar))
                    elif self.currChar == "l" and not self.toggleFlag:
                        stack.append(10)
                    elif self.currChar == "j" and not self.toggleFlag:
                        stack.append(1j)
                    elif self.currChar in "0123456789lj" and self.toggleFlag:
                        if self.currChar == "0":
                            stack.append(0.1)
                        elif self.currChar in "123456":
                            stack.append(int(self.currChar)+10)
                        elif self.currChar == "7":
                            stack.append(1/2)
                        elif self.currChar == "8":
                            stack.append((1+5**.5)/2) #phi
                        elif self.currChar == "9":
                            stack.append(2**.5)
                        elif self.currChar == "l":
                            stack.append(100)
                        elif self.currChar == "j":
                            stack.append(2**.5/2+2**.5*1j/2)

                    elif self.currChar == "L":
                        s = stack.pop() if stack and self.toggleFlag else 1
                        b = stack.pop() if stack else 0
                        a = stack.pop() if stack else 0
                        while a <= b:
                            stack.append(a)
                            a += s

                    elif self.currChar in "hH": #random number
                        if self.currChar == "h":
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag:
                                stack.append(random.randint(0,n))
                            else:
                                stack.append(random.random()*n)
                        elif self.currChar == "H":
                            b = stack.pop() if stack else 0
                            a = stack.pop() if stack else 0
                            if not self.toggleFlag:
                                stack.append(random.randint(a,b))
                            else:
                                stack.append(random.random()*(b-a)+a)

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
                                if not self.toggleFlag:
                                    result = a-b
                                else:
                                    stack.append(a)
                                    result = math.copysign(1,b) if b else 0
                                    if result.is_integer(): result=int(result)
                            elif self.currChar == "*":
                                result = a*b
                            elif self.currChar == ":":
                                result = a//b if not self.toggleFlag else a/b
                            elif self.currChar == ";":
                                result = a**b if not self.toggleFlag else math.log(b,a)
                            elif self.currChar == "%":
                                result = a%b if not self.toggleFlag else [a//b,a%b]
                            elif self.currChar == "=":
                                if not self.toggleFlag:
                                    result = int(a==b)
                                else:
                                    n,b = b,a
                                    a = stack.pop() if stack else 0
                                    result = int(a%n == b)
                            elif self.currChar == "`":
                                result = int(a>b if not self.toggleFlag else b>a)

                        if type(result) != list:
                            stack.append(result)
                        else:
                            stack.extend(result)

                    elif self.currChar in "~,": #negation and not
                        b = stack.pop() if stack else 0

                        if self.currChar == "~":
                            stack.append(-b if not self.toggleFlag else abs(b))
                        elif self.currChar == ",":
                            stack.append(int(not b if not self.toggleFlag else bool(b)))

                    elif self.currChar == "y":
                        a = stack.pop() if stack else 0
                        if type(a) != complex:
                            stack.append(int(a) if not self.toggleFlag else (a-int(a)))
                        else:
                            ar = a.real
                            ai = a.imag
                            ar2 = int(ar) if not self.toggleFlag else (ar-int(ar))
                            ai2 = int(ai) if not self.toggleFlag else (ai-int(ai))
                            stack.append((ar2+ai2*1j))

                    elif self.currChar == "Y":
                        a = stack.pop() if stack else 0
                        if type(a) != complex:
                            stack.append(math.floor(a) if not self.toggleFlag else math.ceil(a))
                        else:
                            ar = a.real
                            ai = a.imag
                            ar2 = math.floor(ar) if not self.toggleFlag else math.ceil(ar)
                            ai2 = math.floor(ai) if not self.toggleFlag else math.ceil(ai)
                            stack.append((ar2+ai2*1j))

                    elif self.currChar in "no": #input
                        if self.currChar == "n":
                            times = 1 if not self.toggleFlag else -1
                            found = 0

                            while times and self.inputStr:
                                found = 0
                                num = 0

                                for beg in range(0,len(self.inputStr)):
                                    for end in range(len(self.inputStr)+1,beg,-1):
                                        part = self.inputStr[beg:end]

                                        try:
                                            num = int(part)
                                        except ValueError:
                                            try:
                                                num = float(part)
                                            except ValueError:
                                                try:
                                                    num = complex(part)
                                                except ValueError:
                                                    continue
                                                else:
                                                    found = 1
                                            else:
                                                found = 1
                                        else:
                                            found = 1

                                        if found: break

                                    if found: break

                                if found:
                                    stack.append(num)
                                    self.inputStr = self.inputStr[end:]
                                else:
                                    self.inputStr = ""
                                    break

                                times -= 1

                            if not found:
                                stack.append(-1)
                                    
                        elif self.currChar == "o":
                            if not len(self.inputStr):
                                stack.append(0)
                            else:
                                if not self.toggleFlag:
                                    stack.append(ord(self.inputStr[0]))
                                    self.inputStr = self.inputStr[1:]
                                else:
                                    stack.extend(map(ord,self.inputStr))
                                    self.inputStr = ""
                            
                    elif self.currChar in "NO": #output
                        
                        if self.currChar == "N":
                            if not self.toggleFlag:
                                out = [stack.pop() if stack else 0]
                            else:
                                out = stack[::-1]; stack.clear()

                            for elem in out:
                                if self.outfile: print(elem, end=' ', flush=True, file=self.outfile)
                                self.output += str(elem) + ' '
                                
                        elif self.currChar == "O":
                            if not self.toggleFlag:
                                out = [stack.pop() if stack else 0]
                            else:
                                out = stack[::-1]; stack.clear()

                            for elem in out:
                                try:
                                    c = chr(int(elem))
                                except ValueError:
                                    c = ""
                                if self.outfile: print(c, end='', flush=True, file=self.outfile)
                                self.output += c

                    elif self.currChar in "dD": #duplication
                        if not self.toggleFlag:
                            tos = stack.pop() if stack else 0
                            
                            if self.currChar == "d":
                                stack.extend([tos]*2)
                            elif self.currChar == "D":
                                n = stack.pop() if stack else 0
                                stack.extend([n]*tos)
                        else:
                            if self.currChar == "d":
                                stack.extend(stack)
                            elif self.currChar == "D":
                                n = stack.pop() if stack else 0
                                stack.extend(stack*(n-1))

                    elif self.currChar == "z": #register
                        if self.toggleFlag:
                            self.register = stack.pop() if stack else 0
                        else:
                            stack.append(self.register)

                    elif self.currChar in "bB": #branches
                        tos = stack.pop() if stack else 0
                        if self.toggleFlag: tos = not tos
                        
                        if self.currChar == "b":
                            if not tos: self.velocity = [-v for v in self.velocity]
                        if self.currChar == "B":
                            self.velocity = [self.velocity[1],self.velocity[0],self.velocity[2]]
                            if not tos: self.velocity = [-v for v in self.velocity]

                    elif self.currChar == "w": #wormhole
                        nz = stack.pop() if stack and self.toggleFlag else self.position[2]
                        ny = stack.pop() if stack else 0
                        nx = stack.pop() if stack else 0
                        
                        movedir = "wormhole"
                        arg2 = [[nx,ny,nz],self.velocity]

                    elif self.currChar in "gG": #stack index/insert
                        if not self.toggleFlag:
                            n = stack.pop() if stack else 0
                            if self.currChar == "g" and stack:
                                stack.append(stack.pop(n))
                            elif self.currChar == "G" and stack:
                                toput = stack.pop() if stack else 0
                                stack.insert(n, toput)
                        else:
                            b = stack.pop() if stack else 0
                            a = stack.pop() if stack else 0
                            if self.currChar == "g" and stack:
                                newstack = stack[a:b]
                                for k in newstack: stack.pop(a)
                                stack.extend(newstack)
                            elif self.currChar == "G" and stack:
                                newstack = stack[b:-a]
                                for k in newstack: stack.pop(b)
                                stack.extend(newstack)

                    elif self.currChar == "c": #stack copy/slice
                        tos = stack.pop() if stack else 0

                        if not self.toggleFlag:
                            try:
                                stack.append(stack[tos])
                            except IndexError:
                                stack.append(0)
                        else:
                            tos2 = stack.pop() if stack else 0
                            stack.extend(stack[tos2:tos])

                    elif self.currChar in "xX": #dump
                        if stack:
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
                        k = stack.pop() if stack and self.toggleFlag else 2
                        newstack = []
                        m = len(stack)//abs(k)

                        if k < 0: k,m = m,-k-1
                        for i in range(m+1): newstack.extend(stack[i::m+1])

                        stack.clear()
                        stack.extend(newstack)

                    elif self.currChar == "p": #code put
                        if self.toggleFlag:
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
                            self.codeput[str((x,y,z))] = n
                            
                        self.codeChanged = 1

                    elif self.currChar == "q": #code get
                        if self.toggleFlag:
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
                            if str((x,y,z)) in self.codeput:
                                q = self.codeput[str((x,y,z))]
                                stack.append(ord(q) if type(q) == str else q)
                            else:
                                stack.append(0)

                    elif self.currChar in "aA": #array get/put
                        y = stack.pop() if stack else 0
                        x = stack.pop() if stack else 0
                        k = stack.pop() if stack and self.currChar == "A" else 0
                        
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
                                        self.array.append([0]*(max([x+1,len(self.array[0])])))
                                if debug: print(*self.array)
                                        
                                self.array[y][x] = k
                                self.arrayChanged = 1

                    elif self.currChar == "u":
                        if not self.toggleFlag:
                            print(stack, file=self.outfile)
                        else:
                            print(*self.code, file=self.outfile)
                            print(*self.loops, file=self.outfile)

                    elif self.currChar == "M": #MATH
                        tos = stack.pop() if stack else 0

                        if tos == 0:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #factorial
                                stack.append(math.factorial(n))
                            else: #gamma
                                stack.append(math.gamma(n))
                                
                        elif tos == 1:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #sqrt
                                stack.append(math.sqrt(n))
                            else: #nth root
                                r = (stack.pop() if stack else 0)**(1/n)
                                if r.is_integer(): r = int(r)
                                stack.append(r)
                                
                        elif tos == 2:
                            n = stack.pop() if stack else 0
                            P = getPrimes_parallelized()

                            if n <= 1:
                                stack.append(0)
                            else:
                                for p in P:
                                    if p**2 > n: #prime
                                        stack.append(not self.toggleFlag)
                                        break
                                    if n%p == 0: #composite
                                        stack.append(self.toggleFlag)
                                        break

                        elif tos == 3:
                            n = stack.pop() if stack else 0
                            P = getPrimes_parallelized()
                            if not self.toggleFlag: #nth prime
                                for i,p in enumerate(P):
                                    if i == n:
                                        stack.append(p)
                                        break
                            else: #nth composite
                                c = -1
                                prevPrime = 0
                                for p in P:
                                    c += (p-prevPrime-1)
                                    prevPrime = p
                                    if c >= n+1:
                                        stack.append(p-(c-n))
                                        break
                                    
                        elif tos == 4:
                            b = stack.pop() if stack else 0
                            a = stack.pop() if stack else 0
                            g = gcd(a,b)
                            if not self.toggleFlag: #gcd
                                stack.append(g)
                            else: #lcm
                                L = a*b/g
                                if L.is_integer(): L = int(L)
                                stack.append(L)
                                
                        elif tos == 5:
                            mean = sum(stack)/len(stack) if stack else 0
                            if not self.toggleFlag: #mean
                                stack.clear()
                                stack.append(mean)
                            else: #standard deviation
                                total = 0
                                for s in stack:
                                    total += (s-mean)**2
                                stack.append(math.sqrt(total)/len(stack) if stack else 0)
                                
                        elif tos == 6:
                            r = stack.pop() if stack else 0
                            n = stack.pop() if stack else 0
                            
                            num = 1
                            for i in range(n,r,-1):
                                num *= i
                            
                            if not self.toggleFlag: #binomial (nCr)
                                for j in range(1,(n-r)+1):
                                    num //= j
                            else: #nPr
                                pass

                            stack.append(num)
                            
                        elif tos == 7:
                            n = complex(stack.pop() if stack else 0)
                            if not self.toggleFlag: #pushes real, imag
                                stack.append(n.real)
                                stack.append(n.imag)
                            else: #complex conjugate
                                stack.append(n.conjugate())
                                
                        elif tos == 8:
                            if not self.toggleFlag: #2D distance
                                n = 2
                            else: #N-d distance
                                n = stack.pop() if stack else 0
                                
                            if not n:
                                stack.append(0)
                            else:
                                x = [stack.pop() if stack else 0 for i in range(2*n)]
                                stack.append(math.sqrt(sum([(x[i]-x[i+n])**2 for i in range(n)])))
                                
                        elif tos == 9:
                            n = stack.pop() if stack else 0
                            P = getPrimes_parallelized()
                            total = 0
                            
                            if not self.toggleFlag: #pi(n)
                                for p in P:
                                    if p <= n: total += 1
                                    else: break
                            else: #phi(n)
                                for i in range(1,n+1):
                                    if gcd(i,n) == 1: total += 1
                                
                            stack.append(total)
                            
                        elif tos == 10:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #log
                                try:
                                    stack.append(math.log(n))
                                except ValueError:
                                    stack.append(cmath.log(n))
                            else: #log_n
                                b = stack.pop() if stack else 0
                                try:
                                    stack.append(math.log(b,n))
                                except ValueError:
                                    stack.append(cmath.log(b,n))

                    elif self.currChar == "T": #TRIG
                        tos = stack.pop() if stack else 0

                        if tos == 0:
                            stack.append(math.pi if not self.toggleFlag else math.e)

                        elif tos == 1:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #convert to radians
                                stack.append(n*math.pi/180)
                            else: #convert to degrees
                                stack.append(n*180/math.pi)

                        elif tos == 2:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #sine
                                stack.append(math.sin(n))
                            else: #arcsine
                                stack.append(math.asin(n))

                        elif tos == 3:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #cosine
                                stack.append(math.cos(n))
                            else: #arccosine
                                stack.append(math.acos(n))

                        elif tos == 4:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #tangent
                                stack.append(math.tan(n))
                            else: #arctangent
                                stack.append(math.atan(n))

                        elif tos == 5:
                            y = stack.pop() if stack else 0
                            x = stack.pop() if stack else 0
                            
                            if not self.toggleFlag: #atan2
                                stack.append(math.atan2(y,x))
                            else: #hypotenuse
                                stack.append(math.hypot(x,y))

                        elif tos == 6:
                            ##using http://stackoverflow.com/a/7869457/1473772
                            if not self.toggleFlag: #angle diff (angles)
                                ang2 = stack.pop() if stack else 0
                                ang1 = stack.pop() if stack else 0
                                stack.append((ang2 - ang1 + 180) % 360 - 180)
                            else: #angle diff (coords)
                                y2 = stack.pop() if stack else 0
                                x2 = stack.pop() if stack else 0
                                y1 = stack.pop() if stack else 0
                                x1 = stack.pop() if stack else 0
                                ang1 = math.atan2(y1,x1)
                                ang2 = math.atan2(y2,x2)
                                stack.append((ang2 - ang1 + math.pi) % (2*math.pi) - math.pi)

                        elif tos == 7:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #hyperbolic sine
                                stack.append(math.sinh(n))
                            else: #hyperbolic arcsine
                                stack.append(math.asinh(n))

                        elif tos == 8:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #hyperbolic cosine
                                stack.append(math.cosh(n))
                            else: #hyperbolic arccosine
                                stack.append(math.acosh(n))

                        elif tos == 9:
                            n = stack.pop() if stack else 0
                            if not self.toggleFlag: #hyperbolic tangent
                                stack.append(math.tanh(n))
                            else: #hyperbolic arctangent
                                stack.append(math.atanh(n))

                        elif tos == 10:
                            if not self.toggleFlag: #?
                                pass
                            else: #?
                                pass

                    elif self.currChar == "Z": #LISTS/STRINGS
                        tos = stack.pop() if stack else 0

                        if tos == 0:
                            if not self.toggleFlag: #count single item
                                a = stack.pop() if stack else 0
                                stack.append(stack.count(a))
                            else: #count multi item
                                a = stack.pop() if stack else 0
                                needle = stack[-a:]
                                for k in needle: stack.pop()
                                count = 0
                                for i in range(len(stack)-len(needle)):
                                    if stack[i:i+len(needle)] == needle:
                                        count += 1
                                stack.append(count)

                        elif tos == 1 or tos == 2:
                            if not self.toggleFlag: #find [first] single item
                                needle = [stack[-1] if stack else 0]
                            else: #find [first] multi item
                                needle = stack[-(stack.pop() if stack else 0):]
                            for k in needle: stack.pop()

                            count = 0
                            for i in range(len(stack)-len(needle)+1):
                                if stack[i:i+len(needle)] == needle:
                                    stack.append(i)
                                    count += 1
                                    if tos == 1: break

                            if not self.toggleFlag and count == 0: stack.append(-1)
                            if tos == 2: stack.append(count)

                        elif tos == 3 or tos == 4:
                            if not self.toggleFlag: #remove [first] single item
                                needle = [stack[-1] if stack else 0]
                            else: #remove [first] multi item
                                needle = stack[-(stack.pop() if stack else 0):]
                            for k in needle: stack.pop()

                            i = 0
                            while i < len(stack)-len(needle):
                                if stack[i:i+len(needle)] == needle:
                                    for k in needle: stack.pop(i)
                                    if tos == 3: break
                                i += 1

                        elif tos == 5: #replace
                            b = stack.pop() if stack else 0
                            a = stack.pop() if stack else 0
                            B = stack[-b:]
                            A = stack[-b-a:-b]
                            for k in A+B: stack.pop()

                            newstack = []
                            i = 0
                            while i < len(stack):
                                if stack[i:i+len(A)] == A:
                                    newstack.extend(B)
                                    i += len(A)-1
                                    if self.toggleFlag: #replace only once
                                        newstack.extend(stack[i+1:])
                                        break
                                else:
                                    newstack.append(stack[i])
                                i += 1

                            stack.clear()
                            stack.extend(newstack)

                        elif tos == 6:
                            if not self.toggleFlag: #convert number to string
                                strnum = list(map(ord,str(stack.pop() if stack else 0)))
                                stack.extend(strnum[::-1])
                            else: #convert string to number
                                numstr = ''.join(map(chr,stack))[::-1]
                                try:
                                    num = int(numstr)
                                except ValueError:
                                    try:
                                        num = float(numstr)
                                    except ValueError:
                                        try:
                                            num = complex(numstr)
                                        except ValueError:
                                            num = 0
                                stack.clear()
                                stack.append(num)

                        elif tos == 7:
                            if not self.toggleFlag: #lowercase
                                for i in range(len(stack)):
                                    if 65 <= stack[i] <= 90: stack[i] += 32
                            else: #uppercase
                                for i in range(len(stack)):
                                    if 97 <= stack[i] <= 122: stack[i] -= 32

                        elif tos == 8:
                            if not self.toggleFlag: #is alphanumeric?
                                try:
                                    stack.append(''.join(map(chr,stack)).isalnum())
                                except ValueError:
                                    stack.append(0)
                            else: #switch case
                                for i in range(len(stack)):
                                    if 65 <= stack[i] <= 90: stack[i] += 32
                                    elif 97 <= stack[i] <= 122: stack[i] -= 32

                        elif tos == 9:
                            if not self.toggleFlag: #is alpha?
                                try:
                                    stack.append(''.join(map(chr,stack)).isalpha())
                                except ValueError:
                                    stack.append(0)
                            else: #is decimal?
                                try:
                                    stack.append(''.join(map(chr,stack)).isdecimal())
                                except ValueError:
                                    stack.append(0)

                        elif tos == 10:
                            if not self.toggleFlag: #alphabet
                                stack.extend((list(range(65,91))+list(range(97,123)))[::-1])
                            else: #numbers
                                stack.extend(list(range(48,58))[::-1])

                        elif tos == 1j: #min/max
                            newstack = stack[:]
                            stack.clear()
                            stack.append(min(newstack) if not self.toggleFlag else max(newstack))

                    elif self.currChar == "P": #MATRICES
                        tos = stack.pop() if stack else 0

                        if tos == 0: #matrix output
                            y = stack.pop() if stack else 0
                            x = stack.pop() if stack else 0
                            
                            array = [[(stack.pop() if stack else 0) for i in range(x)] for j in range(y)]

                            if not self.toggleFlag: #output as numbers
                                
                                for row in array:
                                    line = ' '.join(map(str,row))
                                    print(line, file=self.outfile)
                                    self.output += line + '\n'
                                    
                            else: #output as characters
                                for row in array:
                                    for col in row:
                                        char = ''
                                        try:
                                            char = chr(col)
                                        except ValueError:
                                            pass
                                        print(char, end='', file=self.outfile)
                                        self.output += char
                                    print()
                                    self.output += '\n'
                                    
                        elif tos == 1 or tos == 2: #matrix add, sub
                            yB = stack.pop() if stack else 0
                            xB = stack.pop() if stack else 0
                            arrayB = [[(stack.pop() if stack else 0) for i in range(xB)] for j in range(yB)]
                            
                            yA = stack.pop() if stack else 0
                            xA = stack.pop() if stack else 0
                            arrayA = [[(stack.pop() if stack else 0) for i in range(xA)] for j in range(yA)]

                            array3 = []

                            for j in range(max([yA,yB])):
                                row = []
                                for i in range(max([xA,xB])):
                                    try:
                                        a = arrayA[j][i]
                                    except IndexError:
                                        if self.toggleFlag:
                                            a = 0
                                        else:
                                            raise ValueError("Dimensions must match!")
                                    try:
                                        b = arrayB[j][i]
                                    except IndexError:
                                        if self.toggleFlag:
                                            b = 0
                                        else:
                                            raise ValueError("Dimensions must match!")

                                    c = a+b if tos == 1 else a-b
                                    row.append(c)

                                array3.append(row)

                            for row in array3[::-1]: stack.extend(row[::-1])
                            stack.append(len(array3[0]))
                            stack.append(len(array3))
                            
                        elif tos == 3 or tos == 4: #matrix mul, div
                            if not self.toggleFlag:
                                yB = stack.pop() if stack else 0
                                xB = stack.pop() if stack else 0
                                arrayB = [[(stack.pop() if stack else 0) for i in range(xB)] for j in range(yB)]

                                if tos == 4: arrayB = matrixInverse(arrayB)
                            else:
                                B = stack.pop() if stack else 0

                                if tos == 4: B = 1/B
                            
                            yA = stack.pop() if stack else 0
                            xA = stack.pop() if stack else 0
                            arrayA = [[(stack.pop() if stack else 0) for i in range(xA)] for j in range(yA)]

                            if not self.toggleFlag:
                                if xA != yB:
                                    raise ValueError("Dimension mismatch; cannot multiply matrices with dimensions %dx%d and %dx%d"%(yA,xA,yB,xB))
                                else:
                                    yDim = yA
                                    xDim = xB
                            else:
                                yDim = yA
                                xDim = xA

                            array3 = []

                            for j in range(yDim):
                                row = []
                                for i in range(xDim):
                                    if not self.toggleFlag:
                                        s = [arrayA[j][k] * arrayB[k][i] for k in range(yB)]
                                        row.append(sum(s))
                                    else:
                                        row.append(B * arrayA[j][i])

                                array3.append(row)

                            for row in array3[::-1]: stack.extend(row[::-1])
                            stack.append(len(array3[0]))
                            stack.append(len(array3))

                        elif tos == 5: #Transpose/rotate/flip
                            k = stack.pop()%8 if stack and self.toggleFlag else 0
                            y = stack.pop() if stack else 0
                            x = stack.pop() if stack else 0

                            array = [[(stack.pop() if stack else 0) for i in range(x)] for j in range(y)]
                            arrayT = [[array[j][i] for j in range(y)] for i in range(x)] #transpose
                            
                            if self.toggleFlag: #rotate too if desired
                                array2,x,y = (array,x,y) if k < 4 else (arrayT,y,x)
                                k %= 4
                                array3 = array2
                                
                                if k == 1:
                                    array3 = [[array2[j][i] for j in range(y)[::-1]] for i in range(x)]
                                elif k == 2:
                                    array3 = [row[::-1] for row in array2[::-1]]
                                elif k == 3:
                                    array3 = [[array2[j][i] for j in range(y)] for i in range(x)[::-1]]
                                
                            else:
                                array3 = arrayT

                            for row in array3[::-1]: stack.extend(row[::-1])
                            stack.append(len(array3[0]))
                            stack.append(len(array3))

                        elif tos == 6: #Identity/matrix fill
                            if not self.toggleFlag:
                                n = stack.pop() if stack else 0
                                array3 = [[int(i==j) for i in range(n)] for j in range(n)]
                            else:
                                y = stack.pop() if stack else 0
                                x = stack.pop() if stack else 0
                                n = stack.pop() if stack else 0
                                array3 = [[n for i in range(x)] for j in range(y)]

                            for row in array3[::-1]: stack.extend(row[::-1])
                            stack.append(len(array3[0]))
                            stack.append(len(array3))

                        elif tos == 7: #Determinant
                            y = stack.pop() if stack else 0
                            x = stack.pop() if stack else 0

                            array = [[(stack.pop() if stack else 0) for i in range(x)] for j in range(y)]

                            stack.append(determinant(array))

                        elif tos == 8: #Matrix inverse
                            y = stack.pop() if stack else 0
                            x = stack.pop() if stack else 0

                            array = [[(stack.pop() if stack else 0) for i in range(x)] for j in range(y)]
                            invA = matrixInverse(array)

                            for row in invA[::-1]: stack.extend(row[::-1])
                            stack.append(len(invA[0]))
                            stack.append(len(invA))

                        elif tos == 9: #Scalar exponentiation
                            n = stack.pop() if stack else 0
                            y = stack.pop() if stack else 0
                            x = stack.pop() if stack else 0
                            if x != y: raise ValueError("Matrix must be square, not %dx%d"%(y,x))
                            if type(n) != int: raise ValueError("Exponent must be integer, not %s"%n)
                            
                            array = [[(stack.pop() if stack else 0) for i in range(x)] for j in range(y)]
                            tempA = [[int(i==j) for i in range(x)] for j in range(y)]

                            if n < 0:
                                array = matrixInverse(array)
                                n = -n
                            B = list(map(int,bin(n)[2:]))

                            for b in B:
                                tempA = matrixMult(tempA, tempA) #square first
                                if b: tempA = matrixMult(tempA, array)

                            for row in tempA[::-1]: stack.extend(row[::-1])
                            stack.append(len(tempA[0]))
                            stack.append(len(tempA))

                        elif tos == 11: #Row/column sums
                            y = stack.pop() if stack else 0
                            x = stack.pop() if stack else 0

                            array = [[(stack.pop() if stack else 0) for i in range(x)] for j in range(y)]
                            
                            if not self.toggleFlag: #rows
                                sums = [sum(row) for row in array]
                            else: #columns
                                sums = [sum([array[j][i] for j in range(y)]) for i in range(x)]

                            stack.extend(sums[::-1])
                            stack.append(len(sums))

                        elif tos == 12: #Submatrix slice
                            q = stack.pop() if stack else 0
                            p = stack.pop() if stack else 0
                            
                            y = stack.pop() if stack else 0
                            x = stack.pop() if stack else 0                            
                            array = [[(stack.pop() if stack else 0) for i in range(x)] for j in range(y)]
                            
                            if not self.toggleFlag: #rows
                                array2 = array[p:q+1]
                            else: #columns
                                array2 = [row[p:q+1] for row in array]
                            
                            for row in array2[::-1]: stack.extend(row[::-1])
                            stack.append(len(array2[0]))
                            stack.append(len(array2))

                        elif tos == 13: #Row/col deletion
                            n = stack.pop() if stack else 0
                            
                            y = stack.pop() if stack else 0
                            x = stack.pop() if stack else 0                            
                            array = [[(stack.pop() if stack else 0) for i in range(x)] for j in range(y)]
                            
                            if not self.toggleFlag: #row
                                array2 = array[:n]+array[n+1:]
                            else: #column
                                array2 = [row[:n]+row[n+1:] for row in array]
                            
                            for row in array2[::-1]: stack.extend(row[::-1])
                            stack.append(len(array2[0]))
                            stack.append(len(array2))
                            
                        elif tos == 14: #Matrix spiral
                            if not self.toggleFlag: #spiral unwind
                                pass
                            else: #spiral wind
                                pass

                        else:
                            pass

                    elif self.currChar == "Q": #ITERTOOLS/MISCELLANEOUS
                        tos = stack.pop() if stack else 0

                        if tos == 0 or tos == 1: #Cartesian product, [one/multi] iterable
                            n = stack.pop() if stack and self.toggleFlag else 0
                            r = stack.pop() if stack else 1 #repeats
                            q = stack.pop() if stack and tos == 1 else 1
                            ministacks = []

                            for i in range(q):
                                k = stack.pop() if stack else 0 #length of stack to pop
                                ministacks.append(stack[-k:])
                                for x in ministacks[-1]: stack.pop()
                                
                            prods = itertools.product(*ministacks, repeat=r)
                            
                            if not self.toggleFlag: #all products
                                prods = list(prods)
                                for prod in prods[::-1]:
                                    stack.extend(prod[::-1])
                                    stack.append(len(prod))
                                stack.append(len(prods))
                            else: #nth product
                                for x in range(n): prod = next(prods)
                                stack.extend(prod[::-1])
                                stack.append(len(prod))

                        elif tos == 2: #Permutations
                            n = stack.pop() if stack and self.toggleFlag else 0
                            k = stack.pop() if stack else 0
                            newstack = stack[-k:]
                            for x in newstack: stack.pop()
                            
                            if not self.toggleFlag: #all permutations
                                perms = list(itertools.permutations(newstack))
                                for perm in perms[::-1]:
                                    stack.extend(perm[::-1])
                                    stack.append(len(perm))
                                stack.append(len(perms))
                            else: #nth permutation
                                perm = itertools.permutations(newstack,n)
                                stack.extend(perm[::-1])
                                stack.append(len(perm))

                        elif tos == 3 or tos == 4: #Combinations without/with replacement
                            n = stack.pop() if stack and self.toggleFlag else 0
                            r = stack.pop() if stack else 0
                            k = stack.pop() if stack else 0
                            newstack = stack[-k:]
                            for x in newstack: stack.pop()

                            if tos == 3:
                                comb_func = itertools.combinations
                            elif tos == 4:
                                comb_func = itertools.combinations_with_replacement

                            combs = comb_func(newstack,r)
                            
                            if not self.toggleFlag: #all combinations
                                combs = list(combs)
                                for comb in combs[::-1]:
                                    stack.extend(comb[::-1])
                                    stack.append(len(comb))
                                stack.append(len(combs))
                            else: #nth combination
                                for i in range(n): comb = next(combs)
                                stack.extend(comb[::-1])
                                stack.append(len(comb))

                    elif self.currChar == "J": #BINARY
                        tos = stack.pop() if stack else 0
                        
                        if tos < 6: #and,or,xor,nand,nor,xnor
                            b = stack.pop() if stack else 0
                            a = stack.pop() if stack else 0
                            if tos == 0: result = a&b
                            elif tos == 1: result = a|b
                            elif tos == 2: result = a^b
                            elif tos == 3: result = ~(a&b)
                            elif tos == 4: result = ~(a|b)
                            elif tos == 5: result = ~(a^b)
                        elif tos == 6: result = ~(stack.pop() if stack else 0) #complement
                        elif tos == 7: #if/not if
                            b = stack.pop() if stack else 0
                            a = stack.pop() if stack else 0
                            result = (b if a else 1) if not self.toggleFlag else (b if not a else 1)
                        elif tos == 8 or tos == 9: #bitshift left/right
                            b = stack.pop() if stack and self.toggleFlag else 1
                            a = stack.pop() if stack else 0
                            result = (a << b) if tos == 8 else (a >> b)
                        
                        stack.append(result)

                    elif self.currChar == "k": #break
                        if self.loops:
                            lastLoop = self.loops.pop()
                            parent = self.loops[-1][3] if self.loops else self.stack
                            if not self.toggleFlag: parent.extend(lastLoop[3])

                    elif self.currChar in "fF": #gosub
                        if self.currChar == "f":
                            movedir = "teleport"
                            arg2 = self.gosub.pop()
                        elif self.currChar == "F":
                            movedir = "teleport"
                            arg2 = [self.position,self.velocity]
                            self.gosub.append(arg2[:])
                            jz = stack.pop() if stack and self.toggleFlag else self.position[2]
                            jy = stack.pop() if stack else 0
                            jx = stack.pop() if stack else 0
                            arg2[0] = [jx,jy,jz]
                            for j in range(3): arg2[0][j] -= arg2[1][j]

                    elif self.currChar == "t": #ternary
##                        if debug: print("ternaryFlag: %s" % self.ternaryFlag)
                        if not self.ternaryFlag:
                            if (stack.pop() if stack else 0) == 0:
                                self.ternaryFlag = "t0"
                            else:
                                self.ignoreFlag = " t1"
                                self.ternaryFlag = "t1"
                        else:
                            if self.ternaryFlag == "t1":
                                self.ternaryFlag = "t2"
                            elif self.ternaryFlag == "t2":
                                self.ternaryFlag = ""
                            elif self.ternaryFlag == "t0":
                                self.ternaryFlag = ""
                                self.ignoreFlag = " t0"
                        if debug: print(" ternaryFlag: %s" % self.ternaryFlag)
                            
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

                            finishLoop = not stack.pop() if stack else 1

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

                            if iters > 0:
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
                            else:
                                self.ignoreFlag = " ]"
                            
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
                else: #if in string or number mode or ignoreFlag is set
                    if self.strMode:
                        self.strLiteral += self.currChar
                    elif self.numMode:
                        self.numLiteral += self.currChar

                    if self.ignoreFlag:
                        if debug: print("ignoreFlag: %s" % self.ignoreFlag)
                        if self.ignoreFlag[0] == " ":
                            self.ignoreFlag = self.ignoreFlag[1:]
                        elif self.currChar == self.ignoreFlag[0] and not self.strMode and not self.numMode:
                            if self.ignoreFlag == "t0":
                                self.ternaryFlag = ""
                            elif self.ignoreFlag == "t1":
                                self.ternaryFlag = "t1"
                            self.ignoreFlag = ""

            if self.toggleFlag and self.currChar != "$" and not self.stuckFlag: self.toggleFlag = 0

            if debug: print(stack)
            self.move(movedir, arg2)

    def getCurrent(self):
        if debug: print(self.position)
        self.currChar = self.code[self.position[2]][self.position[1]][self.position[0]]
        if type(self.currChar) != str:
            try:
                self.currChar = chr(self.currChar)
            except (ValueError, TypeError):
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

##        if debug: print("Old position:",self.position)
        if direction != "wormhole":
            self.position = [a+b for a,b in zip(self.position, self.velocity)]
##        if debug: print("New position:",self.position)

        
        for i in range(3):
            while self.position[i] < self.bounds[i][0]:
                self.position[i] += (self.bounds[i][1]-self.bounds[i][0])
            while self.position[i] >= self.bounds[i][1]:
                self.position[i] -= (self.bounds[i][1]-self.bounds[i][0])
##        if debug: print("New position:",self.position)

        if direction == "jump":
            self.velocity = [bool(v)*int(copysign(1,v)) for v in self.velocity] #resets after a jump

    def getCode(self): return self.code
    def getModes(self): return [self.strMode,self.numMode]
    def getOldToggle(self): return self.oldToggle

    def getVars(self):
        return vars(self)
    def getVarsJson(self):
        V = vars(self).copy()
        V.pop('outfile')

        #make complex numbers serializable by stringifying them
        V['stack'] = V['stack'][:]
        for i,v in enumerate(V['stack']):
            if type(v) == complex: V['stack'][i] = str(v)

        V['loops'] = deepcopy(V['loops'])
        for L in V['loops']:
            for i,v in enumerate(L[3]):
                if type(v) == complex: L[3][i] = str(v)
                
        return json.dumps(V)

    def stop(self): self.stopNow = True

def getPrimes_parallelized(): #uses sieve of Sundaram
        yield 2
        yield 3
        P = [[4,1]]
        i = 2
        while 1:
            if P[0][0] <= i:
                while P[0][0] <= i:
                    P[0][0] += 2*P[0][1]+1
                    P.sort()
            elif P[0][0] > i:
                yield 2*i+1
                P.append([2*(i+i*i), i])
                P.sort()
            i += 1

def gcd(a,b):
    while 1:
        a,b = b,a%b
        if b == 0: return a

def determinant(A):
    if len(A) == 0: raise ValueError("Matrix must be non-empty")
    if len(A) != len(A[0]): raise ValueError("Matrix must be square (it is %dx%d)" % (len(A),len(A[0])))

    if len(A) == 1: return A[0][0]
    
    det = 0
    for i in range(len(A[0])):
        A2 = []
        for j in range(1,len(A)):
            A2.append(A[j][:i]+A[j][i+1:])
        det += ((i%2)*2-1)*A[0][i]*determinant(A2)
    return det

def matrixInverse(A): #uses a very inefficient recursive algorithm
    if len(A) == 0: raise ValueError("Matrix must be non-empty")
    if len(A) != len(A[0]): raise ValueError("Matrix must be square (it is %dx%d)" % (len(A),len(A[0])))

    if len(A) == 1: return A[0][0]
    
    C = [[0]*len(A) for x in range(len(A))]
    det = determinant(A)
    
    for j in range(len(A)):
        for i in range(len(A[0])):
            A2 = []
            for row in A[:j]+A[j+1:]:
                A2.append(row[:i]+row[i+1:])
            C[i][j] = ((i+j)%2*2-1)*determinant(A2)/det

    return C

def matrixMult(A,B):
    if len(A)+len(B) == 0: raise ValueError("Matrices must be non-empty")
    if len(A) != len(A[0]): raise ValueError("Matrix A must be square (it is %dx%d)" % (len(A),len(A[0])))
    if len(B) != len(B[0]): raise ValueError("Matrix B must be square (it is %dx%d)" % (len(B),len(B[0])))

    Ax = len(A[0])
    Ay = len(A)
    Bx = len(B[0])
    By = len(B)

    if Ax != By: raise ValueError("Dimension mismatch; cannot multiply matrices with dimensions %dx%d and %dx%d"%(Ay,Ax,By,Bx))

    temp = []
    for j in range(Ay):
        row = []
        for i in range(Bx):
            s = [A[j][k]*B[k][i] for k in range(Ax)]
            row.append(sum(s))
        temp.append(row)
        
    return temp

if file:
    if debug:
        prog = Program(file, sys.argv[2] if len(sys.argv) > 2 else "", debugFlag=1)
        prog.run(numSteps)

    else:
        Program(file, sys.argv[2] if len(sys.argv) > 2 else "").run()
        print()
