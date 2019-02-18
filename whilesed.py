import collections
import itertools
import re


# CLEAR
# x[0-9]+ = 0

# ASSIGN/ADD
# x[0-9]+ = x[0-9]+ \+ (x[0-9]+|[0-9]+)

# LOOP
# loop x[0-9]+
# end

# WHILE
# while x[0-9]+
# end


class ASTNode:
    def visit(self):
        return []


class Block(ASTNode):
    def __init__(self, stmts):
        self.stmts = list(stmts)

    def visit(self):
        yield from self.stmts


class While(ASTNode):
    def __init__(self, cond_var, block):
        self.cond_var = cond_var
        self.block = block

    def visit(self):
        yield self.block


class Loop(ASTNode):
    def __init__(self, ctr_var, block):
        self.ctr_var = ctr_var
        self.block = block

    def visit(self):
        yield self.block


class SetConstant(ASTNode):
    def __init__(self, out_var, constant):
        self.out_var = out_var
        self.constant = constant


def Clear(out_var):
    return SetConstant(out_var, Constant(0))


class AssignAdd(ASTNode):
    def __init__(self, out_var, in_var, constant):
        self.out_var = out_var
        self.in_var = in_var
        self.constant = constant


class Constant(ASTNode):
    def __init__(self, value):
        self.value = value


class AssignAddVar(ASTNode):
    def __init__(self, out_var, op1_var, op2_var):
        pass

    # def lower_basic_LOOP(self):
    #     return [
    #         AssignAdd(self.out_var, self.op1_var, Constant(0)),
    #         LoopBlock(self.op2_var, [
    #             AssignAdd(self.out_var, self.out_var, Constant(1))
    #         ]),
    #     ]


class AssignMulVar(ASTNode):
    def __init__(self, out_var, op1_var, op2_var):
        pass

    # def lower_basic_LOOP(self):
    #     return [
    #         Clear(self.out_var),
    #         LoopBlock(
    #             self.op2_var,
    #             AssignAddVar(self.out_var, self.out_var, self.op1_var).to_basic_LOOP()
    #         )
    #     ]


def eval_subtree(subtree, memory):
    if isinstance(subtree, SetConstant):
        memory[subtree.out_var] = subtree.constant.value
    elif isinstance(subtree, AssignAdd):
        memory[subtree.out_var] = max(memory[subtree.in_var] + subtree.constant.value, 0)
    elif isinstance(subtree, Loop):
        for _ in range(memory[subtree.ctr_var]):
            eval_subtree(subtree.block, memory)
    elif isinstance(subtree, Block):
        for node in subtree.visit():
            eval_subtree(node, memory)
    elif isinstance(subtree, While):
        while memory[subtree.cond_var] != 0:
            for node in subtree.visit():
                eval_subtree(node, memory)
    else:
        raise NotImplementedError("no eval implementation for {}".format(subtree))


def eval_tree(tree, valuemap={}):
    treevars = sorted(set(findvars(tree)))
    if any(name not in treevars for name in valuemap):
        raise ValueError("unused value")

    memory = collections.defaultdict(lambda: 0)
    memory.update(valuemap)
    eval_subtree(tree, memory)
    return memory


def findvars(tree):
    if isinstance(tree, SetConstant):
        yield tree.out_var
    elif isinstance(tree, AssignAdd):
        yield tree.out_var
        yield tree.in_var
    elif isinstance(tree, Loop):
        yield tree.ctr_var

    for node in tree.visit():
        yield from findvars(node)


sed_store = r"s/^(([^#]*#){{{index}}})([^#]*)((#[^#]*)*)#([^#]*)$/\1\6\4/"
sed_load = r"s/^(([^#]*#){{{index}}})([^#]*)((#[^#]*)*)$/\1\3\4#\3/"
sed_pop = r"s/^(.*)#([^#]*)$/\1/"
sed_jz = r"/^((.*)#)?0$/b{label}"
sed_inc = """\
:inc{instance}
:inc{instance}_d
s/^((.*)#)?([01]*)1(_*)$/\\1\\3_\\4/;
tinc{instance}_d

s/^((.*)#)?(_*)$/\\10\\3/
s/^((.*)#)?([01]*)0(_*)$/\\1\\31\\4/;
y/_/0/

s/^((.*)#)?0*(1[01]*)$/\\1\\3/;
s/^((.*)#)?$/\\10/;
"""

