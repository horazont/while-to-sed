# INCREMENT

:inc
:inc_d
s/^((.*)#)?([01]*)1(_*)$/\1\3_\4/;
tinc_d

s/^((.*)#)?(_*)$/\10\3/
s/^((.*)#)?([01]*)0(_*)$/\1\31\4/
y/_/0/

# DECREMENT

:dec
:dec_d
s/^((.*)#)?([01]*)0(_*)$/\1\3_\4/;
tdec_d

# only underscores -> would go negative -> cut at zero
s/^((.*)#)?(_*)$/\10/; tdec_end
s/^((.*)#)?([01]*)1(_*)$/\1\30\4/;
y/_/1/

:dec_end

# NORMALIZE

# clear trailing zeroes
s/^((.*)#)?0*(1[01]*)$/\1\3/;
# re-add single zero if none left
s/^((.*)#)?$/\10/;

# LOAD

s/^(([^#]*#){{{index}}})([^#]*)((#[^#]*)*)$/\1\3\4#\3/

# STORE

s/^(([^#]*#){{{index}}})([^#]*)((#[^#]*)*)#([^#]*)$/\1\6\4/

# CLEAR

s/^(.*)#([^#]*)$/\1#0/
