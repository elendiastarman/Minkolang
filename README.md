# Minkolang
##Current version: 0.1

- [Introduction](#introduction)
- [How To](#how-to)
- [Instructions](#instructions)
- [Control Structures](#control-structures)
- [Example Programs](#example-programs)

---

##Introduction

The Minkowskian (2+1)D semi-golfing language!

This language was inspired by [Befunge](http://esolangs.org/wiki/Befunge) and [><>](http://esolangs.org/wiki/Fish), both of which are stack-based 2D programming languages. It is a (2+1)D Minkowskian language, meaning that it has two dimensions of space and one dimension of time. When the program counter is not moving through space, it is moving through time (the layers of the program). The program space is toroidal in all directions, meaning that if the program counter moves outside of the program's boundary in spacetime, then it will relocate to the opposite side.

Minkolang is stack-based like many esolangs, which has an infinite well of `0`s, though it only has one stack, like Befunge and unlike ><>. It *also* has an array where data can be stored, or data can be stored by altering the program's code. Yes, Minkolang too is capable of self-modification.

---

##How To

Let's say that `ndN(d2%,7@)Nd+1*3b2:dNd1=?).` is stored in `collatz.mkl` (and that it and `minkolang.py` are in the same folder). Then you would run this with an input of `13` like this:

<pre>python minkolang.py collatz.mkl 13</pre>

---

##Instructions

###Implemented

- `v < > ^` Changes the direction of the program counter.
- `<space>` Lets the program counter move through time (fall to the next layer).
- `.` Terminates program.
- `0...9` Pushes the corresponding digit onto the stack.
- `"..."` String literal. Minkolang is smart enough to reverse this before pushing on the stack.
- `'...'` Number literal. Does the work of multiplying by 10 and adding the next digit.
- `+ - * : ; % ~` Add, subtract, multiply, divide (integer division), power (exponent), modulus, negation.
- `= ``` ,` Equality, greater-than (pops `b`,`a`, then pushes `a>b`), and not.
- `#` Net; stops the program counter from moving through time (it's a no-op).
- `! ? @ &` Trampolines. `! ?` jump one character (`?` jumps if the top of stack is non-zero); `@ &` pop `n` from top of stack and jump `n` characters (`&` is conditional, like `?`).
- `o O` Input/output character.
- `n N` Input/output number. (`n` dumps non-digits from the input until an integer is found. This is how [this Befunge interpreter](http://www.quirkster.com/iano/js/befunge.html) works.)
- `b B` Straight, T branches.
- `d D` Duplicate top [n] elements of stack. (`D` pops the top of stack as `n`; `n=1` for `d`.)
- `( )` While loop; takes all of parent's stack.

###To implement

- `V` Boost; enables the program counter to cross any number of spaces.
- `/\|_` Mirrors. They act like you would expect.
- `w W` Wormholes; they allow you to jump to any point in the code. `w` pops `y`,`x` off the stack and jumps to `(x,y)` whereas `W` pops `t`,`y`,`x` off the stack and jumps to `(x,y,t)`.
- `g G` Stack index/insert. `g` pops `n` and gets the stack's `n`th element and puts it on top of stack. `G` pops `n`,`x` and inserts `x` at the `n`-th position (zero-indexed).
- `a A` Array get/put. `a` pops `y`,`x` and puts `Array[y][x]` on top of stack. `A` pops `k`,`y`,`x` and writes `k` to `Array[y][x]`.
- `p P` Puts to code. `p` pops `k`,`y`,`x` and replaces `Code(x,y)` with `k`. `p` pops `k`,`t`,`y`,`x` and replaces `Code(x,y,t)` with `k`.
- `q Q` Gets from code. `q` pops `y`,`x` and puts `Code(x,y)` on top of stack. `Q` pops ``t`,`y`,`x` and puts `Code(x,y,t)` on top of stack.
- `[ ]` For loop. Pops `n` and repeats `n` times.
- `{ }` While loop; takes top `n` elements of parent's stack.
- `r R` Reverse and rotate stack. `R` pops `n` and rotates clockwise `n` times (may be negative). If the stack is `[1,2,3,4,5]`, then `2R` results in `[4,5,1,2,3]`.
- `x X` Dump. `x` pops the top of stack and throws it away. `X` pops `n` and throws away the top `n` elements of the stack.
- `$` Toggles the functionality of many functions. Complex feature, will be explained in its own section.

###Unassigned:

- `c C`
- `e E`
- `f F`
- `h H`
- `i I`
- `j J`
- `k K`
- `l L`
- `m M`
- `s S`
- `t T`
- `u U`
- `y Y`
- `z Z`

---

##Control Structures

One significant feature that sets Minkolang apart from Befunge and ><> is that it has loops. Both for loops and while loops.

###Loops

All loops have their own stack, which may have any number of elements from the parent stack (either the main program or a parent loop). Now, very interestingly, the loop's closing brace can be anywhere. When a closing brace is reached, the program counter is relocated to the opening brace and the direction is reset to what it was when the loop was entered.

- **For loop** `[]`: Pops the top of the stack (`n`) and repeats the loop's contents `n` times.
- **While loop** (take it all) `()`: The parent's whole stack is used to populate this loop's stack. Loops until stack is empty or top of stack is 0.
- **While loop** (n elements) `{}`: Pops the top of the stack (`n`) and takes the top `n` elements of the parent's stack to populate this loop's stack. Loops until stack is empty or top of stack is 0.

---

###Branches

Another interesting thing about Minkolang is its branches. There are two kinds of branches: straight branches (`b`) and T branches (`B`). Both kinds pop the top of the stack off and check to see if it's zero.

- **Straight branch** `b`: a non-zero input will continue on in the same direction whereas a zero input will reverse direction.

<pre>> 0b1

.

1b0 <

.

v

0
b
1

.

1
b
0

^</pre>

- **T branch** `B`: a non-zero input will bend to the right (clockwise) whereas a zero input will bend to the left (counter-clockwise).

<pre>  0
> B
  1

.

 v
 
1B0

.

1
B <
0

.

0B1

 ^</pre>

---

##Example Programs

###Hello world!

<pre>"Hello world!"(O).</pre>

`"Hello world!"` is pushed onto the stack in reverse order, then `(O)` repeatedly prints the top of stack until it's empty.

###Collatz sequence (one line)

<pre>ndN(d2%,7@)Nd+1*3b2:dNd1=?).</pre>

`ndN` takes the input and duplicates it so it can be output.

`(d2%,7@.......b` starts a while loop with `[n]` as the stack. It is duplicated and modded by 2. This is inverted and then seven characters are skipped with `7@`, landing it squarely on the `b`. In effect, the program counter moves right if the top of stack is odd, left if it's even.

`)Nd+1*3` multiplies the top of stack by three, then adds one, and outputs it (duplicated beforehand). The `)` closes the loop.

`2:dNd1=?).` divides the top of stack by two and outputs it. Then it is checked to see if it's equal to `1`. If so, then the conditional trampoline `?` jumps the program counter over the closing `)` and onto the `.`, where it terminates. Otherwise, it just goes back to the start of the loop.

###Collatz sequence (three lines)

<pre>ndN(d2%,B
?=1dNd:2<.)
 )Nd+1*3<</pre>

This one works very similarly to the one above. The biggest difference is that the T-branch `B` is used, which directs the program counter either up or down. The toroidal nature of the program space means that the third line is executed when the top of stack is odd.
