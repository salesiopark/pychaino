'''
2025/07/15 : 최초 버전 작성
2025/07/26 : CRC16을 packet의 첫 2byte에 숫자로 첨부 -> packet구조와 알고리듬 단순화
'''
#2025/08/13 : Cpython과 micropython에서 동시에 사용되는 함수들 분리

import sys
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


'''
**CRC-16-XMODEM (초기값 0x0000)**은 매우 널리 알려진 표준이다.
파이썬의 crc_hqx(data, 0x0000)는 이 표준과 정확히 일치하며,
C/C++로 구현된 코드도 쉽게 찾을 수 있고 검증도 용이하다.
'''
def gen_CRC16_XMODEM(payload: bytes) -> bytes:
    return crc_hqx(payload, 0).to_bytes(2, 'big')


#진리값만 "1"/"0"으로 만들고 나머지는 그대로 str로 변환
def map_args(x):
    return "1" if x is True else "0" if x is False else str(x)        


"""
패킷 구조: [crc:2byte]payload (끝에 {EOT}는 없다)
따라서 첫 두 바이트(crc16)를 분리하고 나머지로 crc를 계산하여 비교
"""
def is_crc_matched(packet: bytes) -> bool:
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
    str_crc16, bytes_data = f"<[0x{packet[:2].hex()}]", packet[2:]
    replaced = bytes_data.replace(bRS, b'{RS}').replace(bEOT, b'{EOT}')
    return str_crc16 + str(replaced)[2:-1] + f">:{len(packet)} bytes"


def print_err(msg: str, end:str = "\n"): #RED text
    print("\033[31mError : " + msg + "\033[0m", end=end)


def print_err2(msg: str, end:str = "\n"): #BLUE text
    print("\033[34mError : " + msg + "\033[0m", end=end)

def print_red(msg: str, end:str = "\n"): #RED text
    print("\033[31m" + msg + "\033[0m", end=end)


def print_yellow(msg: str, end:str = "\n"): #BLUE text
    print("\033[33m" + msg + "\033[0m", end=end)



