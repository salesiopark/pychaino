'''
2025/07/15 : 최초 버전 작성
2025/07/26 : CRC16을 packet의 첫 2byte에 숫자로 첨부 -> packet구조와 알고리듬 단순화
'''

from binascii import crc_hqx
import serial # pyserial을 install해야 한다
import serial.tools.list_ports
import time, sys
from random import randint

py_imp_name = sys.implementation.name #"cpython" or "micropython"

# 구분자들
RS = "\x1e"  #코드 주석에서 {RS}로 표시
EOT = "\x04" #코드 주석에서 {EOT}로 표시
bRS, bEOT = b'\x1e', b'\x04'


# packet is a bytes (array)
def print_packet(packet: bytes, header="", end="\n"):
    str_crc16, bytes_data = f"[0x{packet[:2].hex()}]", packet[2:]
    replaced = bytes_data.replace(bRS, b'{RS}').replace(bEOT, b'{EOT}')
    print(header + str_crc16 + str(replaced)[2:-1] + f"  : {len(packet)} bytes", end=end)


'''
print_packet(PACKET_REQUEST_RESEND)
print(verify_crc(PACKET_REQUEST_RESEND[:-1]))
sys.exit()
#'''







def scan_serial_ports():
    ports = serial.tools.list_ports.comports()
    port_list = [(port.device, port.description) for port in ports]
    return port_list

lst = scan_serial_ports()
for e in lst: print(f"'{e[0]}' : {e[1]}")
#sys.exit()


# bool값은 "1","0"으로 바꾸고 나머지 데이터는 그대로 문자열로 변환
map_args = lambda x: "1" if x is True else "0" if x is False else str(x)
#MAX_PACKET_SIZE = 256  # 최대 패킷 크기 제한


