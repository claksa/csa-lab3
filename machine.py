# !/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис


import json
import argparse
import logging

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
        self.R7: int = 0

        self.ALU = ALU()

    def latch_acc(self):
        self.ACC = self.data_mem[self.MAR]

    def write_to_mem(self):
        self.data_mem[self.MAR] = self.MDR
        if self.MAR == OUTPUT_ADDR:
            self.output.append(self.data_mem[OUTPUT_ADDR])
            logging.debug('write to IO:  {}'.format(self.data_mem[OUTPUT_ADDR]))
        pass

    def read_from_mem(self):
        if self.MAR == INPUT_ADDR:
            self.data_mem[INPUT_ADDR] = self.input.pop()
            logging.debug('read from IO: {}'.format(self.data_mem[INPUT_ADDR]))
        self.MDR = self.data_mem[self.MAR]
        pass

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
        self.cnt_all_ticks: int = 0

    def tick(self):
        self.tick += 1
        self.trace()

    def do_tick(self):
        self.tick += 1
        logging.debug(self.trace())

    def reset_tick(self):
        self.data_path.ALU.reset_alu()
        self.cnt_all_ticks += self.tick
        self.tick = 0

    def reset_step(self):
        self.reset_tick()
        self.step = 0

    def latch_IR(self, instr):
        self.IR = instr
        self.do_tick()

    def latch_CR(self, value):
        self.data_path.CR = value
        self.do_tick()

    def latch_program_counter(self):
        self.PC += 1
        self.do_tick()

    def instruction_fetch(self):
        self.step += 1
        self.latch_CR(self.program[self.PC])
        self.latch_IR(self.data_path.CR["opcode"])

    @staticmethod
    def stop_cmd(mode: bool):
        if mode:
            exit(0)

    def get_reg(self, value):
        if value == "acc":
            return self.data_path.ACC
        elif value == "dr":
            return self.data_path.MDR
        elif value == "br":
            return self.data_path.BR
        elif value == "sp":
            return self.data_path.SP
        elif value == "r7":
            return self.data_path.R7

    def save_value(self, dest, src):
        if dest == "dr":
            self.data_path.MDR = src
        elif dest == "br":
            self.data_path.BR = src
        elif dest == "acc":
            self.data_path.ACC = src
        elif dest == "r7":
            self.data_path.R7 = src

    def jump(self, addr):
        self.PC = addr
        self.do_tick()

    def operand_fetch(self):
        instr = self.data_path.CR

        if self.IR is Opcode.HALT:
            raise StopIteration()

        if self.IR is Opcode.ADD:
            self.latch_program_counter()
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
                right_op = int(source["value"], 0)
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
            self.data_path.ALU.put_values(left_op, right_op)
            self.data_path.ALU.add(set_flags=True)
            self.data_path.ACC = self.data_path.ALU.res
            self.do_tick()
            self.save_value(dest["value"], self.data_path.ACC)
            self.do_tick()

        if self.IR is Opcode.MOV:
            self.latch_program_counter()
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
                right_op = int(source["value"], 0)
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
            self.data_path.ALU.put_values(left_op, right_op)
            self.data_path.ALU.add(set_flags=False)
            self.do_tick()
            self.save_value(dest["value"], self.data_path.ALU.res)
            self.do_tick()

        if self.IR is Opcode.SUB:
            self.latch_program_counter()
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
                right_op = int(source["value"], 0)
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
            self.data_path.ALU.put_values(left_op, right_op)
            self.data_path.ALU.inc()
            self.data_path.ALU.reverse_right()
            self.data_path.ALU.add(set_flags=True)
            self.save_value(dest["value"], self.data_path.ALU.res)
            self.do_tick()

        if self.IR is Opcode.MUL:
            self.latch_program_counter()
            instr = instr["op"]
            op_type = instr["type"]
            value = instr["value"]
            op = 0
            is_indirect = False
            if op_type == Operand_type.REG:
                op = self.get_reg(value)
            elif op_type == Operand_type.CONST:
                op = int(value, 0)
            elif op_type == Operand_type.MEM:
                op = self.address_fetch(value["addr"], value["offset"], value["scale"])
                is_indirect = True
            if is_indirect:
                self.step += 1
            else:
                self.step += 2
            self.data_path.ALU.put_values(self.data_path.ACC, op)
            self.data_path.ALU.mul(True)
            self.data_path.ACC = self.data_path.ALU.res
            self.do_tick()

        if self.IR is Opcode.DIV:
            self.latch_program_counter()
            dest = instr["dest"]
            value = dest["value"]
            left_op = self.get_reg(value)
            source = instr["source"]
            right_op = self.get_reg(source["value"])
            self.data_path.ALU.put_values(left_op, right_op)
            self.data_path.MDR = self.data_path.ALU.div(True)
            self.save_value(value, self.data_path.ALU.res)
            self.do_tick()

        if self.IR is Opcode.MOD:
            self.latch_program_counter()
            dest = instr["dest"]
            value = dest["value"]
            left_op = self.get_reg(value)
            source = instr["source"]
            right_op = 0
            if source["type"] == 'reg':
                right_op = self.get_reg(source["value"])
            if source["type"] == 'const':
                right_op = int(source["value"], 0)
            self.data_path.ALU.put_values(left_op, right_op)
            self.data_path.ALU.mod(True)
            self.save_value(value, self.data_path.ALU.res)
            self.do_tick()

        if self.IR is Opcode.PUSH:
            self.latch_program_counter()
            instr = instr["op"]
            op_type = instr["type"]
            value = instr["value"]
            op = 0
            if op_type == Operand_type.REG:
                op = self.get_reg(value)
            elif op_type == Operand_type.CONST:
                op = int(value, 0)
            self.step += 2
            self.data_path.ALU.right = op
            self.data_path.ALU.add(set_flags=False)
            self.data_path.push()
            self.do_tick()

        if self.IR is Opcode.POP:
            self.latch_program_counter()
            instr = instr["op"]
            value = instr["value"]
            value = self.get_reg(value)
            self.step += 2
            self.do_tick()
            self.data_path.pop()
            self.data_path.ALU.add(set_flags=False)
            self.save_value(value, self.data_path.ALU.res)
            self.step += 1
            self.do_tick()

        if self.IR is Opcode.CALL:
            self.latch_program_counter()
            self.step += 1
            self.data_path.ALU.right = self.PC
            self.data_path.ALU.add(set_flags=False)
            self.data_path.push()
            self.jump(instr['op'])
            self.do_tick()

        if self.IR is Opcode.RET:
            self.data_path.pop()
            self.data_path.ALU.add(set_flags=False)
            self.PC = self.data_path.ALU.res
            self.do_tick()

        if self.IR is Opcode.JMP:
            self.step += 1
            self.jump(instr['op'])

        if self.IR is Opcode.JN:
            self.step += 1
            if self.data_path.ALU.flags[Flag.NF] is True:
                self.jump(instr['op'])
            else:
                self.latch_program_counter()

        if self.IR is Opcode.JZ:
            self.step += 1
            if self.data_path.ALU.flags[Flag.ZF] is True:
                self.jump(instr['op'])
            else:
                self.latch_program_counter()

        if self.IR is Opcode.SV:
            self.latch_program_counter()
            self.step += 2
            dest = instr["dest"]
            left_op = self.get_reg(dest["value"])
            source = instr["source"]
            right_op = int(source["value"], 0)
            self.data_path.MDR = left_op
            self.data_path.MAR = right_op
            self.do_tick()
            self.data_path.write_to_mem()
            self.do_tick()

        if self.IR is Opcode.LD:
            self.latch_program_counter()
            self.step += 2
            dest = instr["dest"]
            source = instr["source"]
            right_op = int(source["value"], 0)

            self.data_path.MAR = right_op
            self.data_path.read_from_mem()
            self.do_tick()
            self.data_path.ALU.right = self.data_path.MDR
            self.data_path.ALU.add(set_flags=False)
            self.save_value(dest["value"], self.data_path.ALU.res)
            self.do_tick()

        if self.IR is Opcode.DB:
            self.data_path.MAR = instr["address"]
            self.data_path.MDR = instr["data"]
            self.data_path.write_to_mem()
            self.program.pop(self.PC)
            self.do_tick()

        if self.IR is Opcode.TEST:
            self.latch_program_counter()
            instr = instr["op"]
            self.data_path.ALU.right = self.get_reg(instr["value"])
            self.data_path.ALU.add(set_flags=True)
            self.do_tick()

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
        state = "{{STEP: {}, TICK: {}}}".format(
            Step(self.step),
            self.tick
        )
        registers = "{{PC: {}, IR: {}, SP: {}, BR: {}, R7: {}, ACC: {} }}".format(
            self.PC,
            self.IR,
            self.data_path.SP,
            self.data_path.BR,
            self.data_path.R7,
            self.data_path.ACC
        )
        instruction = "{{MDR: {} }}".format(self.data_path.MDR)
        command_reg = "{{CR: {}}}".format(self.data_path.CR)
        alu_state = "{{ALU: {} }}".format(self.data_path.ALU.flags)
        return "{}\n{}\n{}\n{}\n{}".format(state, registers, instruction, command_reg, alu_state)

    def run(self):
        self.instruction_fetch()
        self.operand_fetch()
        self.reset_step()


def simulation(code_stream, input_file, limit=1000):
    control_unit = ControlUnit(code_stream)
    cnt_instr = 0
    with open(input_file, 'r') as input_file:
        for line in input_file.readlines():
            control_unit.data_path.input.append(int(line, 0))
    try:
        while True:
            assert limit > cnt_instr, "too long execution, increase limit!"
            cnt_instr += 1
            control_unit.run()
            pass
    except StopIteration:
        pass
    output_stream = control_unit.data_path.output
    logging.info('output_buffer: {}'.format(output_stream))
    program_ticks = control_unit.cnt_all_ticks
    return output_stream, program_ticks, cnt_instr


def main(code_file, res_file, input_file):
    code_stream = read_code(code_file)
    output, ticks, instr = simulation(code_stream, input_file, limit=1000)
    print(output)
    print("total instr: ", instr, "total ticks: ", ticks)
    with open(res_file, 'w') as file:
        json.dump(output, file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Videos to images')
    parser.add_argument('program', type=str, help='translated program')
    parser.add_argument('input', type=str, help='input file with data')
    parser.add_argument('result', type=str, help='result machine file')
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.DEBUG)
    main(code_file=args.program, res_file=args.result, input_file=args.input)
