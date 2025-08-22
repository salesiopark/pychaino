#2025/07/15 : 최초 버전 작성
"""
Core class of chaino Protocol Package
======================================

This module provides the Python client-side implementation for the Chaino protocol,
allowing communication with Chaino-enabled Arduino devices. It supports both standard
CPython (via Serial/pyserial) and MicroPython (via I2C).

The primary entry point is the :class:`Chaino` class, which abstracts the low-level
details of packet creation, CRC checking, and communication.

CPython (Serial) Usage:
-----------------------
.. code-block:: python

    from chaino import Chaino

    # Connect to the master device on COM9
    master = Chaino("COM9")
    print(master.who())

    # Connect to a slave device at I2C address 0x42 via the master on COM9
    slave = Chaino("COM9", i2c_addr=0x42)
    slave.set_neopixel(255, 0, 0) # Set slave's LED to red

MicroPython (I2C) Usage:
------------------------
.. code-block:: python

    from chaino import Chaino

    # Scan for connected slave devices on the I2C bus
    Chaino.scan()

    # Connect to a slave device at I2C address 0x42
    slave = Chaino(0x42)
    print(slave.who())
    slave.set_neopixel(0, 255, 0) # Set slave's LED to green
"""


import sys
import time # micropython에도 time모듈이 있다.

IS_CPYTHON = (sys.implementation.name == "cpython")

# 구분자들
RS = "\x1e"  #코드 주석에서 {RS}로 표시
EOT = "\x04" #코드 주석에서 {EOT}로 표시
bRS, bEOT = b'\x1e', b'\x04'

PACKET_RQ_RESEND = (0x1861).to_bytes(2, 'big') + b'E'


#######################################################################
# python 종류별로 crc_hqx 함수를 정의한다.
#######################################################################
if IS_CPYTHON:
    
    from binascii import crc_hqx # CPython 에서만 존재
    
else: # Micropython에서는 binascii라이브러리에 crc_hqx가 없으므로 직접 구현
    
    def crc_hqx(data: bytes, value: int = 0) -> int:
        crc = value & 0xFFFF
        for b in data:
            crc ^= (b & 0xFF) << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        return crc
########################################################################
# 공통 유틸리티 함수들
########################################################################

'''
**CRC-16-XMODEM (초기값 0x0000)**은 매우 널리 알려진 표준이다.
파이썬의 crc_hqx(data, 0x0000)는 이 표준과 정확히 일치하며,
C/C++로 구현된 코드도 쉽게 찾을 수 있고 검증도 용이하다.
'''
def gen_CRC16_XMODEM(payload: bytes) -> bytes:
    """
    :exclude-from-docs:
    """
    return crc_hqx(payload, 0).to_bytes(2, 'big')


#진리값만 "1"/"0"으로 만들고 나머지는 그대로 str로 변환
def map_args(x):
    """
    :exclude-from-docs:
    """
    return "1" if x is True else "0" if x is False else str(x)        


"""
패킷 구조: [crc:2byte]payload (끝에 {EOT}는 없다)
따라서 첫 두 바이트(crc16)를 분리하고 나머지로 crc를 계산하여 비교
"""
def is_crc_matched(packet: bytes) -> bool:
    """
    :exclude-from-docs:
    """
    if len(packet) <= 2: return False #적어도 crc16+header 3바이트는 되어야 함
    received_crc = int.from_bytes(packet[:2], 'big')
    computed_crc = crc_hqx(packet[2:], 0)
    #print(f"received CRC:0x{hex(received_crc)}, computed CRC:0x{hex(computed_crc)}")
    return received_crc == computed_crc


