# Transpiler to sed

This repository contains two different languages which are compiled to sed.
Both of them are turing complete and support arbitrary-precision non-negative
integer arithmetics.

* The [`WHILE` language](#while)
* A [custom assembly language](#assembly)

## Input/Output format

The state of each program (no matter the input language) must be initialised
completely. It is given by binary numbers separated by hashes. Thus, an
input of `0#10000000000#0#0#0` initialises all but the second variable to zero;
the second variable is initialised to 1024 (binary `10000000000`).

The output format is the same as the input format.

The heading of the generated program contains the names of the variables in the
order they are expected in the input.

## Assembly

The `asmsed.py` program converts a custom assembly-style language to a sed
program.

### Usage

```
$ python3 asmsed.py -o logn.sed logn.ass
$ chmod +x logn.sed
$ echo '1000000000#1010' | ./logn.sed
10
```

This example program calculates the integer logartihm to an arbitrary base. In
this case, it is invoked to calculate the logarithm 512 (`1000000000`) to the
base 10 (`1010`). The output is rounded down, so it prints 2 (`10`).

### Examples

- [`logn.ass`](logn.ass) Calculate the floored integer logartihm.
- [`div.ass`](div.ass) Divide two integer numbers, returning the floored
  result.

### Machine model

The machine corresponding to the instruction set is a stack machine with
an arbitrarily high stack of non-negative integer numbers.

On the sed level, the numbers are encoded as ASCII-binary (that is, sequences
of ASCII `0` and `1`) and the stack slots are separated by hashes (`#`).

### Input/Output format

The input is the initial stack of the program as ASCII binary numbers (see
above) separated by hashes. The usage example above initialises the stack with
two elements, `1000000000` (512) and `1010` (10) on the stack, with 10 being
the topmost element.

The output format is the same as the input format. The entire stack at program
exit is printed.

### Language

#### Comments

Anything following a semicolon (`;`) in a line is treated as a comment.

#### Whitespace

Non-newline is used to separate different tokens in a single line. A newline
ends a mnemonic.

#### Mnemonics / Instruction set

##### load

```
load STACKPOS
```

Loads the value from the given STACKPOS (counting from the bottom starting at
0) and pushes it onto the stack. The element at STACKPOS is left in place.

##### store

```
store STACKPOS
```

Stores the topmost stack value into the given stack position (counting from the
bottom starting at 0) and removes the topmost value from the stack.

##### pushc

```
pushc NUMBER
```

Pushes the given constant NUMBER onto the stack.

##### dup

```
dup
```

Loads the topmost stack element and pushes it onto the stack, effectively
duplicating it.

##### pop

```
pop
```

Discard the topmost element from the stack.

##### inc

```
inc
```

Increment the topmost stack element in-place.

##### dec

```
dec
```

Decrement the topmost stack element in-place.

##### add

```
add
```

Add the two topmost stack elements, remove them from the stack and push the
result of the addition onto the stack.

##### sub

```
sub
```

Subtract the topmost element from the second-topmost element of the stack,
remove both from the stack and push the result.

If the subtraction underflows, it saturates to zero.

##### Labels

```
.LABELNAME
```

Not an instructino per-se, but a label to which a jump can be executed.

The labelname must be a valid sed label name and must not start with an
underscore.

##### jmp

```
jmp LABELNAME
```

Jump to the given label unconditionally.

##### jz

```
jz LABELNAME
```

If the topmost stack value is zero, pop it from the stack and jump to the
given label.

## WHILE

The `whilesed.py` program converts a WHILE program (see below) to a sed program.

### Usage

```
$ python3 whilesed.py -o outfile.sed log10.while
$ chmod +x outfile.sed
$ echo '0#10000000000#0#0#0' | ./outfile.sed
11#0#0#0#1010#0
```

### Input/Output format

The state of the program must be initialised completely. It is given by binary
numbers separated by hashes. The above example initialises all but the second
variable to zero; the second variable is initialised to 1024 (binary
`10000000000`).

The output format is the same as the input format. In the above example, the
first output is 3 (binary `11`), which is the correct (rounded down) for
log10(1024).

The heading of the generated program contains the names of the variables in
the order they are expected in the input.

### WHILE language

The WHILE language has been described in academia, but I don’t know the original source to quote. If you know it, let me know. It is an extension of the [LOOP](https://en.wikipedia.org/wiki/LOOP_(programming_language)) language.

#### Identifiers

Identifiers in this WHILE implementation match the following regular expression (since you are looking at this, I assume that you  know at least the very basics of regular expressions): `x_?([0-9]+)`. The prefix (`x_?`) is ignored. The capture group is converted to an integer. This is the actual identifier of the variable. So `x_2`, `x2`, `x00002` and `x_002` refer all to the same variable.

#### Variables

You do not need to declare variables.

Undeclared variables are initialised to zero.

All variables are non-negative integers. There is no upper bound on the value.

#### Statements

The following statements exist in the language:

##### Assign constant

Assigns a constant integer to a variable. Example (assigns 2 to `x3`):

```
x3 := 2
```

##### Assign variable / copy

Copy the value of one variable to another:

```
x2 := x3
```

##### Assign-and-add

Add/subtract a value from a variable and assign the result to a (possibly different) variable:

```
x1 := x2 - 3
```

Note: since the values can never be negative, negative results are clamped to 0.

##### Loop

Execute a block of statements a semi-fixed amount of times. The value of the loop variable is evaluated when the loop is *first* entered. The loop executes as many times as the value of the variable at enter time; modifying the variable during loop execution has no effect on the number of iterations.

```
loop x1
  ... more statements ...
end
```

##### While

Execute a block of statements until a variable becomes zero.

```
while x1
  ... more statements ...
end
```

##### If

Execute a block of statements once if a variable is non-zero.

```
if x1
   ... more statements ...
end
```

Control structures can be arbitrarily nested.