if IS_CPYTHON:#===========================================

    import serial # pyserial을 install해야 한다
    import serial.tools.list_ports
    import time
    from random import randint
    


    class Chaino:
        
        _SERIAL_TIMEOUT = 0.1 #serial timeout
        _MAX_RETRIES = 3
        _serials = {} 

        @staticmethod
        def scan(): #serial 포트 스캔 함수
            ports = serial.tools.list_ports.comports()
            port_list = [(port.device, port.description) for port in ports]
            for e in port_list: #print(f"'{e[0]}' : {e[1]}")
                test_obj = Chaino(e[0]) #첫번째 포트로 테스트 객체 생성
                if test_obj._is_chaino_device:
                    print_yellow(f'Serial("{e[0]}"): {test_obj._chaino_name}')
                else:
                    print(f'Serial("{e[0]}"): {e[1]}')
            print("Chaino.scan() can detect Chaino \033[31m**MASTER**\033[0m devices only.")


        def __init__(self, port:str, i2c_addr: int=0):
            
            self._port = port
            self._i2c_addr  : int = i2c_addr
            self._cnt_rd_crc_err = 0
            self._cnt_wrt_crc_err = 0
            self._is_chaino_device = False

            if port not in Chaino._serials:
                self._connect_serial() #serial port 연결

            elif i2c_addr == 0: #만약 port가 _serials에 있다면 이미 연결된 것임
                print_err2(f'Serial port("{port}") is already opened.')
                self._serial = Chaino._serials[port] #이미 연결된 serial 객체를 가져온다


        def _check_connection(self):
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
                    self._is_chaino_device = True
                    self._chaino_name = self.who()
                    return self._serial
                
            except Exception as e:
                return None



        def _connect_serial(self):
            serial_or_none = self._check_connection()
            if serial_or_none is None:
                    print_err(f'\nSerial port("{self._port}") does not connected to Chaino device.')
                    #sys.exit() 
                    #raise Exception(f'Serial port("{self._port}") does not connected to Chaino device.')
            else:
                Chaino._serials[self._port] = self._serial



        def _serial_write(self, packet: bytes):
            self._serial.write(packet+bEOT) #끝에 bEOT를 붙여서 전송
            #self._serial.flush() # AI가 flush()는 필요치 않다고 함
            

        

        # (2025/07/29:수정) serial port에서 {EOT}까지 패킷을 읽는다
        def _read_packet(self) -> bytes:
            #CRC16에 우연히 \x04(EOT)가 포함될 수 있으므로
            #첫 2byte를 먼저 강제로 읽은 후, 그 나머지를 {EOT}까지 읽는다.
            #while self._serial.in_waiting < 2 : pass #적어도 2byte가 올때까지 대기
            packet = self._serial.read(2) # CRC16(2 bytes)를 먼저 읽고
            line = self._serial.read_until(bEOT, size=None)#나머지를 EOT까지 읽는다
            if line.endswith(bEOT):
                return packet + line[:-1]  # EOT 제거
            else:
                print_err("Fail to receive [EOT] via Serial")
                #sys.exit()
                self._clear_buffers() # 버퍼를 클리어하고 None을 반환
                return packet        



        def _clear_buffers(self):
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            time.sleep(0.1)  # 버퍼 안정화 대기
            # 추가로 남은 데이터가 있다면 읽어서 버림
            while self._serial.in_waiting > 0: self._serial.read(self._serial.in_waiting)



        """
        RP2040의 함수실행 요구 패킷 생성. 첫 2byts이후는 ASCII문자열. [...]은 option
        패킷 구조 : [crc:2byte]'R'{RS}AD{RS}FN [ {RS}arg1{RS}arg2{RS} ... {RS}argn ] {EOT}
        첫 글자가 'R'이라면 함수 실행을 의미하며 위의 구조를 가진다
            AD (i2c_addr) : 두 자리(고정) 16진수
            FN (func_num) : 한 자리(혹은 두 자리) 16진수 - 아두이노에서 최대 200개까지 등록
        def _gen_exec_func_packet(self, func_num: int, *args) -> bytes:
            # 1) map_args에서 True는 "1"로 False는 "0"으로 교체한 후 패킷 생성
            parts = ["R", f"{self._i2c_addr:02x}", f"{func_num:x}"]
            parts.extend(map_args(x) for x in args)
            payload = RS.join(parts).encode('ascii')
            bytes_crc = gen_CRC16_XMODEM(payload)
            packet = bytes_crc + payload
            #print_packet(packet,"packet sent:")
            return packet
        """


        def exec_func(self, func_num: int, *args):

            #packet = self._gen_exec_func_packet(func_num, *args)
            #print_packet(packet)
            packet = gen_exec_func_packet(self._i2c_addr, func_num, *args)
            self._serial_write(packet) #(1) packet 송신

            for try_count in range(Chaino._MAX_RETRIES):

                packet_ret = self._read_packet() #패킷 수신
                #print(self._str_packet(packet_ret))

                if packet_ret == None:
                    print_err(f"Serial통신 수신 장애({try_count+1}).")
                    self._cnt_rd_crc_err +=1
                    if try_count < Chaino._MAX_RETRIES - 1: continue
                    else: sys.exit()

                #print(f"수신 시도 {retry_attempt + 1}/{Chaino._MAX_RETRIES},",end="")
                #print_packet(packet_ret, "수신패킷:")
                is_crc_ok = is_crc_matched(packet_ret)

                #디버그/디버그/디버깅 --------------------------------------
                #if randint(1,20)==1: is_crc_ok = False;#디버그용
                #--------------------------------------------------------
                
                # (3) packet_ret의 crc16을 체크해서 오류가 났다면 packet_request_resend 패킷을 ESP로 보낸다
                if not is_crc_ok:
                    strp = str_packet(packet_ret)
                    print_err("Recieved packet CRC Error "+strp, end="")

                    self._cnt_rd_crc_err +=1
                    if try_count < Chaino._MAX_RETRIES - 1:
                        print(f" -> Request Resend({try_count+1}/{Chaino._MAX_RETRIES})")
                        self._serial_write(PACKET_RQ_RESEND)
                        continue
                    else:
                        raise Exception("Max retries reached for packet CRC error.")
                        #sys.exit()
                
                # (4) packet_ret에 crc 오류가 없다면 -> 첫 문자는 'E','S','F' 세 경우뿐
                data_packet = packet_ret[2:]
                char0 = chr(data_packet[0])
                
                if char0 == 'E': # 이쪽에서 보낸 packet이 수신쪽에서 crc오류 발생
                    strp = str_packet(packet)
                    print_err2("Serial Writing CRC Error "+strp, end="")

                    self._cnt_wrt_crc_err +=1
                    if try_count < Chaino._MAX_RETRIES - 1:
                        print(f" -> Rewriting packet({try_count+1}/{Chaino._MAX_RETRIES})")
                        self._serial_write(packet) #packet을 다시 보낸다
                        continue
                    else:
                        raise Exception("Max retries reached for packet resending.")
                        #sys.exit()
                
                elif char0 == 'S':# 함수실행 성공: S{RS}args
                    ret_vals = data_packet[2:].split(bRS)   # bytes 분할
                    # args패킷이 비어있어도 ret_vals는 크기가 1이다([b''])
                    if len(ret_vals) == 1:
                        if ret_vals[0]==b'': return None  #반환값이 없는 경우
                        else: return ret_vals[0].decode() #반환값이 하나인 경우
                    else:
                        return [x.decode() for x in ret_vals] #리스트로 반환
                
                elif char0 == 'F':# 함수실행 실패: F{RS}err_msg
                    err_msg = str(data_packet[2:])[2:-1]
                    #print_err("Function execution fail - "+err_msg)
                    #sys.exit()
                    raise Exception("Function execution fail: "+err_msg)       



        def set_i2c_addr(self, new_addr:int): #201번 함수
            if self._i2c_addr != new_addr:
                return self.exec_func(201, new_addr)
            else:
                return f"I2C address is already set to 0x{self._i2c_addr:02x}."

        

        def set_neopixel(self, r:int, g:int, b:int): #202번 함수
            self.exec_func(202, r, g, b)


        def who(self): #203번 함수
            return self.exec_func(203)



