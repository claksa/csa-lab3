import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    MOV = 'mov'  # 2 args +
    PUSH = 'push'  # 1 arg
    POP = 'pop'  # 1 arg
    CALL = 'call'  # 1 arg
    RET = 'ret'  # 0
    ADD = 'add'  # 2 args +
    MUL = 'mul'  # 1 arg +
    DIV = 'div'  # 1 arg +
    MOD = 'mod' # 1 arg +
    JMP = 'jmp'  # 1 arg
    SUB = 'sub'  # 1 arg +
    JL = 'jl'  # 1 arg
    HALT = 'halt'  # 0 +


class Operand_type(str, Enum):
    REG = 'reg'
    MEM = 'mem'
    CONST = 'const'


class Operand(namedtuple('operand', 'cmd, p1, p2')):

    # don't call :/ but not important I assume
    def __int__(self, cmd, p1, p2):
        if not isinstance(cmd, str):
            # throw exception
            pass
        self.cmd = Opcode[cmd]
        if self.cmd == Opcode.PUSH or self.cmd == Opcode.POP or self.cmd == Opcode.CALL or self.cmd == Opcode.MUL \
                or self.cmd == Opcode.DIV or self.cmd == Opcode.JMP or self.cmd == Opcode.CMP or self.cmd == Opcode.JL:
            self.p1 = p1
        if self.cmd == Opcode.ADD or self.cmd == Opcode.MOV:
            self.p1 = p2
            self.p2 = p2


class Term(namedtuple('Term', 'line, address')):
    pass


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        instr['opcode'] = Opcode(instr['opcode'])
        # Конвертация списка из term в класс Term
        if 'terms' in instr:
            instr['terms'] = Term(
                instr['term'][0], instr['term'][1])

    return code
