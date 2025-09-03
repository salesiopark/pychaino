"""
class for controlling Chaino_Hana Board
=======================================

This module provides a high-level, Pythonic interface for controlling a
Chaino_Hana board. It abstracts the underlying function calls into
an intuitive, Arduino-like API.

The primary class, :class:`Hana`, inherits all the base communication features
from :class:`~chaino.chaino.Chaino` and adds specific methods for hardware manipulation
like GPIO, ADC, PWM, and tone generation.

CPython Usage:
--------------
.. code-block:: python

    from chaino import Hana
    import time

    # Connect to a Hana board (master or slave)
    hana = Hana("COM9", i2c_addr=0x42)

    # Use Arduino-like functions
    hana.set_pin_mode(13, hana.OUTPUT)
    hana.write_digital(13, hana.HIGH)
    
    pot_value = hana.read_analog(26)
    print(f"Analog value: {pot_value}")

    hana.start_tone(8, 'c4', 500) # Play a C4 note for 500ms

MicroPython Usage:
------------------
.. code-block:: python

    from chaino import Hana
    import time

    # Connect to a Chaino_Hana slave board on the I2C bus
    hana = Hana(0x42)

    # Blink the onboard neopixel
    hana.set_pin_mode(13, hana.OUTPUT)
    for _ in range(3):
        hana.set_neopixel(255,255,255)
        time.sleep(0.5)
        hana.set_neopixel(0,0,0)
        time.sleep(0.5)
"""
import sys, time

try:
    from .chaino import Chaino  # when loading package
except ImportError:
    from chaino import Chaino   # when executing directly


_PITCHES = {
    "b0": 31,

    "c1": 33, "c#1": 35, "db1": 35, "d1": 37, "d#1": 39, "eb1": 39,
    "e1": 41, "f1": 44, "f#1": 46, "gb1": 46, "g1": 49, "g#1": 52, "ab1": 52,
    "a1": 55, "a#1": 58, "bb1": 58, "b1": 62,

    "c2": 65, "c#2": 69, "db2": 69, "d2": 73, "d#2": 78, "eb2": 78,
    "e2": 82, "f2": 87, "f#2": 93, "gb2": 93, "g2": 98, "g#2": 104, "ab2": 104,
    "a2": 110, "a#2": 117, "bb2": 117, "b2": 123,

    "c3": 131, "c#3": 139, "db3": 139, "d3": 147, "d#3": 156, "eb3": 156,
    "e3": 165, "f3": 175, "f#3": 185, "gb3": 185, "g3": 196, "g#3": 208, "ab3": 208,
    "a3": 220, "a#3": 233, "bb3": 233, "b3": 247,

    "c4": 262, "c#4": 277, "db4": 277, "d4": 294, "d#4": 311, "eb4": 311,
    "e4": 330, "f4": 349, "f#4": 370, "gb4": 370, "g4": 392, "g#4": 415, "ab4": 415,
    "a4": 440, "a#4": 466, "bb4": 466, "b4": 494,

    "c5": 523, "c#5": 554, "db5": 554, "d5": 587, "d#5": 622, "eb5": 622,
    "e5": 659, "f5": 698, "f#5": 740, "gb5": 740, "g5": 784, "g#5": 831, "ab5": 831,
    "a5": 880, "a#5": 932, "bb5": 932, "b5": 988,

    "c6": 1047, "c#6": 1109, "db6": 1109, "d6": 1175, "d#6": 1245, "eb6": 1245,
    "e6": 1319, "f6": 1397, "f#6": 1480, "gb6": 1480, "g6": 1568, "g#6": 1661, "ab6": 1661,
    "a6": 1760, "a#6": 1865, "bb6": 1865, "b6": 1976,

    "c7": 2093, "c#7": 2217, "db7": 2217, "d7": 2349, "d#7": 2489, "eb7": 2489,
    "e7": 2637, "f7": 2794, "f#7": 2960, "gb7": 2960, "g7": 3136, "g#7": 3322, "ab7": 3322,
    "a7": 3520, "a#7": 3729, "bb7": 3729, "b7": 3951,

    "c8": 4186, "c#8": 4435, "db8": 4435, "d8": 4699, "d#8": 4978, "eb8": 4978,
}

