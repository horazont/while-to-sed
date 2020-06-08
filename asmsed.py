import abc
import re


class Instruction(metaclass=abc.ABCMeta):
    @classmethod
    def from_args(cls, argv):
        assert len(argv) == 0
        return cls()


class Load(Instruction):
    MNEMONIC = "load"
    NARGS = 1

    TEMPLATE = r"s/^(([^#]*#){{{stack_offset}}})([^#]*)((#[^#]*)*)$/\1\3\4#\3/"

    # load $offset
    def __init__(self, stack_offset):
        super().__init__()
        self.stack_offset = stack_offset

    @classmethod
    def from_args(cls, argv):
        return cls(int(argv[0]))

    def __repr__(self):
        return "<instruction: load {}>".format(self.stack_offset)

    def tosed(self):
        return self.TEMPLATE.format(
            stack_offset=self.stack_offset
        )


class Store(Instruction):
    MNEMONIC = "store"
    NARGS = 1

    TEMPLATE = r"s/^(([^#]*#){{{stack_offset}}})([^#]*)((#[^#]*)*)#([^#]*)$/\1\6\4/"

    # store $offset
    def __init__(self, stack_offset):
        super().__init__()
        self.stack_offset = stack_offset

    @classmethod
    def from_args(cls, argv):
        return cls(int(argv[0]))

    def __repr__(self):
        return "<instruction: store {}>".format(self.stack_offset)

    def tosed(self):
        return self.TEMPLATE.format(
            stack_offset=self.stack_offset
        )


class Label(Instruction):
    EXPRESSION = re.compile(r"^\.([a-z0-9][a-z0-9_]*)$", re.I)
    TEMPLATE = ":{label_id}\n"

    def __init__(self, label_id):
        super().__init__()
        self.label_id = label_id

    @classmethod
    def from_args(cls, argv):
        return cls(argv[0])

    def __repr__(self):
        return "<label {!r}>".format(self.label_id)

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
            label_id=self.label_id,
        )


class Jump(Instruction):
    MNEMONIC = "jmp"
    NARGS = 1

    TEMPLATE = r"b{label_id}"

    def __init__(self, label_id):
        super().__init__()
        self.label_id = label_id

    @classmethod
    def from_args(cls, argv):
        return cls(argv[0])

    def __repr__(self):
        return "<instruction: jmp {!r}>".format(self.label_id)

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
            label_id=self.label_id,
        )


class PushConstant(Instruction):
    MNEMONIC = "pushc"
    NARGS = 1

    TEMPLATE = r"s/^(.*)$/\1#{value:b}/"

    def __init__(self, value):
        super().__init__()
        self.value = value

    @classmethod
    def from_args(cls, argv):
        return cls(int(argv[0]))

    def __repr__(self):
        return "<instruction: pushc {}>".format(self.value)

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
            value=self.value
        )


class Dup(Instruction):
    MNEMONIC = "dup"
    NARGS = 0

    TEMPLATE = r"""
    s/^((.*)#)?([^#]*)$/\1\3#\3/
    """

    def __repr__(self):
        return "<instruction: inc>"

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
        )


class Pop(Instruction):
    MNEMONIC = "pop"
    NARGS = 0

    TEMPLATE = r"s/^((.*)#|^)[^#]*$/\2/"

    def __repr__(self):
        return "<instruction: inc>"

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
        )


class JumpIfZero(Instruction):
    MNEMONIC = "jz"
    NARGS = 1

    TEMPLATE = r"/^((.*)#)?0$/{{{{;{pop};b{{label_id}};}}}};{pop}".format(pop=Pop.TEMPLATE)

    def __init__(self, label_id):
        super().__init__()
        self.label_id = label_id

    @classmethod
    def from_args(cls, argv):
        return cls(argv[0])

    def __repr__(self):
        return "<instruction: jz {!r}>".format(self.label_id)

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
            label_id=self.label_id,
        )


class Inc(Instruction):
    MNEMONIC = "inc"
    NARGS = 0

    TEMPLATE = """\
    :_inc{instance}d
    s/^((.*)#)?([01]*)1(_*)$/\\1\\3_\\4/;
    t_inc{instance}d

    s/^((.*)#)?(_*)$/\\10\\3/
    s/^((.*)#)?([01]*)0(_*)$/\\1\\31\\4/;
    y/_/0/

    s/^((.*)#)?0*(1[01]*)$/\\1\\3/;
    s/^((.*)#)?$/\\10/;
    """

    def __repr__(self):
        return "<instruction: inc>"

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
        )


class Add(Instruction):
    MNEMONIC = "add"
    NARGS = 0

    TEMPLATE = """\
    s/^(.*)$/\\1#0#/; t_add{instance}
    :_add{instance}
    s/^(.*)###([01])#([01]*)$/\\1#\\2\\3/; t_add{instance}end
    s/^(.*)##([01]+)#([01])#([01]*)$/\\1#0#\\2#\\3#\\4/
    s/^(.*)#([01]+)##([01])#([01]*)$/\\1#\\2#0#\\3#\\4/
    s/^(.*)#([01]*)0#([01]*)0#0#([01]*)$/\\1#\\2#\\3#0#0\\4/; t_add{instance}
    s/^(.*)#([01]*)0#([01]*)0#1#([01]*)$/\\1#\\2#\\3#0#1\\4/; t_add{instance}
    s/^(.*)#([01]*)0#([01]*)1#0#([01]*)$/\\1#\\2#\\3#0#1\\4/; t_add{instance}
    s/^(.*)#([01]*)1#([01]*)0#0#([01]*)$/\\1#\\2#\\3#0#1\\4/; t_add{instance}
    s/^(.*)#([01]*)0#([01]*)1#1#([01]*)$/\\1#\\2#\\3#1#0\\4/; t_add{instance}
    s/^(.*)#([01]*)1#([01]*)1#0#([01]*)$/\\1#\\2#\\3#1#0\\4/; t_add{instance}
    s/^(.*)#([01]*)1#([01]*)0#1#([01]*)$/\\1#\\2#\\3#1#0\\4/; t_add{instance}
    s/^(.*)#([01]*)1#([01]*)1#1#([01]*)$/\\1#\\2#\\3#1#1\\4/; t_add{instance}
    s/^(.*)$/invalid state: \\1/; p; q1
    :_add{instance}end
    s/^((.*)#|^)0*(1[01]*)$/\\1\\3/;
    s/^((.*)#|^)$/\\10/;
    """

    def __repr__(self):
        return "<instruction: add>"

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
        )


