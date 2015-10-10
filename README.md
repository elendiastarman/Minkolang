# Minkolang
The Minkowskian (2+1)D semi-golfing language!

This language was inspired by [Befunge](http://esolangs.org/wiki/Befunge) and [><>](http://esolangs.org/wiki/Fish), both of which are stack-based 2D programming languages. It is a (2+1)D Minkowskian language, meaning that it has two dimensions of space and one dimension of time. When the program counter is not moving through space, it is moving through time (the layers of the program). The program space is toroidal in all directions, meaning that if the program counter moves outside of the program's boundary in spacetime, then it will relocate to the opposite side.

Minkolang is stack-based like many esolangs, though it only has one stack, like Befunge and unlike ><>. It *also* has an array where data can be stored, or data can be stored by altering the program's code. Yes, Minkolang too is capable of self-modification.

One significant feature that sets Minkolang apart from Befunge and ><> is that it has loops. Both for loops and while loops.

##Instructions

###Implemented

`v<>^` Changes the direction of the program counter.

###To implement

`V` Boost; enables the program counter to cross any number of spaces.