# 자주 사용되는 음계별 별칭 추가
_NOTES = {

    "do": _PITCHES["c4"],    # 도
    "re": _PITCHES["d4"],    # 레  
    "mi": _PITCHES["e4"],    # 미
    "fa": _PITCHES["f4"],    # 파
    "sol": _PITCHES["g4"],   # 솔
    "la": _PITCHES["a4"],    # 라
    "si": _PITCHES["b4"],    # 시

    "c": _PITCHES["c4"],
    "d": _PITCHES["d4"],
    "e": _PITCHES["e4"],
    "f": _PITCHES["f4"],
    "g": _PITCHES["g4"],
    "a": _PITCHES["a4"],
    "b": _PITCHES["b4"],
}


class _HanaBase:
    # A mixin class providing common hardware control methods for a Chaino_Hana board.
    # This class is not intended to be instantiated directly.
    HIGH = 1
    LOW = 0
    
    INPUT = 0
    OUTPUT = 1
    INPUT_PULLUP = 2
    INPUT_PULLDOWN = 3


    def set_pin_mode(self, pin: int, mode: int):
        """
        Configures the specified pin to behave either as an input or an output.
        This is equivalent to Arduino's ``pinMode()``.

        :param pin: The number of the pin whose mode you wish to set.
        :type pin: int
        :param mode: The mode for the pin. Can be :attr:`INPUT`, :attr:`OUTPUT`,
                     :attr:`INPUT_PULLUP`, or :attr:`INPUT_PULLDOWN`.
        :type mode: int

        .. code-block:: python

            # Set pin 13 as an output for an LED
            hana.set_pin_mode(13, hana.OUTPUT)
            
            # Set pin 2 as an input with a pull-up for a button
            hana.set_pin_mode(2, hana.INPUT_PULLUP)
        """
        self.exec_func(11, pin, mode)


    def read_digital(self, pin: int) -> int:
        """
        Reads the value from a specified digital pin.
        This is equivalent to Arduino's ``digitalRead()``.

        :param pin: The number of the digital pin you want to read.
        :type pin: int
        :return: The state of the pin, either :attr:`HIGH` (1) or :attr:`LOW` (0).
        :rtype: int

        .. code-block:: python
        
            button_state = hana.read_digital(2)
            if button_state == hana.LOW:
                print("Button is pressed!")
        """
        return int(self.exec_func(12, pin))
    


    def write_digital(self, pin: int, status: int):
        """
        Write a HIGH or a LOW value to a digital pin.
        This is equivalent to Arduino's ``digitalWrite()``.

        :param pin: The number of the pin to write to.
        :type pin: int
        :param status: The value to write, either :attr:`HIGH` or :attr:`LOW`.
        :type status: int

        .. code-block:: python

            # Turn an LED on
            hana.write_digital(13, hana.HIGH)
            time.sleep(1)
            # Turn the LED off
            hana.write_digital(13, hana.LOW)
        """
        self.exec_func(13, pin, status)



    def read_analog(self, pin: int) -> int:
        """
        Reads the value from the specified analog pin.
        This is equivalent to Arduino's ``analogRead()``.

        :param pin: The number of the analog input pin to read from (e.g., 26~29 on RP2040).
        :type pin: int
        :return: The analog reading on the pin. The range depends on the ADC
                 resolution (e.g., 0-1023 for 10-bit, 0-4095 for 12-bit).
        :rtype: int
        :seealso: :meth:`set_adc_bits` to change the reading resolution.
        """
        return int(self.exec_func(14, pin))
    

    def set_adc_bits(self, bits: int):
        """
        Sets the resolution for :meth:`read_analog`.
        This is equivalent to ``analogReadResolution()`` on supported boards.

        :param bits: The desired resolution in bits. Common values are 10 (for a
                     range of 0-1023) or 12 (for a range of 0-4095).
        :type bits: int

        .. code-block:: python

            # Set ADC to 12-bit resolution for more precision
            hana.set_adc_bits(12)
            high_res_value = hana.read_analog(26) # Returns a value between 0 and 4095
        """
        self.exec_func(15, bits)



    def write_analog(self, pin: int, duty: int):
        """
        Writes an analog value (PWM wave) to a pin.
        This is equivalent to Arduino's ``analogWrite()``.

        :param pin: The pin to write to.
        :type pin: int
        :param duty: The duty cycle for the PWM signal. The value should be between
                     0 (always off) and the maximum range (default is 255).
        :type duty: int
        :seealso: :meth:`set_pwm_freq`, :meth:`set_pwm_range`
        
        .. code-block:: python

            # Fade an LED to half brightness
            hana.write_analog(9, 128)
        """
        self.exec_func(21, pin, duty)



    def set_pwm_freq(self, pin:int, freq:int):
        """
        Sets the frequency for PWM signals generated by :meth:`write_analog`.

        :param pin: The pin to write to.
        :type pin: int
        :param freq: The desired frequency in Hertz (Hz).
        :type freq: int
        
        .. code-block:: python
        
            # Set PWM frequency to 1 kHz for smoother LED fading
            hana.set_pwm_freq(9, 1000)
        """
        self.exec_func(22, pin, freq)


    def set_pwm_bits(self, pin:int, bits:int):
        """
        Sets the range for the duty cycle used in :meth:`write_analog`.

        :param pin: The pin to write to.
        :type pin: int
        :param bits: The number of bits which defines the
                     PWM resolution (e.g., 8, 10, 12, etc).
        :type bits: int
        
        .. code-block:: python

            # Set PWM resolution to 9-bits
            hana.set_pwm_bits(9, 1023)
            # Now set LED to 50% brightness with the new range
            hana.write_analog(9, 512)
        """
        self.exec_func(23, bits)



    def get_millis(self) -> int: #"""현재 밀리초 단위 시간 반환"""
        """
        Returns the number of milliseconds passed since the board began running.
        This is equivalent to Arduino's ``millis()``.

        :return: The number of milliseconds as an integer.
        :rtype: int
        :note: This number will overflow (go back to zero) after approximately 50 days.
        """
        return int(self.exec_func(31))
    

    '''
    def get_micros(self) -> int:
        """
        Returns the number of microseconds passed since the board began running.
        This is equivalent to Arduino's ``micros()``.

        :return: The number of microseconds as an integer.
        :rtype: int
        :note: This number will overflow (go back to zero) after approximately 70 minutes.
        """
        return int(self.exec_func(32))
    '''


    # 음 발생 관련 함수들
    def start_tone(self, pin: int, freq, duration: int = 0):
        """
        Generates a square wave tone on a pin.
        This is equivalent to Arduino's ``tone()``.

        :param pin: The pin on which to generate the tone.
        :type pin: int
        :param freq: The frequency of the tone in Hertz, or a string representing a
                     musical note (e.g., 'c4', 'a#5', 'db3').
        :type freq: int | str
        :param duration: The duration of the tone in milliseconds. If 0 (default),
                         the tone plays continuously until :meth:`stop_tone` is called.
        :type duration: int
        :raises ValueError: If an unrecognized note string is provided.

        .. code-block:: python

            # Play a 440 Hz 'A' note for 1 second
            hana.start_tone(8, 440, 1000)

            # Play a 'C4' note continuously
            hana.start_tone(8, 'c4')
            time.sleep(2)
            hana.stop_tone(8)
            
        .. code-block:: python

            >>> # Direct frequency specification
            >>> from chaino import Hana
            >>> import time
            >>> hana = Hana("COM9")
            >>> hana.start_tone(8, 440, 1000)  # 440Hz on pin 8 for 1 second
            
            >>> # Note name specification  
            >>> hana.start_tone(8, 'a4', 1000)   # A4 (440Hz) on pin 8 for 1 second
            >>> hana.start_tone(8, 'c#5', 500)   # C#5 on pin 8 for 0.5 seconds
            >>> hana.start_tone(8, 'do')         # Do note on pin 8 infinitely
            
            >>> # Simple melody
            >>> melody = ['do', 're', 'mi', 'fa', 'sol']
            >>> for note in melody:
            ...     hana.start_tone(8, note, 400)
            ...     time.sleep(0.5)
        
        :note: Case insensitive
        """
        if isinstance(freq, str):
            freq_lower = freq.lower()
            if freq_lower in _PITCHES: freq = _PITCHES[freq_lower]
            elif freq_lower in _NOTES: freq = _NOTES[freq_lower]
            else: raise ValueError(f"Unknown note: {freq}.")
        
        self.exec_func(41, pin, freq, duration)



    def stop_tone(self, pin: int):
        """
        Stops the tone being generated on a pin.
        This is equivalent to Arduino's ``noTone()``.

        :param pin: The pin on which to stop the tone.
        :type pin: int
        
        .. code-block:: python

            >>> # Start tone
            >>> hana.start_tone(8, 'a4')  # Play A4 note on pin 8 infinitely
            >>> 
            >>> # Do other work...
            >>> time.sleep(2)    # Wait 2 seconds
            >>> 
            >>> # Stop tone
            >>> hana.stop_tone(8)     # Stop tone generation on pin 8
            
            >>> # Create silence between notes in melody
            >>> hana.start_tone(8, 'c4', 500)   # Do note for 0.5 seconds
            >>> hana.stop_tone(8)           # Stop immediately
            >>> time.sleep(1.5)           # 1.5 second silence
            >>> hana.start_tone(8, 'd4', 500)   # Re note for 0.5 seconds
        
        :note:
            - Only needed when start_tone() method's duration parameter is 0.
            - When duration is specified, tone stops automatically, stop_tone() is unnecessary.
        """
        self.exec_func(42, pin)