sed_dec = """\
:dec{instance}
:dec{instance}_d
s/^((.*)#)?([01]*)0(_*)$/\\1\\3_\\4/;
tdec{instance}_d

s/^((.*)#)?(_*)$/\\10/; tdec{instance}_end
s/^((.*)#)?([01]*)1(_*)$/\\1\\30\\4/;
y/_/1/

:dec{instance}_end
s/^((.*)#)?0*(1[01]*)$/\\1\\3/;
s/^((.*)#)?$/\\10/;
"""


def instantiate_sed_template(template, instance_id, **kwargs):
    return template.format(instance=instance_id, **kwargs)


def tosed_subtree(tree, slotmap):
    if isinstance(tree, SetConstant):
        # generate the value in the buffer
        yield r"s/^(.*)$/\1#{:b}/".format(tree.constant.value)
        # store the zero
        dest_index = slotmap[tree.out_var]
        yield instantiate_sed_template(
            sed_store,
            id(tree),
            index=dest_index,
        )
    elif isinstance(tree, AssignAdd):
        src_index = slotmap[tree.in_var]
        dest_index = slotmap[tree.out_var]
        # load
        yield instantiate_sed_template(
            sed_load,
            id(tree),
            index=src_index,
        )

        if tree.constant.value > 0:
            # increase by constant
            for i in range(tree.constant.value):
                yield instantiate_sed_template(
                    sed_inc,
                    "{}_{}".format(id(tree), i)
                )
        elif tree.constant.value < 0:
            # decrease by constant
            for i in range(-tree.constant.value):
                yield instantiate_sed_template(
                    sed_dec,
                    "{}_{}".format(id(tree), i)
                )

        # store to dest
        yield instantiate_sed_template(
            sed_store,
            id(tree),
            index=dest_index,
        )
    elif isinstance(tree, Loop):
        # this will become slightly stacky, but I don’t think that’s an issue
        src_index = slotmap[tree.ctr_var]
        head_label = "loop_head_{}".format(id(tree))
        exit_label = "loop_exit_{}".format(id(tree))
        # first, we load the counter
        yield instantiate_sed_template(
            sed_load,
            id(tree),
            index=src_index,
        )
        # next, we insert a label where we’ll jump
        yield ":{}".format(head_label)
        # and now we check whether we may even iterate; for this, we check if
        # the number is zero and branch to the end if it is
        yield instantiate_sed_template(
            sed_jz,
            id(tree),
            label=exit_label,
        )
        # now that we’ve that cleared, we insert the loop body
        yield from tosed_subtree(tree.block, slotmap)
        # and finally, decrease our counter and return
        yield instantiate_sed_template(
            sed_dec,
            id(tree)
        )
        # reloop
        yield "b{}".format(head_label)
        # exit label
        yield ":{}".format(exit_label)
        # we need to "pop" the element from the stack
        yield instantiate_sed_template(
            sed_pop,
            id(tree)
        )
    elif isinstance(tree, While):
        # again, stacky
        var_index = slotmap[tree.cond_var]
        head_label = "while_head_{}".format(id(tree))
        exit_label = "while_exit_{}".format(id(tree))
        # head label
        yield ":{}".format(head_label)
        # check condition: load value
        yield instantiate_sed_template(
            sed_load,
            id(tree),
            index=var_index,
        )
        # check condition: if zero, branch to exit
        yield instantiate_sed_template(
            sed_jz,
            id(tree),
            label=exit_label,
        )
        # check condition: pop value
        yield instantiate_sed_template(sed_pop, id(tree))
        # loop body
        yield from tosed_subtree(tree.block, slotmap)
        # loop
        yield "b{}".format(head_label)
        yield ":{}".format(exit_label)
        # pop counter value again
        yield instantiate_sed_template(sed_pop, id(tree))
    elif isinstance(tree, Block):
        for node in tree.visit():
            yield from tosed_subtree(node, slotmap)
    else:
        raise NotImplementedError("no tosed implementation for {}".format(tree))


