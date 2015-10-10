# Minkolang
The Minkowskian (2+1)D semi-golfing language!

This language was inspired by [Befunge](http://esolangs.org/wiki/Befunge) and [><>](http://esolangs.org/wiki/Fish), both of which are stack-based 2D programming languages. It is a (2+1)D Minkowskian language, meaning that it has two dimensions of space and one dimension of time. When the program counter is not moving through space, it is moving through time (the layers of the program). The program space is toroidal in all directions, meaning that if the program counter moves outside of the program's boundary in spacetime, then it will relocate to the opposite side.

Minkolang is stack-based like many esolangs, though it only has one stack, like Befunge and unlike ><>. It *also* has an array where data can be stored, or data can be stored by altering the program's code. Yes, Minkolang too is capable of self-modification.

One significant feature that sets Minkolang apart from Befunge and ><> is that it has loops. Both for loops and while loops.

##Loops

All loops have their own stack, which may have any number of items from the parent stack (either the main program or a parent loop). Now, very interestingly, the loop's closing brace can be anywhere. When a closing brace is reached, the program counter is relocated to the opening brace and the direction is reset to what it was when the loop was entered.

###Types of loops:

- For loop `[]`: Pops the top of the stack (`n`) and repeats the loop's contents `n` times.
- While loop (take it all) `()`: The parent's whole stack is used to populate this loop's stack. Loops until stack is empty or top of stack is 0.
- While loop (n items) `{}`: Pops the top of the stack (`n`) and takes the top `n` elements of the parent's stack to populate this loop's stack. Loops until stack is empty or top of stack is 0.

##Instructions

###Implemented

- `v<>^` Changes the direction of the program counter.
- `<space>` Lets the program counter move through time (fall to the next layer).
- `0...9` Pushes the corresponding digit onto the stack.
- `"..."` String literal. Minkolang is smart enough to reverse this before pushing on the stack.
- `'...'` Number literal. Does the work of multiplying by 10 and adding the next digit.

###To implement

- `V` Boost; enables the program counter to cross any number of spaces.
- `/\|_` Mirrors. They act like you would expect.
- `

##Example programs

###Hello world!

<pre>"Hello world!"(O).</pre>

###Collatz sequence (one line)

<pre>ndN(d2%,7@)Nd+1*3b2:dNd1=?).</pre>

###Collatz sequence (three lines)

<pre>ndN(d2%,B
?=1dNd:2<.)
 )Nd+1*3<</pre>