class Chaino:

    #_PACKET_RQ_RESEND = (0x1861).to_bytes(2, 'big') + b'E' + bEOT #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    _PACKET_RQ_RESEND = (0x1861).to_bytes(2, 'big') + b'E'
    _MAX_RETRIES = 10


    @staticmethod
    def _str_packet(packet: bytes):
        str_crc16, bytes_data = f"<[0x{packet[:2].hex()}]", packet[2:]
        replaced = bytes_data.replace(bRS, b'{RS}').replace(bEOT, b'{EOT}')
        return str_crc16 + str(replaced)[2:-1] + f">:{len(packet)} bytes"

    @staticmethod
    def _map_args(x):
        return "1" if x is True else "0" if x is False else str(x)        

    '''
    **CRC-16-XMODEM (초기값 0x0000)**은 매우 널리 알려진 표준이다.
    파이썬의 crc_hqx(data, 0x0000)는 이 표준과 정확히 일치하며,
    C/C++로 구현된 코드도 쉽게 찾을 수 있고 검증도 용이하다.
    '''
    @staticmethod
    def _CRC_16_XMODEM(payload: bytes) -> bytes:
        return crc_hqx(payload, 0).to_bytes(2, byteorder='big')

    
    @staticmethod
    def _is_crc_matched(packet: bytes) -> bool:
        """
        패킷 구조: [crc:2byte]data_part ({EOT}는 없이 넘어온다)
        따라서 첫 두 바이트(crc16)를 분리하고 나머지로 crc를 계산하여 비교
        """
        received_crc = int.from_bytes(packet[:2], byteorder='big')
        computed_crc = crc_hqx(packet[2:], 0)
        #print(f"received CRC:0x{hex(received_crc)}, computed CRC:0x{hex(computed_crc)}")
        return received_crc == computed_crc



    @staticmethod
    def _print_err(msg: str, end:str = "\n"): #RED text
        print("\033[31mError : " + msg + "\033[0m", end=end)



    @staticmethod
    def _print_err2(msg: str, end:str = "\n"): #BLUE text
        print("\033[34mError : " + msg + "\033[0m", end=end)



    def __init__(self, port, i2c_addr: int=0):
        
        if isinstance(port, str): self.connect_serial(port)
        elif isinstance(port, Chaino):
            self._serial = port._serial
            print(f"I2c(0x{i2c_addr:02x}) device connected through Chaino Master ('{self._serial.port}').")
        else:
            Chaino._print_err("First parameter must be Serial port name(str) or Chaino object.")
            sys.exit();         

        self._i2c_addr  : int = i2c_addr

        self._cnt_rd_crc_err = 0
        self._cnt_wrt_crc_err = 0



    def connect_serial(self, port:str):
        # 2025/7/19:(eps32) 921600 이 *460800 보다 오히려 더 느려진다. (2ms)
        # 2025/7/21:(RP2040zero) 921600 이 *460800 보다 더 빠르지 않다.(0.8ms < esp32보다 더 고속동작)
        try:
            self._serial = serial.Serial(
                port        = port,
                baudrate    = 460800, # 921600 < **460800 > 230400 > 115200
                timeout     = 3.0,  # 3초 타임아웃
                bytesize    = serial.EIGHTBITS,
                parity      = serial.PARITY_NONE,
                stopbits    = serial.STOPBITS_ONE
            )
            print(f'Serial Port("{port}") connected.')
            #print(self.who())
            self._clear_buffers() # 버퍼 클리어 (문제 2 해결)
        except serial.SerialException:
            Chaino._print_err(f'Serial port("{port}") connection failed.')
            sys.exit()



    def _serial_write(self, packet: bytes):
        #self._serial.write(packet) #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        self._serial.write(packet+bEOT) #끝에 bEOT를 붙여서 전송
        self._serial.flush()



    def _make_exec_func_packet(self, func_num: int, *args) -> bytes:
        """
        RP2040의 함수실행 요구 패킷 생성. 첫 2byts이후는 ASCII문자열. [...]은 option
        패킷 구조 : [crc:2byte]'R'{RS}AD{RS}FN [ {RS}arg1{RS}arg2{RS} ... {RS}argn ] {EOT}
        첫 글자가 'R'이라면 함수 실행을 의미하며 위의 구조를 가진다
            AD (i2c_addr) : 두 자리(고정) 16진수
            FN (func_num) : 한 자리(혹은 두 자리) 16진수 - 아두이노에서 최대 200개까지 등록
        """
        # 1) map_args에서 True는 "1"로 False는 "0"으로 교체한 후 패킷 생성
        parts = ["R", f"{self._i2c_addr:02x}", f"{func_num:x}"]
        parts.extend(Chaino._map_args(x) for x in args)
        payload = RS.join(parts).encode('ascii')
        bytes_crc = Chaino._CRC_16_XMODEM(payload)
        #packet = bytes_crc + payload + bEOT  #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        packet = bytes_crc + payload
        #print_packet(packet,"packet sent:")
        return packet
    
    

    # (2025/07/29:수정) serial port에서 {EOT}까지 패킷을 읽는다
    def _read_packet(self) -> bytes:
        #CRC16에 우연히 \x04(EOT)가 포함될 수 있으므로
        #첫 2byte를 먼저 강제로 읽은 후, 그 나머지를 {EOT}까지 읽는다.
        while self._serial.in_waiting < 2 : pass #적어도 2byte가 올때까지 대기
        packet = self._serial.read(2) # CRC16(2 bytes)를 먼저 읽고
        line = self._serial.read_until(bEOT, size=None)#나머지를 EOT까지 읽는다
        if line.endswith(bEOT):
            return packet + line[:-1]  # EOT 제거
        else:
            self._print_err("Fail to receive [EOT] via Serial")
            sys.exit()

    

    def _clear_buffers(self):

        try:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            time.sleep(0.1)  # 버퍼 안정화 대기
            # 추가로 남은 데이터가 있다면 읽어서 버림
            while self._serial.in_waiting > 0: self._serial.read(self._serial.in_waiting)
        except Exception as e:
            print(f"버퍼 클리어 중 오류: {e}")

    

    def exec_func(self, func_num: int, *args):

        packet = self._make_exec_func_packet(func_num, *args)
        #print_packet(packet)

        try:
            self._serial_write(packet) #(1) packet 송신

            for try_count in range(Chaino._MAX_RETRIES):

                packet_ret = self._read_packet() #패킷 수신
                #print(self._str_packet(packet_ret))

                if packet_ret == None:
                    Chaino._print_err(f"Serial통신 수신 장애({try_count+1}).")
                    self._cnt_rd_crc_err +=1
                    if try_count < Chaino._MAX_RETRIES - 1: continue
                    else: sys.exit()

                #print(f"수신 시도 {retry_attempt + 1}/{Chaino._MAX_RETRIES},",end="")
                #print_packet(packet_ret, "수신패킷:")
                is_crc_ok = Chaino._is_crc_matched(packet_ret)

                #디버그/디버그/디버깅 --------------------------------------
                #if randint(1,20)==1: is_crc_ok = False;#디버그용
                #--------------------------------------------------------
                
                # (3) packet_ret의 crc16을 체크해서 오류가 났다면 packet_request_resend 패킷을 ESP로 보낸다
                if not is_crc_ok:
                    strp = Chaino._str_packet(packet_ret)
                    Chaino._print_err("Recieved packet CRC Error "+strp, end="")

                    self._cnt_rd_crc_err +=1
                    if try_count < Chaino._MAX_RETRIES - 1:
                        print(f" -> Request Resend({try_count+1}/{Chaino._MAX_RETRIES})")
                        self._serial_write(Chaino._PACKET_RQ_RESEND)
                        continue
                    else: sys.exit()
                
                # (4) packet_ret에 crc 오류가 없다면 -> 첫 문자는 'E','S','F' 세 경우뿐
                data_packet = packet_ret[2:]
                char0 = chr(data_packet[0])
                
                if char0 == 'E': # 이쪽에서 보낸 packet이 수신쪽에서 crc오류 발생
                    strp = Chaino._str_packet(packet)
                    Chaino._print_err2("Serial Writing CRC Error "+strp, end="")

                    self._cnt_wrt_crc_err +=1
                    if try_count < Chaino._MAX_RETRIES - 1:
                        print(f" -> Rewriting packet({try_count+1}/{Chaino._MAX_RETRIES})")
                        self._serial_write(packet) #packet을 다시 보낸다
                        continue
                    else: sys.exit()
                
                elif char0 == 'S':# 함수실행 성공: S{RS}args
                    ret_vals = data_packet[2:].split(bRS)   # bytes 분할
                    # args패킷이 비어있어도 ret_vals는 크기가 1이다([b''])
                    if len(ret_vals) == 1:
                        if ret_vals[0]==b'': return None  #반환값이 없는 경우
                        else: return ret_vals[0].decode() #반환값이 하나인 경우
                    else: return [x.decode() for x in ret_vals] #리스트로 반환
                
                elif char0 == 'F':# 함수실행 실패: F{RS}err_msg
                    err_msg = str(data_packet[2:])[2:-1]
                    Chaino._print_err("Function execution fail - "+err_msg)
                    sys.exit()
                                
        except serial.SerialException as e:
                print(f"Serial통신 오류: {e}")
                sys.exit()

        #except Exception as e:
        #        print(f"예상치 못한 오류: {e}")



    def set_i2c_addr(self, new_addr:int): #201번 함수
        if self._i2c_addr != new_addr:
            return self.exec_func(201, new_addr)
        else:
            return f"I2C address is already set to 0x{self._i2c_addr:02x}."

    

    def set_neopixel(self, r:int, g:int, b:int): #202번 함수
        self.exec_func(202, r, g, b)


    def who(self): #0번 함수
        return self.exec_func(203)
