# Minkolang
##Current version: 0.9

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

Let's say that `ndN(d2%,7@)Nd+1*3b2:dNd1=?).` is stored in `collatz.mkl` (and that it and `minkolang_0.8.py` are in the same folder). Then you would run this with an input of `13` like this:

<pre>python minkolang_0.8.py collatz.mkl 13</pre>

---

##Instructions

###Implemented

**Movement**
- `<space>` Lets the program counter move through time (fall to the next layer).
- `#` Net; stops the program counter from moving through time (it's a no-op).
- `v < > ^` Changes the direction of the program counter.
- `/\|_` Mirrors. They act like you would expect.
- `! ? @ &` Trampolines. `! ?` jump one character (`?` jumps if the top of stack is non-zero); `@ &` pop `n` from top of stack and jump `n` characters (`&` is conditional, like `?`).
- `V` Boost; enables the program counter to cross any number of spaces.
 - `$` enables the boost permanently until it encounters another `V`.
- `w W` Wormholes; they allow you to jump to any point in the code. `w` pops `y`,`x` off the stack and jumps to `(x,y)` whereas `W` pops `t`,`y`,`x` off the stack and jumps to `(x,y,t)`.

**Control structures**
- `.` Terminates program.
- `b B` Straight, T branches.
 - `$` reverses the branch endpoints (swaps where truthy and falsy go).
- `( )` While loop; takes all of parent's stack and repeats until the stack is empty.
 - `$(` pops `n` and puts the top `n` elements of the parent stack into the loop's stack. `$)` pops `n` and repeats if `n` is not zero.
- `[ ]` For loop. Pops `n` and repeats body `n` times.
 - `$` Pops `x` and puts the top `x` elements of parent stack into the loop's stack.
- `{ }` [Recursion.](#recursion)
 - `$` Starts a new recursion.
- `k` Breaks out of the current loop. (That is, its stack is pushed onto the parent stack.)

**Literals**
- `0...9` Pushes the corresponding digit onto the stack.
- `"..."` String literal. Minkolang is smart enough to reverse this before pushing on the stack.
- `'...'` Number literal. Does the work of multiplying by 10 and adding the next digit.

**Math and comparisons**
- `+ - * : ; % ~` Add, subtract (`a-b`), multiply, integer division (`a//b`), exponentiation (`a**b`), modulus (`a%b`), negation. `b` is popped first, then `a` so doing `53-` (for example) intuitively gives `2`, as expected.
 - `$` changes these into sum, reverse subtract (`b-a`), product, float division (`a/b`), reverse exponentiation (`b**a`), reverse modulus (`b%a`), and absolute value.
- `= <backtick> ,` Equality, greater-than (pops `b`,`a`, then pushes `a>b`, so `53<backtick>` will push 1, as expected), and not.
 - `$` changes these into not-equal, `b>a`, and boolean (like Python's `bool()`).

**Input and output**
- `o O` Input/output character.
- `n N` Input/output number. (`n` dumps non-digits from the input until an integer is found. This is how [this Befunge interpreter](http://www.quirkster.com/iano/js/befunge.html) works.)

**Stack manipulation**
- `d D` Duplicates top element of stack. `D` pops `n` and duplicates the top of stack `n` times.
 - `$` does the same except on the whole stack. So executing `$d` on `[1,2,3]` will give `[1,2,3,1,2,3]`.
- `g G` Stack index/insert. `g` pops `n` and gets the stack's `n`th element and puts it on top of stack. `G` pops `n`,`x` and inserts `x` at the `n`-th position (zero-indexed).
- `c` Stack item copy. Pops `n` and pushes `stack[n]` onto the stack without removing it.
 - `$` Stack slice. Pops `k` in addition and pushes `stack[k:n]` onto the stack. So `36$c` on `[0,1,2,3,4,5,6,7,8,9]` will result in `[0,1,2,3,4,5,6,7,8,9,3,4,5]`.
- `i` Gets loop's counter (0-based) and pushes it onto the stack.
 - `$` pushes the loop's maximum number of iterations if the current loop is a For loop.
- `I` Pushes the stack's length onto the stack.
 - `$` pushes the input string's length onto the stack.
- `r` Reverses stack.
 - `$` swaps the top two values of the stack.
- `R` Rotates stack. Pops `n` and rotates clockwise `n` times (may be negative). If the stack is `[1,2,3,4,5]`, then `2R` results in `[4,5,1,2,3]`.
- `s` Sorts the stack.
 - `$` pops `n` and sorts the top `n` elements of the stack.
- `S` Removes duplicates. So `"Hello world!"S(O).` will give you `Hel wrd!`.
 - `$` pops `n` and removes duplicates from the top `n` elements of the stack.
- `x X` Dump. `x` pops the top of stack and throws it away. `X` pops `n` and throws away the top `n` elements of the stack.
 - `$` dumps from the front of the stack.
- `m` Merge. Splits a list in half (if length is odd, the first half is longer) and interleaves the halves. `m` on `[1,2,3,4,5,6,7]` would result in `[1,5,2,6,3,7,4]`.
 - `$` pops `n` and merges the top `n` elements of the stack at the front of stack. As in, `3$m` on `[1,2,3,4,5,6,7,8,9]` would result in `[1,7,2,8,3,9,4,5,6]`.

**Memory and reflection (self-modification)**
- `p P` Puts to code. `p` pops `y`,`x`,`k` and replaces `Code(x,y)` with `k`. `p` pops `t`,`y`,`x`,`k` and replaces `Code(x,y,t)` with `k`.
- `q Q` Gets from code. `q` pops `y`,`x` and puts `Code(x,y)` on top of stack. `Q` pops ``t`,`y`,`x` and puts `Code(x,y,t)` on top of stack.
- `a A` Array get/put. `a` pops `y`,`x` and puts `Array[y][x]` on top of stack. `A` pops `k`,`y`,`x` and writes `k` to `Array[y][x]`.

**Special**
- `$` Toggles the functionality of many functions. This "toggle flag" only remains active for one step.
 - `$` (that is, `$$`) turns on the toggle flag permanently until another `$` is encountered.
- `$$$` Separates layers of a program. See the [layered Hello world! example](#layered-hello-world).
- `u U` Debug (print) the current stack (`u`) and the code and loops (`U`).

###To implement

- `K` Park. Pops `n` and repeats the next instruction `n` times.
- Register where you can store and retrieve one value
- Random integer
- Random direction
- Escape-able characters in strings (so `"\n"` would be a newline)
- Specify a base for a number literal
- `M` Map
- `F` Fold (reduce)

###Unassigned:

- `C`
- `e E`
- `f`
- `h H`
- `j J`
- `k K`
- `l L`
- `t T`
- `y Y`
- `z Z`

---

##Control Structures

One significant feature that sets Minkolang apart from Befunge and ><> is that it has loops. Both for loops and while loops.

###Loops

All loops have their own stack, which may have any number of elements from the parent stack (either the main program or a parent loop). Now, very interestingly, the loop's closing brace can be anywhere. When a closing brace is reached, the program counter is relocated to the opening brace and the direction is reset to what it was when the loop was entered.

- **For loop** `[]`: Pops the top of the stack (`n`) and repeats the loop's contents `n` times.
- **While loop** (take it all) `()`: The parent's whole stack is used to populate this loop's stack, **unless** `$` is used right beforehand, in which case, pops the top of the stack (`n`) and takes the top `n` elements of the parent's stack to populate this loop's stack. Loops until stack is empty or top of stack is 0.

###Branches

Another interesting thing about Minkolang is its branches. There are two kinds of branches: straight branches (`b`) and T branches (`B`). Both kinds pop the top of the stack off and check to see if it's zero.

- **Straight branch** `b`: a non-zero input will continue on in the same direction whereas a zero input will reverse direction.

<pre>       v
       0         1
> 0b1  b  1b0 <  b
       1         0
                 ^</pre>

- **T branch** `B`: a non-zero input will bend to the right (clockwise) whereas a zero input will bend to the left (counter-clockwise).

<pre>  0   v   1
> B  1B0  B <  0B1
  1       0     ^</pre>

###Recursion

As far as I know, this is absolutely the only 2D language to have recursion. In Minkolang, `{}` are the control characters. On the first use of `{` (or if `$` was used right before), a recursive function is initialized. This means popping `n` off the top of the stack, which sets the number of arguments to take. The top `n` elements of the parent stack are popped off and used to populate the recursion's stack. This applies to child instances too, which are started when the program counter encounters another `{`. Returning is done by using `}`, which simply plops the instance's stack on top of the parent (often, another recursion instance) stack.

To put it another way, there are three steps to doing recursion in Minkolang:

1. Initialize. For example, if the program counter encounters `3{` and the stack is `[1,2,3,4,5]`, then the recursion's stack will be `[3,4,5]`, and any further children will also take the top three elements of their parent's stack.
2. Recurse. This is done by using `{` again. The program counter jumps to the very first `{` that started the whole recurrence.
3. Return. This is done by using `}`. The program counter jumps to the last `{` that was countered and moves from there.

This is certainly a bit complicated, but try working through the [Fibonacci example](#fibonacci-sequence-recursion) below. Hopefully that'll help.

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

###Fibonacci sequence (recursion)

This (horribly inefficient) way of calculating the Fibonacci sequence uses its recursive definition: F(n) = F(n-1) + F(n-2) where F(0) = 0 and F(1) = 1.

<pre>n1{d1`,9&d1-{r2-{+}N.</pre>

`n` takes an integer in input, then the recursive function is initialized with `1{`. The `1` here specifies that the function takes one argument.

`d1```,9&` looks to see if the top of stack is <= 1. If it is, then it jumps to the closing `}`, which effectively "returns" from the function. This is the base case - where the input is 0 or 1, so F(0 or 1) is the same.

If the top of stack is *not* 0 or 1, then the trampoline is not taken. Hence, `d1-{` is executed, which duplicates the top of stack, subtracts 1, and runs the function on it. This is the F(n-1) part.

Once that returns, `r2-{` is executed. This reverses the stack so input is now in front. Then two is subtracted and the function is run again with it as input. This is the F(n-2) part.

Once *that* returns, then finally, the two values are added together and returned with `+}`. This is the F(n-1) + F(n-2) part.

At the ultimate conclusion (i.e., when F(n) has been calculated), `N.` outputs F(n) as an integer and exits.

###Layered "Hello world!"

<pre>!v"Hello world!"!

$$$

$$$

V<        .)O(</pre>

This demonstrates how the layers of a program can be separated. The interpreter automatically fills in lines and spaces as needed to make a complete rectangular prism for the code space. The execution is as follows: the first `!` jumps over the `v`, "Hello world!" is pushed onto the stack, then another `!` skips the first one, so the program counter is redirected downward. It lands on a space, so it moves through time (falls) until it hits the `<`. The `V` boosts it across the space to the output loop `.)O(` (normally written as `(O).`).