#=============================================================================================
IS_CPYTHON = (sys.implementation.name == "cpython")

if IS_CPYTHON:
    
    class Hana(_HanaBase, Chaino):
        """
        A high-level interface for controlling a Chaino_Hana board from CPython.

        This class combines the serial communication capabilities of :class:`~chaino.Chaino`
        with the Arduino-like hardware control methods specific to the Chaino_Hana board.

        .. note::
           This class inherits all methods from :class:`~chaino.chaino.Chaino`, 
           such as :meth:`~chaino.chaino.Chaino.ping`, :meth:`~chaino.chaino.Chaino.who`,
           :meth:`~chaino.chaino.Chaino.get_version`, etc. 
           Only Hana-specific methods are listed below.

        :param port: The name of the serial port (e.g., "COM9").
        :type port: str
        :param i2c_addr: The I2C address of the target Chaino_Hana board. If 0 (default),
                         commands are sent to the master device connected via serial.
        :type i2c_addr: int
        """
        def __init__(self, port, i2c_addr: int = 0):
            Chaino.__init__(self, port, i2c_addr)
            
else:
    
    class Hana(_HanaBase, Chaino):
        """
        A high-level interface for controlling a Chaino Hana board from MicroPython.

        This class combines the I2C communication capabilities of :class:`~chaino.Chaino`
        with the Arduino-like hardware control methods specific to the Chaino_Hana board.

        .. note::
           This class inherits all methods from :class:`~chaino.chaino.Chaino`, 
           such as :meth:`~chaino.chaino.Chaino.ping`, :meth:`~chaino.chaino.Chaino.who`,
           :meth:`~chaino.chaino.Chaino.get_version`, etc. 
           Only Hana-specific methods are listed below.

        :param i2c_addr: The I2C address of the target Chaino_Hana slave board.
        :type i2c_addr: int
        """
        def __init__(self, i2c_addr: int):
            # MicroPython용 Chaino는 (slave_addr)만 받는다고 가정
            Chaino.__init__(self, i2c_addr)





if __name__ == "__main__":

    #"""
    h = Hana("COM10",0x40)
    print(h.who())
    print(h.get_version())
    print(f"0x{h.get_addr():02x}")
    #for _ in range(10000): print(h.read_analog(26))
    h.ping()

    #print(h.set_addr(0x40))
    #'''
    import time
    for _ in range(100):
        h.set_neopixel(255,0,0)
        time.sleep(0.1)
        h.set_neopixel(0,0,0)
        time.sleep(0.1)
    #'''
    #"""

    
    #Hana.scan()
