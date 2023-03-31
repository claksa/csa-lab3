from enum import Enum

MASK = 0xFFFFFFFF
CARRY_MASK = 0x100000000
NF_MASK = 0x80000000


class Flag(str, Enum):
    NF = 'NF'
    CF = 'CF'
    ZF = 'ZF'
    OF = 'OF'


class ALU:
    def __init__(self):
        self.res: int = 0

        # левый вход алу
        self.left: int = 0
        # правый вход алу
        self.right: int = 0

        self.flags: dict = {Flag.NF: False, Flag.CF: False, Flag.ZF: False, Flag.OF: False}

    def put_values(self, left: int, right: int):
        self.left = left
        self.right = right

    def check_res(self):
        if self.res == 0:
            self.set_flag(Flag.ZF, True)
        if self.res & CARRY_MASK:
            self.set_flag(Flag.CF, True)
        if self.res & NF_MASK:
            self.set_flag(Flag.NF, True)
        if (not self.left & NF_MASK and not self.right & NF_MASK and self.res & NF_MASK) \
                or (self.left & NF_MASK and self.right & NF_MASK and not self.res & NF_MASK):
            self.set_flag(Flag.OF, True)

    def set_flag(self, flag: Flag, value: bool):
        self.flags[flag] = value

    def reset_flag(self, flag: Flag):
        self.flags[flag] = False

    def add(self, set_flags: bool):
        self.left &= MASK
        self.right &= MASK
        self.res = self.left + self.right
        self.res &= MASK
        if set_flags:
            self.check_res()

    def div(self, set_flags: bool):
        self.left &= MASK
        self.right &= MASK
        self.res = self.left // self.right
        self.res &= MASK
        if set_flags:
            self.check_res()

    def mul(self, set_flags: bool):
        self.left &= MASK
        self.right &= MASK
        self.res = self.left * self.right
        self.res &= MASK
        if set_flags:
            self.check_res()

    def mod(self, set_flags: bool):
        self.left &= MASK
        self.right &= MASK
        self.res = self.right % self.right
        self.res &= MASK
        if set_flags:
            self.check_res()

    def inc(self):
        self.left += 1

    def dec(self):
        self.left -= 1
        self.check_res()

    def reverse_left(self):
        self.left = ~self.left

    def reverse_right(self):
        self.right = ~self.right
        pass
