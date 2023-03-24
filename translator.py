from isa import Opcode, Operand, Term, write_code

DATA_MEM_MAX_SIZE = 0xFFFF
ADDR_MEM_MAX_SIZE = '0x7FF'

instructions = {'mov', 'push', 'pop', 'call', 'ret', 'add', 'mul', 'div', 'jmp', 'cmp', 'jl', 'halt'}


def remove_comments(statement):
    semicolon = ';'
    sem_ind = -1
    if semicolon in statement:
        sem_ind = statement.index(semicolon)
    if sem_ind >= 0:
        del (statement[sem_ind], statement[len(statement) - 1])
    return statement


def decode_as_register(operand):
    if operand == 'ac':
        return '1'
    elif operand == 'cr':
        return '2'
    elif operand == 'dr':
        return '3'
    elif operand == 'br':
        return '4'
    return operand


def decode_address(num):
    hex_num = hex(num)
    if hex_num > ADDR_MEM_MAX_SIZE:
        # throw exception
        pass
    if hex_num < '0':
        # throw exception
        pass
    return hex_num


def decode_instr(command, operand):
    command_args = []
    if operand.cmd == Opcode.MOV and operand.p1 is not None and operand.p2 is not None:
        command_args.append(operand.p1)
        command_args.append(operand.p2)
        command |= {"opcode": operand.cmd, "operands": command_args}
    if operand.cmd == Opcode.HALT and operand.p1 is None and operand.p2 is None:
        command |= {"opcode": operand.cmd, "operands": command_args}
        del command["operands"]


def translate(program):
    lines = program.readlines()
    statements = []
    for line in lines:
        statement = remove_comments(line.strip().split())
        if statement:
            statements.append(statement)

    terms = []
    operands = []
    opcodes = []
    for line, statement in enumerate(statements, 1):
        if statement[0] not in instructions:
            # throw exception
            print("error: no such instruction", statement[0])
        terms.append(Term(line, decode_address(line-1)))
        opcodes.append(Opcode(statement[0]))
        size = len(statement)
        if size == 1:
            operand = Operand(Opcode(statement[0]), None, None)
            operands.append(operand)
        elif size == 2:
            operand = Operand(Opcode(statement[0]), decode_as_register(statement[1]), None)
            operands.append(operand)
        elif size == 3:
            operand = Operand(Opcode(statement[0]), decode_as_register(statement[1]), decode_as_register(statement[2]))
            operands.append(operand)
    terms.append(Term(10, decode_address(23)))

    code = []
    for i in range(len(operands)):
        struct = {"mem": "instr", "opcode": "", "operands": [], "terms": terms[i]}
        # print(opcodes[i], operands[i], terms[i])
        decode_instr(struct, operands[i])
        code.append(struct)

    for c in code:
        print(c)
    return code


def main(file):
    code = ''
    target = "output.txt"
    with open(file, 'r') as program:
        code = translate(program)
    write_code(target, code)


if __name__ == '__main__':
    filename = "test.asm"
    main(filename)
    pass
