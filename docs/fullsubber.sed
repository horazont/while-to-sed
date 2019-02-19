# push the carry bit holder and the output holder
s/^(.*)$/\1#0#/; tsub
:sub
p;
# test whether we're done (both inputs empty)
# case 1: carry bit 1 => we’re going negative, clamp to 0
/^(.*)###1#[01]*$/bsub_zero
# case 2: carry bit 0 => we’re done
s/^(.*)###0#([01]*)$/\1#\2/; tsub_end

# there’s still input left. if the leftover is on the rhs, we can exit right here with a zero, because it’ll go negative
/^(.*)##[01]+#[01]#[01]*$/bsub_zero
# if the leftover is on the lhs, zero-extend the input and move on
s/^(.*)#([01]+)##([01])#([01]*)$/\1#\2#0#\3#\4/
# now we do the truth table thing
# 0 0 0
s/^(.*)#([01]*)0#([01]*)0#0#([01]*)$/\1#\2#\3#0#0\4/; tsub

# 0 0 1
s/^(.*)#([01]*)0#([01]*)0#1#([01]*)$/\1#\2#\3#1#1\4/; tsub
# 0 1 0
s/^(.*)#([01]*)0#([01]*)1#0#([01]*)$/\1#\2#\3#1#1\4/; tsub
# 1 0 0
s/^(.*)#([01]*)1#([01]*)0#0#([01]*)$/\1#\2#\3#0#1\4/; tsub

# 0 1 1
s/^(.*)#([01]*)0#([01]*)1#1#([01]*)$/\1#\2#\3#1#0\4/; tsub
# 1 1 0
s/^(.*)#([01]*)1#([01]*)1#0#([01]*)$/\1#\2#\3#0#0\4/; tsub
# 1 0 1
s/^(.*)#([01]*)1#([01]*)0#1#([01]*)$/\1#\2#\3#0#0\4/; tsub

# 1 1 1
s/^(.*)#([01]*)1#([01]*)1#1#([01]*)$/\1#\2#\3#1#1\4/; tsub

s/^(.*)$/unreachable code reached with: \1/; q1

:sub_zero
s/^(.*)#([01]*)#([01]*)#([01])#([01]*)$/\1#0/

:sub_end
