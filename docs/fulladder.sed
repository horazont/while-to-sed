# push the carry bit holder and the output holder
s/^(.*)$/\1#0#/; tadd
:add
# test whether we're done: if both inputs are empty, we only need to move the carry bit to the output and are finished
s/^(.*)###([01])#([01]*)$/\1#\2\3/; tadd_end
# okay, we're not done yet. ensure that both inputs have at least one bit in them
s/^(.*)##([01]+)#([01])#([01]*)$/\1#0#\2#\3#\4/
s/^(.*)#([01]+)##([01])#([01]*)$/\1#\2#0#\3#\4/
# now we do the truth table thing
# 0 0 0
s/^(.*)#([01]*)0#([01]*)0#0#([01]*)$/\1#\2#\3#0#0\4/; tadd

# 0 0 1
s/^(.*)#([01]*)0#([01]*)0#1#([01]*)$/\1#\2#\3#0#1\4/; tadd
# 0 1 0
s/^(.*)#([01]*)0#([01]*)1#0#([01]*)$/\1#\2#\3#0#1\4/; tadd
# 1 0 0
s/^(.*)#([01]*)1#([01]*)0#0#([01]*)$/\1#\2#\3#0#1\4/; tadd

# 0 1 1
s/^(.*)#([01]*)0#([01]*)1#1#([01]*)$/\1#\2#\3#1#0\4/; tadd
# 1 1 0
s/^(.*)#([01]*)1#([01]*)1#0#([01]*)$/\1#\2#\3#1#0\4/; tadd
# 1 0 1
s/^(.*)#([01]*)1#([01]*)0#1#([01]*)$/\1#\2#\3#1#0\4/; tadd

# 1 1 1
s/^(.*)#([01]*)1#([01]*)1#1#([01]*)$/\1#\2#\3#1#1\4/; tadd

:add_end
