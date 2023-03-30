import logging
import sys

from isa import Opcode, read_code

# = 127; 7-битные адреса в памяти
ADDR_MAX_SIZE = '0x7F'
#  16-битная память данных '0xFFFFFFFF'== 2^32-1 == макс. адрес
DATA_MEM_MAX_SIZE = 2 ** 32
INPUT_ADDR = DATA_MEM_MAX_SIZE - 1
OUTPUT_ADDR = DATA_MEM_MAX_SIZE - 2


class DataPath:
    def __init__(self, token_stream):
        # mgm
        self.input: list = token_stream
        self.output: list = []

        self.data_mem: list = [0] * DATA_MEM_MAX_SIZE

        self.acc: int = 0
        self.data_reg: int = 0
        self.addr_reg: int = 0

        self.left: int = 0
        self.right: int = 0

    def inc(self):
        self.left += 1

    def latch_acc(self):
        self.acc = self.data_mem[self.addr_reg]

    def zero_flag(self):
        self.acc = 0

    def write_to_mem(self):
        self.data_mem[self.addr_reg] = self.data_reg

    def write(self):
        if self.addr_reg is OUTPUT_ADDR:
            self.output.append(self.data_mem[self.addr_reg])
        else:
            self.write_to_mem()

    def read_from_mem(self):
        self.data_reg = self.data_mem[self.addr_reg]
        # idk but this next tick:
        self.latch_acc()

    def read(self):
        if self.addr_reg is INPUT_ADDR:
            self.data_mem[self.addr_reg] = self.input.pop()
        else:
            self.read_from_mem()


class ControlUnit:
    def __init__(self, program, data_path):
        self.program = program
        self.data_path = data_path
        # уточнить
        self.cmd_mem: list = [0] * DATA_MEM_MAX_SIZE
        # счетчик тактов
        self.tick: int = 0

        # счетчик "шагов" каждой инструкции
        self.step_counter: int = 0

        # count register; store next instr
        self.cr: int = 0
        # instruction pointer; current register
        self.ip: int = 0

        self.opcode = Opcode.HALT

    def tick(self):
        self.tick += 1

    def current_tick(self):
        return self.tick

    def reset_step_counter(self):
        self.step_counter = 0

    def do_step(self):
        self.step_counter += 1

    def latch_instr_pointer(self):
        self.ip += 1

    def current_instr_addr(self):
        return self.ip

    def latch_program_counter(self, next_instr):
        if next_instr:
            self.cr += 1
        else:
            # error???
            pass

    def do_sstep(self):
        if self.step_counter == 0:
            # instruction  fetch
            instr = self.program[self.cr]
            self.opcode = instr['opcode']
            self.do_step()
        elif self.step_counter == 1:
            # decode
            self.do_step()
            pass
        elif self.step_counter == 2:
            # operand fetch
            self.do_step()
            pass
        elif self.step_counter == 3:
            # execute
            self.do_step()
            pass
        elif self.step_counter == 4:
            # operand store steps is being carried out
            pass

    def execute_by_steps(self):
        # 0 instruction fetch
        instr = self.program[self].cr
        # trace control unit trace
        self.do_step()
        pass
        # 1 decode
        self.opcode = instr['opcode']
        self.do_step()
        pass
        # 2 operands fetch
        if instr['operands']:
            operands = instr['operands']
        self.do_step()
        pass
        # 3 execute
        self.execute_instruction()
        self.do_step()
        pass
        # 4
        pass

    def execute_instruction(self):
        if self.opcode is Opcode.HALT:
            raise StopIteration()

        if self.opcode is Opcode.MOV:
            # execute mov
            pass

        self.latch_instr_pointer()


# limit -- ограничение на кол-во операций
def simulation(code_stream, input_tokens, limit=1000):
    data_path = DataPath(input_tokens)
    control_unit = ControlUnit(code_stream, data_path)
    try:
        while True:
            # throw exception for very long instruction
            control_unit.do_step()
            control_unit.reset_step_counter()
    except StopIteration:
        pass
    output_stream = ''.join(data_path.output)
    return output_stream


def main(code_file, input_file):
    code_stream = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    output = simulation(code_stream, input_tokens=input_token, limit=1000)
    print(''.join(output))
    # print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == '__main__':
    code = "output.txt"
    result = "cpu.txt"
    main(code, result)