"""
RP2040의 함수실행 요구 패킷 생성. 첫 2byts이후는 ASCII문자열. [...]은 option
패킷 구조 : [crc:2byte]'R'{RS}AD{RS}FN [ {RS}arg1{RS}arg2{RS} ... {RS}argn ] {EOT}
첫 글자가 'R'이라면 함수 실행을 의미하며 위의 구조를 가진다
    AD (i2c_addr) : 두 자리(고정) 16진수
    FN (func_num) : 한 자리(혹은 두 자리) 16진수 - 아두이노에서 최대 200개까지 등록
"""
def gen_exec_func_packet(i2c_addr: int, func_num: int, *args) -> bytes:
    """
    :exclude-from-docs:
    """
    # 1) map_args에서 True는 "1"로 False는 "0"으로 교체한 후 패킷 생성
    if i2c_addr == -1:  # micropython에서 호출한 경우
        parts = [f"{func_num:x}"]
    else:               # cpython에서 호출한 경우
        parts = ["R", f"{i2c_addr:02x}", f"{func_num:x}"]
    parts.extend(map_args(x) for x in args)
    payload = RS.join(parts).encode('ascii')
    bytes_crc = gen_CRC16_XMODEM(payload)
    packet = bytes_crc + payload
    #print_packet(packet,"packet sent:")
    return packet


def str_packet(packet: bytes):
    """
    :exclude-from-docs:
    """
    str_crc16, bytes_data = f"<[0x{packet[:2].hex()}]", packet[2:]
    replaced = bytes_data.replace(bRS, b'{RS}').replace(bEOT, b'{EOT}')
    return str_crc16 + str(replaced)[2:-1] + f">:{len(packet)} bytes"


def print_err(msg: str, end:str = "\n"): #RED text
    """
    :exclude-from-docs:
    """
    print("\033[31mError : " + msg + "\033[0m", end=end)


def print_err2(msg: str, end:str = "\n"): #BLUE text
    """
    :exclude-from-docs:
    """
    print("\033[34mError : " + msg + "\033[0m", end=end)

def print_red(msg: str, end:str = "\n"): #RED text
    """
    :exclude-from-docs:
    """
    print("\033[31m" + msg + "\033[0m", end=end)


def print_yellow(msg: str, end:str = "\n"): #BLUE text
    """
    :exclude-from-docs:
    """
    print("\033[33m" + msg + "\033[0m", end=end)

########################################################################
# 공통 베이스 클래스
########################################################################

class _ChainoBase:
    
    _MAX_RETRIES = 3
    

    def __init__(self, addr: int):
        self._addr = addr #이 주소는 exec_func_packet을 만드는데 사용됨
        self._cnt_rd_crc_err = 0
        self._cnt_wrt_crc_err = 0


    def _parse_response(self, data_packet: bytes):
        """응답 패킷 파싱 - CPython/MicroPython 공통 로직"""
        char0 = chr(data_packet[0])
        
        if char0 == 'S':  # 함수실행 성공: S{RS}args
            ret_vals = data_packet[2:].split(bRS)
            if len(ret_vals) == 1:
                if ret_vals[0] == b'': 
                    return None  # 반환값이 없는 경우
                else: 
                    return ret_vals[0].decode()  # 반환값이 하나인 경우
            else:
                return [x.decode() for x in ret_vals]  # 리스트로 반환
                
        elif char0 == 'F':  # 함수실행 실패: F{RS}err_msg
            err_msg = str(data_packet[2:])
            raise Exception(f"Function execution fail(addr:{self._addr}): {err_msg}")
            
        else:
            raise Exception(f"Unknown response header(addr:{self._addr}): {char0}")
        
    
    # 공통 인터페이스 메소드들
    def who(self) -> str:
        """
        Gets the identification string of the target device.

        The string is the device name that is set in the Arduino firmware
        which starts as "Chaino_".

        :return: The identification string, e.g., "Chaino_Hana", "Chaino_Unknown".
        :rtype: str
        """
        return self.exec_func(201)
    
    
    def get_version(self) -> str:
        """
        Gets the firmware version string of the target device.

        :return: The firmware version string, e.g., "Chaino_Hana Firmware v0.9.4".
        :rtype: str
        """
        return self.exec_func(202)
    
    
    def get_addr(self) -> int:
        """
        Gets the currently configured I2C address of the target device.

        :return: The I2C address as a int number
        :rtype: int
        """
        int_addr = int(self.exec_func(203))
        #return f"0x{int_addr:2x}"
        return int_addr
    
    
    def set_addr(self, new_addr: int):
        """
        Changes the I2C address of the target device.

        This change is written to the device's EEPROM, making it persistent
        across power cycles. **A device reset is required for the new address
        to take effect.**

        :param new_addr: The new 7-bit I2C address to set (e.g., 0x45).
        :type new_addr: int
        :return: A status message from the device indicating the result.
        :rtype: str
        """
        if self._addr != new_addr:
            return self.exec_func(204, new_addr)
        else:
            return f"I2C address is already set to 0x{self._addr:02x}."
    
    def set_neopixel(self, r: int, g: int, b: int):
        """
        Sets the color of the onboard NeoPixel LED on the target device.

        :param r: The red component of the color (0-255).
        :type r: int
        :param g: The green component of the color (0-255).
        :type g: int
        :param b: The blue component of the color (0-255).
        :type b: int
        """
        self.exec_func(205, r, g, b)