def tosed_tree(tree, valuemap, debug=False):
    treevars = sorted(set(findvars(tree)), key=lambda x: int(x[1:]))
    if any(name not in treevars for name in valuemap):
        raise ValueError("unused value")

    slotmap = {
        name: i
        for i, name in enumerate(treevars)
    }

    init = "#".join("{:b}".format(valuemap.get(name, 0)) for name in treevars)

    statements = tosed_subtree(tree, slotmap)
    if debug:
        code = "\np;\n".join(
            itertools.chain([""], statements, [""])
        )
    else:
        code = "\n".join(statements)

    return init, code, treevars


def parse(lines):
    rxs_identifier = "x_?[0-9]+"
    rx_identifier = re.compile("x_?([0-9]+)")
    rx_assign_const = re.compile(
        r"(?P<target>{ident})\s*:?=\s*(?P<value>[0-9]+)".format(ident=rxs_identifier),
        re.I,
    )
    rx_assign_op = re.compile(
        r"(?P<target>{ident})\s*:?=\s*(?P<var>{ident})\s*(?P<op>[-+])\s*(?P<const>[0-9]+)".format(ident=rxs_identifier),
        re.I,
    )
    rx_assign_var = re.compile(
        r"(?P<target>{ident})\s*:?=\s*(?P<var>{ident})".format(ident=rxs_identifier),
        re.I,
    )
    rx_loop_start = re.compile(
        r"loop\s*(?P<ctr>{ident})(\s*do)?".format(ident=rxs_identifier),
        re.I,
    )
    rx_while_start = re.compile(
        r"while\s*(?P<ctr>{ident})(\s*(!=|≠)\s*0+)?(\s*do)?".format(ident=rxs_identifier),
        re.I,
    )
    rx_end = re.compile(r"end", re.I)
    rx_comment = re.compile(r"^([^#]*)#.*$")

    def normalise_name(name):
        return "x{}".format(int(rx_identifier.match(name).group(1)))

    block_stack = []
    out_block = Block([])
    curr_stmts = out_block.stmts

    for i, line_raw in enumerate(lines, 1):
        line = rx_comment.sub(line_raw, r"\1")
        line = line_raw.strip()
        if not line:
            continue

        m = rx_assign_const.match(line)
        if m is not None:
            info = m.groupdict()

            curr_stmts.append(SetConstant(
                normalise_name(info["target"]),
                Constant(int(info["value"]))
            ))
            continue

        m = rx_assign_op.match(line)
        if m is not None:
            info = m.groupdict()
            value = int(info["const"])
            if info["op"] == "-":
                value = -value

            curr_stmts.append(AssignAdd(
                normalise_name(info["target"]),
                normalise_name(info["var"]),
                Constant(value),
            ))
            continue

        m = rx_assign_var.match(line)
        if m is not None:
            info = m.groupdict()

            curr_stmts.append(AssignAdd(
                normalise_name(info["target"]),
                normalise_name(info["var"]),
                Constant(0),
            ))
            continue

        m = rx_loop_start.match(line)
        if m is not None:
            info = m.groupdict()

            new_block = Block([])
            curr_stmts.append(Loop(normalise_name(info["ctr"]), new_block))
            block_stack.append(curr_stmts)
            curr_stmts = new_block.stmts
            continue

        m = rx_while_start.match(line)
        if m is not None:
            info = m.groupdict()

            new_block = Block([])
            curr_stmts.append(While(normalise_name(info["ctr"]), new_block))
            block_stack.append(curr_stmts)
            curr_stmts = new_block.stmts
            continue

        m = rx_end.match(line)
        if m is not None:
            info = m.groupdict()

            curr_stmts = block_stack.pop()
            continue

        raise ValueError("syntax error: {}".format(line_raw))

    return out_block


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "infile",
        nargs="?",
        default=None,
        help="Input file (defaults to stdin)"
    )
    parser.add_argument(
        "-o", "--output",
        dest="outfile",
        default=None,
        help="Output file (defaults to stdout)"
    )

    args = parser.parse_args()

    if args.infile is None:
        args.infile = sys.stdin
    else:
        args.infile = open(args.infile, "r")

    with args.infile as f:
        program = parse(f)

    _, compiled, varmap = tosed_tree(program, {})

    if args.outfile is None:
        args.outfile = sys.stdout
    else:
        args.outfile = open(args.outfile, "w")

    with args.outfile as f:
        print("#!/bin/sed -rf", file=f)
        print("# variable mapping:", file=f)
        print("# {}".format(", ".join(varmap)), file=f)
        print(compiled, file=f)
