import logging
import sys

from isa import Opcode, read_code, Operand_type
from alu import ALU, Flag
from enum import Enum

# = 127; 7-битные адреса в памяти
ADDR_MAX_SIZE = 2 ** 7
MAX_ADDR = ADDR_MAX_SIZE - 1

#  32-битная память данных '0xFFFFFFFF'== 2^32-1 == макс. адрес
DATA_MEM_MAX_SIZE = 2 ** 32

# 16-битная память команд 0xFFFF == 2^16-1, макс. "кодировка" команды; not realised :( optional
CMD_MEM_MAX_SIZE = 2 ** 16

INPUT_ADDR = DATA_MEM_MAX_SIZE - 1
OUTPUT_ADDR = DATA_MEM_MAX_SIZE - 2
SP_DEFAULT = DATA_MEM_MAX_SIZE - 3


# Размер регистра -- 32 бит (?)


class DataPath:
    def __init__(self):
        self.output: list = []
        self.input: list = []

        self.data_mem: list = [0] * DATA_MEM_MAX_SIZE

        self.ACC: int = 0
        # memory-data-register
        self.MDR: int = 0
        # memory-address-register
        self.MAR: int = 0
        # stack pointer
        self.SP: int = SP_DEFAULT
        # command register
        self.CR: int = 0
        # buffer register
        self.BR: int = 0

        self.ALU = ALU()

    def latch_acc(self):
        self.ACC = self.data_mem[self.MAR]

    def write_to_mem(self):
        self.data_mem[self.MAR] = self.MDR
        if self.MAR == OUTPUT_ADDR:
            self.output.append(self.data_mem[OUTPUT_ADDR])

    def read_from_mem(self):
        if self.MAR == INPUT_ADDR:
            self.data_mem[INPUT_ADDR] = self.input.pop()
        self.MDR = self.data_mem[self.MAR]

    def push(self):
        self.SP -= 1
        self.MAR = self.SP
        self.MDR = self.ALU.res
        self.write_to_mem()

    def pop(self):
        self.MAR = self.SP
        self.read_from_mem()
        self.ALU.right = self.MDR
        self.SP += 1


class Step(Enum):
    INSTR_FETCH = 1
    ADDR_FETCH = 2
    OPERAND_FETCH = 3
    EXECUTION = 4