class Dec(Instruction):
    MNEMONIC = "dec"
    NARGS = 0

    TEMPLATE = """\
    :_dec{instance}d
    s/^((.*)#)?([01]*)0(_*)$/\\1\\3_\\4/;
    t_dec{instance}d

    s/^((.*)#)?(_*)$/\\10/; t_dec{instance}end
    s/^((.*)#)?([01]*)1(_*)$/\\1\\30\\4/;
    y/_/1/

    :_dec{instance}end
    s/^((.*)#)?0*(1[01]*)$/\\1\\3/;
    s/^((.*)#)?$/\\10/;
    """

    def __repr__(self):
        return "<instruction: dec>"

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
        )


class Sub(Instruction):
    MNEMONIC = "sub"
    NARGS = 0

    TEMPLATE = """\
    s/^(.*)$/\\1#0#/; t_sub{instance}
    :_sub{instance}
    /^(.*)###1#[01]*$/b_sub{instance}_zero
    s/^(.*)###0#([01]*)$/\\1#\\2/; t_sub{instance}_end
    /^(.*)##[01]+#[01]#[01]*$/b_sub{instance}_zero
    s/^(.*)#([01]+)##([01])#([01]*)$/\\1#\\2#0#\\3#\\4/
    s/^(.*)#([01]*)0#([01]*)0#0#([01]*)$/\\1#\\2#\\3#0#0\\4/; t_sub{instance}
    s/^(.*)#([01]*)0#([01]*)0#1#([01]*)$/\\1#\\2#\\3#1#1\\4/; t_sub{instance}
    s/^(.*)#([01]*)0#([01]*)1#0#([01]*)$/\\1#\\2#\\3#1#1\\4/; t_sub{instance}
    s/^(.*)#([01]*)1#([01]*)0#0#([01]*)$/\\1#\\2#\\3#0#1\\4/; t_sub{instance}
    s/^(.*)#([01]*)0#([01]*)1#1#([01]*)$/\\1#\\2#\\3#1#0\\4/; t_sub{instance}
    s/^(.*)#([01]*)1#([01]*)1#0#([01]*)$/\\1#\\2#\\3#0#0\\4/; t_sub{instance}
    s/^(.*)#([01]*)1#([01]*)0#1#([01]*)$/\\1#\\2#\\3#0#0\\4/; t_sub{instance}
    s/^(.*)#([01]*)1#([01]*)1#1#([01]*)$/\\1#\\2#\\3#1#1\\4/; t_sub{instance}
    :_sub{instance}_zero
    s/^(.*)#([01]*)#([01]*)#([01])#([01]*)$/\\1#0/
    :_sub{instance}_end
    s/^((.*)#|^)?0*(1[01]*)?$/\\1\\3/;
    s/^((.*)#|^)?$/\\10/;
    """

    def __repr__(self):
        return "<instruction: sub>"

    def tosed(self):
        return self.TEMPLATE.format(
            instance=id(self),
        )


INSTRUCTION_SET = list(Instruction.__subclasses__())
COMMENT = re.compile(r"^([^;]*);.*$")


def parse_asm(lines):
    matchmap = []
    for insn in INSTRUCTION_SET:
        try:
            expr = insn.EXPRESSION
        except AttributeError:
            expr = re.compile("{}{}".format(
                re.escape(insn.MNEMONIC),
                r"\s+(\S+)" * insn.NARGS
            ))

        matchmap.append((expr, insn))

    instructions = []

    for i, line_raw in enumerate(lines, 1):
        line = COMMENT.sub(r"\1", line_raw)
        line = line.strip()
        if not line:
            continue

        for expr, cls in matchmap:
            m = expr.match(line)
            if m is None:
                continue

            instructions.append(cls.from_args(m.groups()))
            break
        else:
            raise ValueError("invalid syntax:{}: {}".format(i, line_raw.rstrip("\n")))

    return instructions


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "infile",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
    )
    parser.add_argument(
        "-o", "--output",
        dest="outfile",
        default=None,
    )

    args = parser.parse_args()

    with args.infile as f:
        instructions = parse_asm(f)

    buf = []
    for insn in instructions:
        buf.append(insn.tosed())

    if args.outfile is not None:
        args.outfile = open(args.outfile, "w")
    else:
        args.outfile = sys.stdout

    with args.outfile as f:
        print("#!/bin/sed -rf", file=f)
        print(r"s/^(.*)$/#\1/", file=f)
        for l in buf:
            print(l, file=f)
        print(r":_exit", file=f)
        print(r"s/^#(.*)$/\1/", file=f)