else: # micropython에서는 binascii 모듈에 crc_hqx함수가 없음 #=============================

    from machine import Pin, I2C
    
    
    class Chaino:    
        
        #chaino는 I2C1을 사용
        _Wire1 = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
        _MAX_RETRY = 3
        
        @staticmethod
        def scan(): #i2c 포트 스캔 함수

            print("I2C1 scan starts ... ")
            addr_lst = Chaino._Wire1.scan()

            if addr_lst:
                for addr in addr_lst:
                    c = Chaino(addr)
                    print_yellow(c.who())
            else:
                print_err("No slave devices found.")


        def __init__(self, slave_addr:int):
            
            self._slave_addr : int = slave_addr
            
        
        
        def exec_func(self, func_num:int, *args):
            
            addr   = self._slave_addr
            #packet = self._gen_exec_func_packet(func_num, *args)
            packet = gen_exec_func_packet(-1, func_num, *args)

            for attempt in range(Chaino._MAX_RETRY):
                try:
                    Chaino._Wire1.writeto(addr, packet)
                    buf = Chaino._Wire1.readfrom(addr, 3)
                except OSError:
                    if attempt == Chaino._MAX_RETRY - 1:
                        raise Exception(f"Slave(addr:0x{addr:02x}) write error")
                    continue

                header, ret_len, rx_ck = buf[0], buf[1], buf[2]
                calc_ck = (~(header + ret_len)) & 0xFF

                # (a) 슬레이브가 'E' 알림 보냄  (b) 체크섬 불일치 → 재시도
                if header == ord('E') or rx_ck != calc_ck:
                    if attempt == Chaino._MAX_RETRY - 1:
                        why = "crc error" if header == ord('E') else "checksum mismatch"
                        raise Exception(f"Slave(addr:0x{addr:02x}) header invalid: {why}")
                    continue

            
            for attempt in range(Chaino._MAX_RETRY):
                try:
                    packet_ret = Chaino._Wire1.readfrom(addr, ret_len)
                except OSError:
                    if attempt == Chaino._MAX_RETRY - 1:
                        raise Exception(f"Slave(addr:0x{addr:02x}) read error")
                    continue

                is_crc_ok = is_crc_matched(packet_ret)
                if not is_crc_ok:
                    if attempt == Chaino._MAX_RETRY - 1:
                        raise Exception(f"Received packet from slave(addr:0x{addr:02x}) CRC error")
                    continue
                
                if packet_ret[2] == ord('E'): #packet_ret[2]는 첫 글자(header)
                    if attempt == Chaino._MAX_RETRY - 1:
                        raise Exception(f"Sent packet to slave(addr:0x{addr:02x}) CRC error")
                    continue


            # (4) packet_ret에 crc 오류가 없다면 -> 첫 문자는 'E','S','F' 세 경우뿐
            data_packet = packet_ret[2:]
            char0 = chr(data_packet[0])
                
            if char0 == 'S':# 함수실행 성공: S{RS}args
                ret_vals = data_packet[2:].split(bRS)   # bytes 분할
                # args패킷이 비어있어도 ret_vals는 크기가 1이다([b''])
                if len(ret_vals) == 1:
                    if ret_vals[0]==b'': return None  #반환값이 없는 경우
                    else: return ret_vals[0].decode() #반환값이 하나인 경우
                else:
                    return [x.decode() for x in ret_vals] #리스트로 반환
                
            elif char0 == 'F':# 함수실행 실패: F{RS}err_msg
                err_msg = str(data_packet[2:])[2:-1]
                raise Exception("Slave(addr:0x{addr:02x}) function execution fail: "+err_msg)       

            # 여기 오면 모두 실패
            raise Exception("Slave(addr:0x{addr:02x}) Retry limit exceeded")
    
    
        def set_i2c_addr(self, new_addr:int): #201번 함수
            if self._slave_addr != new_addr:
                return self.exec_func(201, new_addr)
            else:
                return f"I2C address is already set to 0x{self._i2c_addr:02x}."

        
        def set_neopixel(self, r:int, g:int, b:int): #202번 함수
            self.exec_func(202, r, g, b)


        def who(self): #203번 함수
            return self.exec_func(203)
        



if __name__=="__main__":

    import time

    c = Chaino(0x40)
    print(c.exec_func(203))
    for _ in range(100):
        c.set_neopixel(255,0,0)
        print(c.exec_func(4,26))
        time.sleep(0.1)
        c.set_neopixel(0,255,0)
        print(c.exec_func(4,26))
        time.sleep(0.1)
        c.set_neopixel(0,0,255)
        print(c.exec_func(4,26))
        time.sleep(0.1)

