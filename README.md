# WHILE to sed transpiler

The `whilesed.py` program converts a WHILE program (see below) to a sed program.

## Usage

```
$ python3 whilesed.py -o outfile.sed log10.while
$ chmod +x outfile.sed
$ echo '0#10000000000#0#0#0' | ./outfile.sed
11#0#0#0#1010#0
```

### Input/Output format

The state of the program must be initialised completely. It is given by binary numbers separated by hashes. The above example initialises all but the second variable to zero; the second variable is initialised to 1024 (binary `10000000000`).

The output format is the same as the input format. In the above example, the first output is 3 (binary `11`), which is the correct (rounded down) for log10(1024).

The heading of the generated program contains the names of the variables in the order they are expected in the input.

## WHILE language

The WHILE language has been described in academia, but I don’t know the original source to quote. If you know it, let me know. It is an extension of the [LOOP](https://en.wikipedia.org/wiki/LOOP_(programming_language)) language.

### Identifiers

Identifiers in this WHILE implementation match the following regular expression (since you are looking at this, I assume that you  know at least the very basics of regular expressions): `x_?([0-9]+)`. The prefix (`x_?`) is ignored. The capture group is converted to an integer. This is the actual identifier of the variable. So `x_2`, `x2`, `x00002` and `x_002` refer all to the same variable.

### Variables

You do not need to declare variables.

Undeclared variables are initialised to zero.

All variables are non-negative integers. There is no upper bound on the value.

### Statements

The following statements exist in the language:

#### Assign constant

Assigns a constant integer to a variable. Example (assigns 2 to `x3`):

```
x3 := 2
```

#### Assign variable / copy

Copy the value of one variable to another:

```
x2 := x3
```

#### Assign-and-add

Add/subtract a value from a variable and assign the result to a (possibly different) variable:

```
x1 := x2 - 3
```

Note: since the values can never be negative, negative results are clamped to 0.

#### Loop

Execute a block of statements a semi-fixed amount of times. The value of the loop variable is evaluated when the loop is *first* entered. The loop executes as many times as the value of the variable at enter time; modifying the variable during loop execution has no effect on the number of iterations.

```
loop x1
  ... more statements ...
end
```

#### While

Execute a block of statements until a variable becomes zero.

```
while x1
  ... more statements ...
end
```

Loops and whiles can be arbitrarily nested.