########################################################################
# 플랫폼별 구현
########################################################################

if IS_CPYTHON:#===========================================

    import serial # pyserial을 pip install해야 한다
    import serial.tools.list_ports
    import time
    from random import randint


    class Chaino (_ChainoBase):
        """
        The primary client class for communicating with a Chaino-enabled device from CPython.

        This class handles serial communication with a Chaino master device. It can send
        commands to the master itself or relay them to a specific I2C slave device
        connected to the master. It manages packet formatting, CRC checksums, and
        communication retries automatically.
        """

        
        _SERIAL_TIMEOUT = 0.1 #serial timeout
        _serials = {} 

        @staticmethod
        def scan(): #serial 포트 스캔 함수
            """
            Scans available serial ports for connected Chaino master devices.

            This method iterates through all detected serial ports, attempts to
            connect, and verifies if each is a Chaino master by sending a handshake
            command. It prints a list of found Chaino devices and other ports.

            .. code-block:: python

                Chaino.scan()
            
            Example Output::

                Serial("COM9"): Chaino_Hana (I2C addr.:0x40)
                Serial("COM3"): Not a Chaino (master) device
                Note: Chaino.scan() can detect **MASTER** Chaino devices only.
            """
            ports = serial.tools.list_ports.comports()
            port_list = [(port.device, port.description) for port in ports]
            for s in port_list: #print(f"'{e[0]}' : {e[1]}")
                try:
                    test_obj = Chaino(s[0]) #첫번째 포트로 테스트 객체 생성
                    # 예외가 발생하지 않았다면 "ImChn" 까지 확인된 것임
                    #print_yellow(f'Serial("{s[0]}"): {test_obj._chaino_name}')
                    print_yellow(f'Serial("{s[0]}"): {test_obj._chaino_name}(0x{test_obj._my_slave_addr:02x})')
                except Exception as e:
                    print(str(e))
                    print(f'Serial("{s[0]}"): Not a Chaino (master) device')
            print("Note: Chaino.scan() can detect \033[31m**MASTER**\033[0m Chaino devices only.")


        def ping(self):
            """
            Measures the round-trip communication latency to the target device.

            This method sends a simple command (`who()`) and measures the time it
            takes to receive a response. The result, in milliseconds, is printed
            to the console. This is useful for checking connection health and speed.

            .. code-block:: python
            
                device = Chaino("COM9")
                device.ping()

            Example Output::

                ping... elapsed time to execute who() : 0.934 ms
            """
            print("ping...", end="")
            start_time = time.time()   # 시작 시간 기록
            self.who()
            end_time = time.time()     # 종료 시간 기록
            elapsed_time = end_time - start_time
            print(f" elapsed time to execute who() : {elapsed_time*1000:.3f} ms")


        def __init__(self, port:str, i2c_addr: int=0):
            """
            Initializes a connection to a Chaino device over a serial port.

            If a connection for the given port does not already exist, it will be
            created and verified. If it exists, the existing connection is reused.

            :param port: The name of the serial port (e.g., "COM9" on Windows,
                         "/dev/ttyACM0" on Linux).
            :type port: str
            :param i2c_addr: The 7-bit I2C address of the target slave device.
                             If 0 (default), commands are sent to the master
                             device connected via serial.
            :type i2c_addr: int
            :raises Exception: If the serial port cannot be opened or if the
                               device on the port is not a valid Chaino master.
            
            .. code-block:: python

                # Connect to the master device itself
                master_device = Chaino("COM9")

                # Target a slave device with I2C address 0x42 through the same master
                slave_device = Chaino("COM9", 0x42)
            """
            super().__init__(i2c_addr)
            self._port = port

            if port not in Chaino._serials:
                self._connect_serial() #serial port 연결

            elif i2c_addr == 0: #만약 port가 _serials에 있다면 이미 연결된 것임
                print_err2(f'Serial port("{port}") is already opened.')
                self._serial = Chaino._serials[port] #이미 연결된 serial 객체를 가져온다


        #def _check_connection(self):
        def _connect_serial(self):
            # 2025/7/19:(eps32) 921600 이 *460800 보다 오히려 더 느려진다. (2ms)
            # 2025/7/21:(RP2040zero) 921600 이 *460800 보다 더 빠르지 않다.(0.8ms < esp32보다 더 고속동작)
            try:
                self._serial = serial.Serial(
                    port        = self._port,
                    baudrate    = 460800, # 921600 < **460800 > 230400 > 115200
                    timeout     = Chaino._SERIAL_TIMEOUT, # **read** timeout
                    write_timeout = Chaino._SERIAL_TIMEOUT, #write timeout
                    bytesize    = serial.EIGHTBITS,
                    parity      = serial.PARITY_NONE,
                    stopbits    = serial.STOPBITS_ONE
                )
                self._clear_buffers() # 버퍼 클리어 (문제 2 해결)
                if self.exec_func(0) == "ImChn":
                    self._chaino_name = self.who()
                    self._my_slave_addr = self.get_addr()
                    Chaino._serials[self._port] = self._serial
                
            except Exception as e:
                    #print_err(str(e))
                    #print_red(f'\nSerial port("{self._port}") does not connected to Chaino device.')
                    raise Exception(f'Serial port("{self._port}") does not connected to Chaino device.')
                    #sys.exit() 


        def _serial_write(self, packet: bytes):
            self._serial.write(packet+bEOT) #끝에 bEOT를 붙여서 전송
            #self._serial.flush() # AI가 flush()는 필요치 않다고 함

        

        # (2025/07/29:수정) serial port에서 {EOT}까지 패킷을 읽는다
        def _read_packet(self) -> bytes:
            #CRC16에 우연히 \x04(EOT)가 포함될 수 있으므로
            #첫 2byte를 먼저 강제로 읽은 후, 그 나머지를 {EOT}까지 읽는다.
            packet = self._serial.read(2)
            line = self._serial.read_until(bEOT, size=None)
            if line.endswith(bEOT):
                return packet + line[:-1]  # EOT 제거
            else:
                #print_err("Fail to receive [EOT] via Serial")
                self._clear_buffers() # 버퍼를 클리어하고 None을 반환
                return None        



        def _clear_buffers(self):
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            time.sleep(0.1)  # 버퍼 안정화 대기
            # 추가로 남은 데이터가 있다면 읽어서 버림
            while self._serial.in_waiting > 0:
                self._serial.read(self._serial.in_waiting)



        def exec_func(self, func_num: int, *args):
            """
            Executes a function by its ID on the target Chaino device.

            This is the core low-level method for sending commands. It constructs a
            Chaino packet with the specified function ID and arguments, sends it over
            serial, and handles the response, including CRC checks and retries.
            Higher-level methods like `who()` or `set_neopixel()` use this internally.

            :param func_num: The integer ID of the function to execute on the
                             Arduino device (e.g., 1~200 for user-defined functions).
            :type func_num: int
            :param args: A variable number of arguments to pass to the remote function.
                         Arguments are automatically converted to strings.
            :return: The value(s) returned from the remote function. Can be ``None`` if
                     there's no return value, a ``str`` for a single return value, or a
                     ``list[str]`` for multiple return values.
            :rtype: None | str | list[str]
            :raises Exception: If communication fails after multiple retries, a CRC
                               error persists, or the remote function reports an error.

            .. code-block:: python

                # Assuming a function with ID 12 is registered on the Arduino
                adc_str = master.exec_func(12, 13)
                adc = int(adc_str)
                print(f"adc result: {adc}")
            """
            packet = gen_exec_func_packet(self._addr, func_num, *args)
            #print_packet(packet)
            self._serial_write(packet) #(1) packet 송신

            for try_count in range(Chaino._MAX_RETRIES):

                packet_ret = self._read_packet() #패킷 수신
                #print(self._str_packet(packet_ret))

                if packet_ret == None:
                    #print_err(f"Serial통신 수신 장애({try_count+1}).")
                    self._cnt_rd_crc_err +=1
                    if try_count < Chaino._MAX_RETRIES - 1: continue
                    else:
                        raise Exception("Max retries reached for serial read error.") 
                        #sys.exit()

                #print(f"수신 시도 {retry_attempt + 1}/{Chaino._MAX_RETRIES},",end="")
                #print_packet(packet_ret, "수신패킷:")
                is_crc_ok = is_crc_matched(packet_ret)

                #디버그/디버그/디버깅 --------------------------------------
                #if randint(1,20)==1: is_crc_ok = False;#디버그용
                #--------------------------------------------------------
                
                # (3) packet_ret의 crc16을 체크해서 오류가 났다면 packet_request_resend 패킷을 ESP로 보낸다
                if not is_crc_ok:
                    #print_err("Recieved packet CRC Error "+str_packet(packet_ret), end="")
                    self._cnt_rd_crc_err +=1
                    if try_count < Chaino._MAX_RETRIES - 1:
                        #print(f" -> Request Resend({try_count+1}/{Chaino._MAX_RETRIES})")
                        self._serial_write(PACKET_RQ_RESEND)
                        continue
                    else:
                        raise Exception("Max retries reached for received packet CRC error.")
                        #sys.exit()
                
                # (4) packet_ret에 crc 오류가 없다면 -> 첫 문자(header)는 'E','S','F' 세 경우뿐
                # header가 E라면이쪽에서 보낸 packet이 수신쪽에서 crc오류 발생
                if chr(packet_ret[2]) == 'E': 
                    #print_err2("Serial Writing CRC Error "+str_packet(packet), end="")
                    self._cnt_wrt_crc_err +=1
                    if try_count < Chaino._MAX_RETRIES - 1:
                        #print(f" -> Rewriting packet({try_count+1}/{Chaino._MAX_RETRIES})")
                        self._serial_write(packet) #packet을 다시 보낸다
                        continue
                    else:
                        raise Exception("Max retries reached for resending packet error.")
                        #sys.exit()
                
                return self._parse_response(packet_ret[2:])  # 응답 패킷 파싱 후 반환


