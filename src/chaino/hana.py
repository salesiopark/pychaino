from .chaino import Chaino          # CPython 패키지 환경


import sys
IS_MICROPY = (sys.implementation.name == "micropython")


class _HanaCommon:

    """공통 상수/메서드만 정의 (한 번만)"""
    HIGH = 1
    LOW = 0
    
    INPUT = 0
    OUTPUT = 1
    INPUT_PULLUP = 2
    INPUT_PULLDOWN = 3

    def set_pin_mode(self, pin: int, mode: int):
        self.exec_func(1, pin, mode)

    def read_digital(self, pin: int) -> int:
        return int(self.exec_func(2, pin))

    def write_digital(self, pin: int, status: int):
        self.exec_func(3, pin, status)

    def read_analog(self, pin: int) -> int:
        return int(self.exec_func(4, pin))

    def write_analog(self, pin: int, duty: int):
        self.exec_func(5, pin, duty)


if IS_MICROPY:
    
    class Hana(_HanaCommon, Chaino):
        """MicroPython: Chaino(slave_addr:int) 시그니처 가정"""
        def __init__(self, i2c_addr: int):
            # MicroPython용 Chaino는 (slave_addr)만 받는다고 가정
            Chaino.__init__(self, i2c_addr)
            
else:
    
    class Hana(_HanaCommon, Chaino):
        """CPython: Chaino(port, i2c_addr=0) 시그니처 가정"""
        def __init__(self, port, i2c_addr: int = 0):
            Chaino.__init__(self, port, i2c_addr)

