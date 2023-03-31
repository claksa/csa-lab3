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
    if operand == 'acc':
        return '1'
    elif operand == 'dr':
        return '3'
    elif operand == 'br':
        return '4'
    elif operand == 'sp':
        return '5'
    return operand


def is_register(operand):
    if operand == 'acc' or operand == 'dr' or operand == 'br' or operand == 'sp':
        return True
    else:
        return False


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
    if operand.cmd == Opcode.ADD and operand.p1 is not None and operand.p2 is not None:
        command_args.append(operand.p1)
        command_args.append(operand.p2)
        command |= {"opcode": operand.cmd, "operands": command_args}


def translate(program):
    lines = program.readlines()
    statements = []
    for line in lines:
        statement = remove_comments(line.strip().split())
        if statement:
            statements.append(statement)

    code = []
    labels = []
    for line, statement in enumerate(statements, 1):

        struct = {"opcode": None, "address": None}
        label = {"label": None, "addr": None}

        if statement[0] not in instructions:
            if ":" in statement[0]:
                label["label"] = statement[0].strip().replace(':', '')
                # TODO check: label address or next address (2nd option I suppose)
                label["addr"] = decode_address(line)
            else:
                print("error: no such instruction", statement[0])
            labels.append(label)
            continue
        size = len(statement)
        struct["opcode"] = Opcode(statement[0])
        struct["address"] = line-1
        if size == 2:
            arg = statement[1]
            is_label = False
            for label in labels:
                if arg == label["label"]:
                    struct |= {"op": label["addr"]}
                    is_label = True
            if not is_label:
                # TODO handle reg and mem operands
                op = {"type": "const", "value": arg}
                struct |= {"op": op}
        elif size == 3:
            struct |= {"dest": None, "source": None}

            mem_dict = {"addr": None, "offset": None, "scale": None}

            op1 = {"type": "reg", "value": None}
            op2 = {"type": "reg", "value": None}

            if "[" in statement[1] or "[" in statement[2]:

                if "[" in statement[1]:
                    op1["type"] = "mem"
                    tmp_arg = statement[1]
                    op2["value"] = statement[2]
                else:
                    op2["type"] = "mem"
                    tmp_arg = statement[2]
                    op1["value"] = statement[1]

                tmp_arg = tmp_arg.replace('[', '').replace(']', '')
                if "+" in tmp_arg:
                    tmp_arg = tmp_arg.split("+")
                    if "*" in tmp_arg[0] or "*" in tmp_arg[1]:
                        if "*" in tmp_arg[0]:
                            tmp_arr = tmp_arg[0].split("*")

                            for i in tmp_arr:
                                if is_register(i):
                                    mem_dict["addr"] = i
                                else:
                                    mem_dict["scale"] = i
                            if is_register(tmp_arg[1]):
                                mem_dict["addr"] = tmp_arg[1]
                            else:
                                mem_dict["offset"] = tmp_arg[1]

                        if "*" in tmp_arg[1]:
                            tmp_arr = tmp_arg[1].split("*")
                            print("possible scale", tmp_arr)
                            for i in tmp_arr:
                                if is_register(i):
                                    mem_dict["addr"] = i
                                else:
                                    mem_dict["scale"] = i

                            if is_register(tmp_arg[0]):
                                mem_dict["addr"] = tmp_arg[0]
                            else:
                                mem_dict["offset"] = ord(tmp_arg[0])
                    else:
                        for i in tmp_arg:
                            if is_register(i):
                                mem_dict["addr"] = i
                            else:
                                mem_dict["offset"] = i
                else:
                    if is_register(tmp_arg):
                        mem_dict["addr"] = tmp_arg
                    else:
                        mem_dict["offset"] = tmp_arg
            else:
                op1["value"] = statement[1]
                op2["value"] = statement[2]

                # only source register can be constant
                if not is_register(op2["value"]):
                    op2["type"] = "const"

            if op1["type"] == "mem":
                op1["value"] = mem_dict
            if op2["type"] == "mem":
                op2["value"] = mem_dict

            struct["source"] = op2
            struct["dest"] = op1
        code.append(struct)
    for c in code:
        print(c)
    return code


def main(file):
    target = "output.txt"
    with open(file, 'r') as program:
        code = translate(program)
    write_code(target, code)


if __name__ == '__main__':
    filename = "tests/instr.asm"
    main(filename)