##################################################################
else: # micropython에서는 binascii 모듈에 crc_hqx함수가 없음 #=============================
###################################################################
    
    from machine import Pin, I2C
    
    
    class Chaino(_ChainoBase):    
        """
        The primary client class for communicating with a Chaino device from MicroPython.

        This class acts as an I2C master to communicate with Chaino slave devices.
        It manages I2C transactions, packet formatting, CRC checksums, and communication
        retries automatically.
        """
        #chaino는 I2C1을 사용
        _Wire1 = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)


        @staticmethod
        def scan(): #i2c 포트 스캔 함수
            """
            Scans the I2C bus for connected Chaino slave devices.

            This method performs an I2C scan, and for each device found, it
            attempts to communicate to verify if it's a Chaino slave. It prints
            a list of found and identified Chaino devices.

            .. code-block:: python

                Chaino.scan()

            Example Output::

                I2C1 scan starts ...
                Chaino_Hana (slave addr:0x42)
                Chaino_Unknown (slave addr:0x45)
            """
            print("I2C1 scan starts ... ")
            addr_lst = Chaino._Wire1.scan()

            if addr_lst:
                for addr in addr_lst:
                    c = Chaino(addr)
                    print_yellow(f"{c.who()} (slave addr:0x{addr:02x})")
            else:
                print_err("No slave devices found.")



        def ping(self):
            """
            Measures the round-trip communication latency to the target device.

            This method sends a simple command (`who()`) over I2C and measures the
            time it takes to receive a response. The result, in milliseconds, is
            printed to the console.

            .. code-block:: python

                slave = Chaino(0x42)
                slave.ping()
            
            Example Output::

                ping... elapsed time to execute who() : 5.134 ms
            """
            print("ping...", end="")
            start = time.ticks_us()   # 시작 시간 (µs)
            self.who()
            end = time.ticks_us()     # 종료 시간 (µs)
            elapsed = time.ticks_diff(end, start)  # 실행 시간 계산
            print(f" elapsed time to execute who() : {elapsed/1000:.3f} ms")



        def __init__(self, addr:int):
            """
            Initializes a connection to a Chaino slave device over the I2C bus.

            :param i2c_addr: The 7-bit I2C address of the target slave device.
            :type i2c_addr: int

            .. code-block:: python

                # Connect to a slave device with I2C address 0x42
                slave_device = Chaino(0x42)
            """
            super().__init__(addr)
            
        
        
        def exec_func(self, func_num:int, *args):
            """
            Executes a function by its ID on the target I2C slave device.

            This is the core low-level method for sending commands. It constructs a
            Chaino packet and sends it over the I2C bus, handling the response,
            checksums, and retries.

            :param func_num: The integer ID of the function to execute on the
                             Arduino device.
            :type func_num: int
            :param args: A variable number of arguments to pass to the remote function.
            :return: The value(s) returned from the remote function. Can be ``None``,
                     a ``str``, or a ``list[str]``.
            :rtype: None | str | list[str]
            :raises Exception: If I2C communication fails or the remote function
                               reports an error.
            """            
            addr   = self._addr
            packet = gen_exec_func_packet(-1, func_num, *args)

            for attempt in range(Chaino._MAX_RETRIES):
                try:
                    Chaino._Wire1.writeto(addr, packet)
                    buf = Chaino._Wire1.readfrom(addr, 3)
                except OSError:
                    if attempt == Chaino._MAX_RETRIES - 1:
                        raise Exception(f"Slave(addr:0x{addr:02x}) write error")
                    continue

                header, ret_len, rx_ck = buf[0], buf[1], buf[2]
                calc_ck = (~(header + ret_len)) & 0xFF

                # (a) 슬레이브가 'E' 알림 보냄  (b) 체크섬 불일치 → 재시도
                if header == ord('E') or rx_ck != calc_ck:
                    if attempt == Chaino._MAX_RETRIES - 1:
                        why = "crc error" if header == ord('E') else "checksum mismatch"
                        raise Exception(f"Slave(addr:0x{addr:02x}) header invalid: {why}")
                    continue

            
            for attempt in range(Chaino._MAX_RETRIES):
                try:
                    packet_ret = Chaino._Wire1.readfrom(addr, ret_len)
                except OSError:
                    if attempt == Chaino._MAX_RETRIES - 1:
                        raise Exception(f"Slave(addr:0x{addr:02x}) read error")
                    continue

                is_crc_ok = is_crc_matched(packet_ret)
                if not is_crc_ok:
                    if attempt == Chaino._MAX_RETRIES - 1:
                        raise Exception(f"Received packet from slave(addr:0x{addr:02x}) CRC error")
                    continue
                
                if packet_ret[2] == ord('S'): #성공
                    return self._parse_response(packet_ret[2:])
                else: #'S'가 아니면 'F'임
                    raise Exception(f"Fail to execute function#{func_num} at the slave(0x{addr:02x})")

            # 여기 오면 모두 실패
            raise Exception("Slave(addr:0x{addr:02x}) Retry limit exceeded")
    

########################################################################
# 테스트 코드
########################################################################    


if __name__=="__main__":

    import sys, os

    # Ensure that the parent of this package folder ("src") is on sys.path
    pkg_dir = os.path.dirname(os.path.abspath(__file__))   # .../src/chaino
    src_dir = os.path.dirname(pkg_dir)                     # .../src
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # Now import and run the real CLI entrypoint as a package module
    from chaino.__main__ import main as _cli_main
    sys.exit(_cli_main())
