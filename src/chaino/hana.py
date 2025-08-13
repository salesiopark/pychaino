from .chaino import Chaino


class Hana(Chaino):
    """
    @brief Hana 클래스는 hana 보드를 제어하는 기능을 제공

    @param port 시리얼 포트(str) 또는 마스터 Chaino 객체
    @param i2c_addr I2C 장치 주소 (기본값 0)
    """

    HIGH            = 1
    LOW             = 0

    INPUT           = 0
    OUTPUT          = 1
    INPUT_PULLUP    = 2
    INPUT_PULLDOWN  = 3


    def __init__(self, port, i2c_addr: int = 0):
        """
        @brief Devkit 인스턴스를 초기화.

        @param port 시리얼 포트 또는 통신 포트
        @param i2c_addr I2C 장치 주소, 기본값은 0
        """
        super().__init__(port, i2c_addr)

    
    def set_pin_mode(self, pin:int, mode:int):
        pass

    
    def read_digital(self, pin:int):
        pass

    
    def write_digital(self, pin:int, status:int):
        pass


    def read_analog(self, pin: int) -> int:
        """
        @brief 지정한 핀에서 아날로그 값을 읽음.

        @param pin 아날로그 값을 읽을 핀 번호
        @return int 아날로그 변환 결과 값
        """
        str_ret = self.exec_func(4, pin)
        return int(str_ret)

    
    def write_analog(self, pin:int, duty:int):
        pass