class ControlUnit:
    def __init__(self, program):
        self.program = program

        # holds the memory address of the next instruction to be fetched from main memory -- program counter
        self.PC: int = 0
        self.data_path = DataPath()

        # instruction register; holds current instruction
        self.IR: int = 0

        self.step: int = 0
        self.tick: int = 0

    def tick(self):
        self.tick += 1

    def reset_step(self):
        self.step = 0

    def reset_tick(self):
        self.tick = 0

    def latch_IR(self, instr):
        self.IR = instr

    def latch_program_counter(self, next_addr):
        if next_addr:
            self.PC += 1
        else:
            instr = self.program[self.PC]
            # TODO handle next program error
            assert 'op' in instr, "internal error"
            # self.PC = instr["op"]

    def instruction_fetch(self):
        self.step += 1
        instr = self.program[self.PC]
        self.data_path.MDR = instr
        self.tick += 1
        self.trace()
        self.data_path.CR = self.data_path.MDR
        self.tick += 1
        self.trace()
        self.IR = instr["opcode"]
        self.tick += 1
        self.trace()

    def get_reg(self, value):
        if value == "acc":
            return self.data_path.ACC
        elif value == "dr":
            return self.data_path.MDR
        elif value == "br":
            return self.data_path.BR
        elif value == "sp":
            return self.data_path.SP

    def save_value(self, dest, src):
        if dest == "dr":
            self.data_path.MDR = src
        elif dest == "br":
            self.data_path.BR = src
        elif dest == "acc":
            self.data_path.ACC = src

    def jump(self, addr):
        self.PC = addr
        self.tick += 1
        self.trace()

    def operand_fetch(self):

        instr = self.data_path.CR

        if self.IR is Opcode.HALT:
            raise StopIteration()

        if self.IR is Opcode.ADD:
            # fetch operand(as step)
            dest = instr["dest"]
            dest_type = dest["type"]

            source = instr["source"]
            src_type = source["type"]

            left_op = 0
            right_op = 0
            is_indirect = False

            if src_type == Operand_type.REG:
                right_op = self.get_reg(source["value"])

            elif src_type == Operand_type.CONST:
                right_op = int(source["value"], 32)
            elif src_type == Operand_type.MEM:
                right_op = self.address_fetch(right_op["addr"], right_op["offset"], right_op["scale"])
                is_indirect = True

            if dest_type == Operand_type.REG:
                left_op = self.get_reg(dest["value"])

            elif dest_type == Operand_type.MEM:
                left_op = self.address_fetch(right_op["addr"], right_op["offset"], right_op["scale"])
                is_indirect = True

            print("left_op, right_op:", left_op, right_op)
            if is_indirect:
                self.step += 1
            else:
                self.step += 2
            self.trace()
            #   execution step:
            self.tick += 1

            self.data_path.ALU.put_values(left_op, right_op)
            self.data_path.ALU.add(set_flags=True)
            self.data_path.ACC = self.data_path.ALU.res

            self.trace()
            self.save_value(dest["value"], self.data_path.ACC)
            self.tick += 1
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()

        if self.IR is Opcode.MOV:
            dest = instr["dest"]
            dest_type = dest["type"]

            source = instr["source"]
            src_type = source["type"]
            left_op = 0
            right_op = 0
            is_indirect = False

            if src_type == Operand_type.REG:
                right_op = self.get_reg(source["value"])

            elif src_type == Operand_type.CONST:
                right_op = int(source["value"], 32)
            elif src_type == Operand_type.MEM:
                right_op = self.address_fetch(right_op["addr"], right_op["offset"], right_op["scale"])
                is_indirect = True

            if dest_type == Operand_type.MEM:
                left_op = self.address_fetch(right_op["addr"], right_op["offset"], right_op["scale"])
                is_indirect = True

            if is_indirect:
                self.step += 1
            else:
                self.step += 2
            self.trace()
            #   execution step:
            self.tick += 1

            self.data_path.ALU.put_values(left_op, right_op)
            self.data_path.ALU.add(set_flags=False)

            self.trace()
            self.save_value(dest["value"], self.data_path.ALU.res)

            self.tick += 1
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()

        if self.IR is Opcode.SUB:
            dest = instr["dest"]
            dest_type = dest["type"]

            source = instr["source"]
            src_type = source["type"]
            left_op = 0
            right_op = 0
            is_indirect = False

            if src_type == Operand_type.REG:
                right_op = self.get_reg(source["value"])

            elif src_type == Operand_type.CONST:
                right_op = int(source["value"], 32)
            elif src_type == Operand_type.MEM:
                right_op = self.address_fetch(right_op["addr"], right_op["offset"], right_op["scale"])
                is_indirect = True

            if dest_type == Operand_type.REG:
                left_op = self.get_reg(dest["value"])

            elif dest_type == Operand_type.MEM:
                left_op = self.address_fetch(right_op["addr"], right_op["offset"], right_op["scale"])
                is_indirect = True

            if is_indirect:
                self.step += 1
            else:
                self.step += 2
            self.trace()
            #   execution step:
            self.data_path.ALU.put_values(left_op, right_op)
            self.data_path.ALU.inc()
            self.data_path.ALU.reverse_right()
            self.data_path.ALU.add(True)
            self.tick += 1
            self.trace()
            self.save_value(dest["value"], self.data_path.ALU.res)
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()

        if self.IR is Opcode.MUL:
            instr = instr["op"]
            op_type = instr["type"]
            value = instr["value"]
            op = 0
            is_indirect = False

            if op_type == Operand_type.REG:
                op = self.get_reg(value)

            elif op_type == Operand_type.CONST:
                op = int(value, 32)

            elif op_type == Operand_type.MEM:
                op = self.address_fetch(value["addr"], value["offset"], value["scale"])
                is_indirect = True

            if is_indirect:
                self.step += 1
            else:
                self.step += 2
            self.trace()
            #   execution step:
            self.data_path.ALU.put_values(self.data_path.ACC, op)
            self.data_path.ALU.mul(True)
            self.tick += 1
            self.trace()
            self.data_path.ACC = self.data_path.ALU.res
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()

        if self.IR is Opcode.DIV:
            instr = instr["op"]
            op_type = instr["type"]
            value = instr["value"]
            op = 0
            is_indirect = False

            if op_type == Operand_type.REG:
                op = self.get_reg(value)

            elif op_type == Operand_type.CONST:
                op = int(value, 32)

            elif op_type == Operand_type.MEM:
                op = self.address_fetch(value["addr"], value["offset"], value["scale"])
                is_indirect = True

            if is_indirect:
                self.step += 1
            else:
                self.step += 2
            self.trace()
            #   execution step:
            self.data_path.ALU.put_values(self.data_path.ACC, op)
            self.data_path.ALU.div(True)
            self.data_path.ACC = self.data_path.ALU.res
            self.tick += 1
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()

        if self.IR is Opcode.MOD:
            instr = instr["op"]
            op_type = instr["type"]
            value = instr["value"]
            op = 0
            is_indirect = False

            if op_type == Operand_type.REG:
                op = self.get_reg(value)

            elif op_type == Operand_type.CONST:
                op = int(value, 32)

            elif op_type == Operand_type.MEM:
                op = self.address_fetch(value["addr"], value["offset"], value["scale"])
                is_indirect = True

            if is_indirect:
                self.step += 1
            else:
                self.step += 2
            self.trace()
            #   execution step:
            self.data_path.ALU.put_values(self.data_path.ACC, op)
            self.data_path.ALU.mod(True)
            self.data_path.ACC = self.data_path.ALU.res
            self.tick += 1
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()

        if self.IR is Opcode.PUSH:
            instr = instr["op"]
            op_type = instr["type"]
            value = instr["value"]
            op = 0

            if op_type == Operand_type.REG:
                op = self.get_reg(value)

            elif op_type == Operand_type.CONST:
                op = int(value, 32)

            self.step += 2
            self.data_path.ALU.right = op
            # self.data_path.ALU.put_values(self.data_path.ACC, op)
            self.data_path.ALU.add(False)
            self.data_path.push()
            self.tick += 1
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()

        if self.IR is Opcode.POP:
            # operand fetch
            instr = instr["op"]
            value = instr["value"]

            # only destination register
            value = self.get_reg(value)
            self.step += 2
            self.tick += 1
            self.trace()

            # execute
            self.data_path.pop()
            self.data_path.ALU.add(False)
            if value == "acc":
                self.data_path.ACC = self.data_path.ALU.res
            elif value == "dr":
                self.data_path.MDR = self.data_path.ALU.res
            elif value == "br":
                self.data_path.BR = self.data_path.ALU.res
            self.step += 1
            self.tick += 1
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()
        if self.IR is Opcode.CALL:
            self.step += 1
            # положили на стек след инструкцию
            self.PC += 1
            self.tick += 1
            self.trace()

            self.data_path.ALU.right = self.PC
            self.data_path.ALU.add(False)
            self.data_path.push()
            self.jump(instr['op'])
            self.tick += 1
            self.trace()
        if self.IR is Opcode.RET:
            # сняли со стека адрес возврата
            self.data_path.pop()
            self.data_path.ALU.add(False)
            self.PC = self.data_path.ALU.res
            self.tick += 1
            self.trace()
        if self.IR is Opcode.JMP:
            self.step += 1
            self.jump(instr['op'])
        if self.IR is Opcode.JN:
            self.step += 1
            if self.data_path.ALU.flags[Flag.NF] is True:
                self.jump(instr['op'])
        #  прямая загрузка -- сохранить значение в ячейку памяти dest <-- value
        if self.IR is Opcode.SV:
            self.step += 2
            dest = instr["dest"]
            left_op = self.get_reg(dest["value"])

            source = instr["source"]
            right_op = int(source["value"], 32)

            self.data_path.ALU.put_values(left_op, right_op)
            self.data_path.ALU.add(False)
            self.data_path.write_to_mem()
            # TODO проверить такты для прямой загрузки
            self.tick += 1
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()
        # прямая "выгрузка" -- загрузить из ячейки памяти reg <-- mem(addr)
        if self.IR is Opcode.LD:
            dest = instr["dest"]
            source = instr["source"]
            # addr
            right_op = int(source["value"], 7)
            self.data_path.MAR = right_op
            # прочитанное значение в регистре данных
            self.data_path.read_from_mem()
            self.data_path.ALU.right = self.data_path.MDR
            self.data_path.ALU.add(False)

            value = dest["value"]
            if value == "acc":
                self.data_path.ACC = self.data_path.ALU.res
            elif value == "dr":
                self.data_path.MDR = self.data_path.ALU.res
            elif value == "br":
                self.data_path.BR = self.data_path.ALU.res
            self.tick += 1
            self.trace()

            self.PC += 1
            self.tick += 1
            self.trace()

    def address_fetch(self, address, offset, scale):
        res = 0
        if address is not None:
            # fetch address value --> acc
            if offset is not None and scale is not None:
                # addr*scale+offset -- use alu 2 ticks (or more)
                pass
            if offset is None and scale is not None:
                # addr*scale -- use alu 1 time +1 tick
                pass
            if offset is not None and scale is None:
                # addr + offset -- use alu 1 time +1 tick
                pass
        elif offset is not None:
            # acc+offset -- use alu 1 ticks
            pass
        self.step += 1
        return res

    def trace(self):
        print("------")
        state = "{{STEP: {}, TICK: {}}}".format(
            Step(self.step),
            self.tick
        )
        registers = "{{PC: {}, IR: {}, SP: {}, BR: {}, ACC: {} }}".format(
            self.PC,
            self.IR,
            self.data_path.SP,
            self.data_path.BR,
            self.data_path.ACC
        )
        instruction = "{{MDR: {} }}".format(self.data_path.MDR)
        command_reg = "{{CR: {}}}".format(self.data_path.CR)
        alu_state = "{{ALU: {} }}".format(self.data_path.ALU.flags)
        print(state)
        print(registers)
        print(instruction)
        print(command_reg)
        print(alu_state)
        print()

    def run(self):
        self.instruction_fetch()
        self.operand_fetch()
        self.reset_tick()
        self.reset_step()


def simulation(code_stream, limit=1000):
    control_unit = ControlUnit(code_stream)
    control_unit.run()
    try:
        while True:
            control_unit.run()
    except StopIteration:
        pass
    output_stream = ''.join(control_unit.data_path.output)
    return output_stream


def main(code_file, res_file, input_file):
    code_stream = read_code(code_file)
    output = simulation(code_stream, limit=1000)
    print(''.join(output))
    # print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == '__main__':
    code = "build/output.txt"
    result = "cpu.txt"
    main(code, result, input_file="build/input.txt")
