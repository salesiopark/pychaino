if __name__ == "__main__":
    from chaino import Chaino
else:
    from .chaino import Chaino          # CPython 패키지 환경

import sys, time


_PITCHES = {
    # 옥타브 0
    "b0": 31,
    # 옥타브 1
    "c1": 33, "c#1": 35, "db1": 35, "d1": 37, "d#1": 39, "eb1": 39,
    "e1": 41, "f1": 44, "f#1": 46, "gb1": 46, "g1": 49, "g#1": 52, "ab1": 52,
    "a1": 55, "a#1": 58, "bb1": 58, "b1": 62,
    # 옥타브 2
    "c2": 65, "c#2": 69, "db2": 69, "d2": 73, "d#2": 78, "eb2": 78,
    "e2": 82, "f2": 87, "f#2": 93, "gb2": 93, "g2": 98, "g#2": 104, "ab2": 104,
    "a2": 110, "a#2": 117, "bb2": 117, "b2": 123,
    # 옥타브 3
    "c3": 131, "c#3": 139, "db3": 139, "d3": 147, "d#3": 156, "eb3": 156,
    "e3": 165, "f3": 175, "f#3": 185, "gb3": 185, "g3": 196, "g#3": 208, "ab3": 208,
    "a3": 220, "a#3": 233, "bb3": 233, "b3": 247,
    # 옥타브 4 (중간 옥타브)
    "c4": 262, "c#4": 277, "db4": 277, "d4": 294, "d#4": 311, "eb4": 311,
    "e4": 330, "f4": 349, "f#4": 370, "gb4": 370, "g4": 392, "g#4": 415, "ab4": 415,
    "a4": 440, "a#4": 466, "bb4": 466, "b4": 494,
    # 옥타브 5
    "c5": 523, "c#5": 554, "db5": 554, "d5": 587, "d#5": 622, "eb5": 622,
    "e5": 659, "f5": 698, "f#5": 740, "gb5": 740, "g5": 784, "g#5": 831, "ab5": 831,
    "a5": 880, "a#5": 932, "bb5": 932, "b5": 988,
    # 옥타브 6
    "c6": 1047, "c#6": 1109, "db6": 1109, "d6": 1175, "d#6": 1245, "eb6": 1245,
    "e6": 1319, "f6": 1397, "f#6": 1480, "gb6": 1480, "g6": 1568, "g#6": 1661, "ab6": 1661,
    "a6": 1760, "a#6": 1865, "bb6": 1865, "b6": 1976,
    # 옥타브 7
    "c7": 2093, "c#7": 2217, "db7": 2217, "d7": 2349, "d#7": 2489, "eb7": 2489,
    "e7": 2637, "f7": 2794, "f#7": 2960, "gb7": 2960, "g7": 3136, "g#7": 3322, "ab7": 3322,
    "a7": 3520, "a#7": 3729, "bb7": 3729, "b7": 3951,
    # 옥타브 8
    "c8": 4186, "c#8": 4435, "db8": 4435, "d8": 4699, "d#8": 4978, "eb8": 4978,
}

# 자주 사용되는 음계별 별칭 추가
_NOTES = {
    # 도레미파솔라시도 (C major scale)
    "do": _PITCHES["c4"],    # 도
    "re": _PITCHES["d4"],    # 레  
    "mi": _PITCHES["e4"],    # 미
    "fa": _PITCHES["f4"],    # 파
    "sol": _PITCHES["g4"],   # 솔
    "la": _PITCHES["a4"],    # 라
    "si": _PITCHES["b4"],    # 시
    # 영어식 음명 (4옥타브 기준)
    "c": _PITCHES["c4"],
    "d": _PITCHES["d4"],
    "e": _PITCHES["e4"],
    "f": _PITCHES["f4"],
    "g": _PITCHES["g4"],
    "a": _PITCHES["a4"],
    "b": _PITCHES["b4"],
}


class _HanaCommon:
    """Common constants and methods for controlling Chaino_Hana device.
    
    This class defines Arduino-compatible constants and methods that work
    across different Python implementations (CPython and MicroPython).
    """
    HIGH = 1
    LOW = 0
    
    INPUT = 0
    OUTPUT = 1
    INPUT_PULLUP = 2
    INPUT_PULLDOWN = 3


    def set_pin_mode(self, pin: int, mode: int):
        """Configure the specified pin to behave as an input or output.
        
        This method provides the same functionality as Arduino's pinMode() function.
        
        Args:
            pin (int): The pin number to configure (0-40 depending on board)
            mode (int): The pin mode to set
                - INPUT (0): Configure as input pin
                - OUTPUT (1): Configure as output pin
                - INPUT_PULLUP (2): Configure as input with internal pull-up resistor
                - INPUT_PULLDOWN (3): Configure as input with internal pull-down resistor
        
        Example:
            >>> from chaino import Hana
            >>> hana = Hana("COM9")
            >>> hana.set_pin_mode(13, hana.OUTPUT)     # Set pin 13 as output
            >>> hana.set_pin_mode(2, hana.INPUT)       # Set pin 2 as input
            >>> hana.set_pin_mode(3, hana.INPUT_PULLUP) # Set pin 3 as input with pull-up
        
        Note:
            - Pin mode must be set before using the pin for digital I/O operations
            - Pull-up/pull-down modes eliminate the need for external resistors
            - Not all pins support all modes (depends on hardware capabilities)
        """
        self.exec_func(11, pin, mode)


    def read_digital(self, pin: int) -> int:
        """Read the digital value from the specified pin.
        
        This method provides the same functionality as Arduino's digitalRead() function.
        
        Args:
            pin (int): The pin number to read from
            
        Returns:
            int: Digital value (HIGH/1 or LOW/0)
            
        Example:
            >>> # Read button state
            >>> hana.set_pin_mode(2, Hana.INPUT_PULLUP)
            >>> button_state = hana.read_digital(2)
            >>> if button_state == Hana.LOW:
            ...     print("Button pressed!")
            
            >>> # Read sensor output
            >>> sensor_value = hana.read_digital(7)
            >>> print(f"Sensor state: {'HIGH' if sensor_value else 'LOW'}")
        
        Note:
            - Pin must be configured as INPUT, INPUT_PULLUP, or INPUT_PULLDOWN first
            - Returns 1 (HIGH) for voltages above ~2.5V, 0 (LOW) for voltages below ~1.5V
            - For analog readings, use read_analog() instead
        """
        return int(self.exec_func(12, pin))
    


    def write_digital(self, pin: int, status: int):
        """Write a digital value (HIGH or LOW) to the specified pin.
        
        This method provides the same functionality as Arduino's digitalWrite() function.
        
        Args:
            pin (int): The pin number to write to
            status (int): Digital value to write (HIGH/1 or LOW/0)
            
        Example:
            >>> # Control LED
            >>> hana.set_pin_mode(13, Hana.OUTPUT)
            >>> hana.write_digital(13, Hana.HIGH)  # Turn LED on
            >>> time.sleep(1)
            >>> hana.write_digital(13, Hana.LOW)   # Turn LED off
            
            >>> # Control relay
            >>> hana.set_pin_mode(8, Hana.OUTPUT)
            >>> hana.write_digital(8, 1)  # Activate relay
        
        Note:
            - Pin must be configured as OUTPUT first using set_pin_mode()
            - For PWM output, use write_analog() instead
        """
        self.exec_func(13, pin, status)



    def read_analog(self, pin: int) -> int:
        """Read the analog value from the specified pin.
        
        This method provides the same functionality as Arduino's analogRead() function.
        
        Args:
            pin (int): The analog pin number to read from (26,27,28,29 for RP2040)
            
        Returns:
            int: Analog value (0-1023 for 10-bit ADC, 0-4095 for 12-bit ADC)
            
        Example:
            >>> # Read potentiometer value
            >>> pot_value = hana.read_analog(0)  # Read from A0
            >>> voltage = (pot_value / 1023.0) * 3.3  # Convert to voltage
            >>> print(f"Potentiometer: {pot_value} ({voltage:.2f}V)")
            
            >>> # Read temperature sensor
            >>> temp_raw = hana.read_analog(1)
            >>> # Convert based on sensor specifications
            >>> temperature = (temp_raw * 3.3 / 1023.0 - 0.5) * 100
            >>> print(f"Temperature: {temperature:.1f}°C")
        
        Note:
            - No need to set pin mode for analog pins
            - Resolution depends on the ADC resolution (10-bit = 0-1023, 12-bit = 0-4095)
            - Input voltage range is typically 0V to VCC (3.3V or 5V)
            - For setting resolution, use set_adc_resolution() method
        """
        return int(self.exec_func(14, pin))
    

    def set_adc_bits(self, bits: int):
        """Set the ADC resolution for analog readings.
        
        This method allows changing the resolution of analog readings.
        Supported resolutions are 10-bit (default) and 12-bit.
        
        Args:
        bits (int): Resolution in bits (8, 10, 12, etc.)
                   - 8 bits resolution : range 0~255
                   - 10 bits resolution : range 0~1023 (default for RP2040)
                   - 12 bits resolution : range 0~4095 (maximum for RP2040)
        
        Example:
            >>> hana.set_adc_bits(12)  # Set to 12-bit resolution
            >>> value = hana.read_analog(26)  # Now returns 0-4095
            
            >>> hana.set_adc_bits(10)  # Set back to 10-bit resolution
            >>> value = hana.read_analog(27)  # Returns 0-1023
        
        Note:
            - Default resolution is usually 10-bit, change only if needed
            - Affects all subsequent read_analog() calls
        """
        self.exec_func(15, bits)



    def write_analog(self, pin: int, duty: int):
        """Output PWM signal with specified duty cycle.
        
        Outputs a PWM (Pulse Width Modulation) signal on the specified pin
        with the given duty cycle value.
        
        Args:
            pin (int): GPIO pin number (0-28 for RP2040)
            duty (int): PWM duty cycle value
                Range: 0 to current PWM range (default 0-255)
                * 0 = 0% duty cycle (always LOW)
                * pwm_range/2 = 50% duty cycle  
                * pwm_range = 100% duty cycle (always HIGH)
        
        Returns:
            None
        
        Note:
            - Default frequency: 1000Hz (1kHz)
            - Default range: 0-255 (8-bit)
            - Use set_pwm_freq() to change frequency
            - Use set_pwm_range() to change duty cycle range
            - All GPIO pins on RP2040 support PWM
        
        Example:
            >>> # Basic PWM output (default 1kHz, 0-255 range)
            >>> self.write_analog(25, 128)  # 50% duty cycle on built-in LED
            
            >>> # With custom frequency and range
            >>> self.set_pwm_freq(15, 2000)    # 2kHz frequency
            >>> self.set_pwm_range(15, 1023)   # 10-bit resolution
            >>> self.write_analog(15, 256)     # 25% duty cycle
        """
        self.exec_func(21, pin, duty)



    def set_pwm_freq(self, pin:int, freq:int):
        """Set PWM frequency for specified pin.
    
        Sets the PWM frequency for the specified pin. This affects all PWM pins
        on the same PWM slice in RP2040.
        
        Args:
            pin (int): GPIO pin number (0-28 for RP2040)
            freq (int): PWM frequency in Hz (typically 100Hz - 40kHz)
                Default frequency is 1000Hz (1kHz)
        
        Returns:
            None
        
        Note:
            - RP2040 has 8 PWM slices, each controlling 2 pins
            - Pins on the same slice share the same frequency
            - Higher frequencies reduce PWM resolution
            - Recommended frequencies:
                * LEDs: 1kHz - 5kHz
                * Motors: 20kHz+  
                * Servos: 50Hz
        
        Example:
            >>> # Set PWM frequency to 2kHz for pin 15
            >>> self.set_pwm_freq(15, 2000)
            >>> # Set servo frequency (50Hz) for pin 14  
            >>> self.set_pwm_freq(14, 50)
        """
        self.exec_func(22, pin, freq)



    def set_pwm_range(self, pwm_range:int):
        """Set PWM duty cycle range for specified pin.
        
        Sets the maximum value for PWM duty cycle on the specified pin.
        This determines the resolution of PWM control.
        
        Args:
            pin (int): GPIO pin number (0-28 for RP2040)
            pwm_range (int): Maximum duty cycle value
                Common ranges:
                * 255 (8-bit, default)
                * 1023 (10-bit)  
                * 4095 (12-bit)
                * 65535 (16-bit)
        
        Returns:
            None
        
        Note:
            - Default range is 255 (8-bit resolution)
            - Higher ranges provide finer control but may reduce max frequency
            - Range applies to analogWrite() duty cycle values
            - 0 = 0% duty cycle, pwm_range = 100% duty cycle
        
        Example:
            >>> # Set 10-bit resolution (0-1023)
            >>> self.set_pwm_range(15, 1023)
            >>> # Now use analogWrite with 0-1023 range
            >>> self.write_analog(15, 512)  # 50% duty cycle
            
            >>> # Set 12-bit resolution (0-4095)  
            >>> self.set_pwm_range(16, 4095)
            >>> self.write_analog(16, 2048)  # 50% duty cycle
        """
        self.exec_func(23, pwm_range)







    def get_millis(self) -> int: #"""현재 밀리초 단위 시간 반환"""
        """Return the current time in milliseconds since program start.
        
        This method provides the same functionality as Arduino's millis() function.
        
        Returns:
            int: Current time in milliseconds
            
        Example:
            >>> # Measure execution time
            >>> start_time = hana.get_millis()
            >>> # ... do some work ...
            >>> execution_time = hana.get_millis() - start_time
            >>> print(f"Execution took {execution_time}ms")
            
            >>> # Non-blocking delay
            >>> previous_time = hana.get_millis()
            >>> while True:
            ...     current_time = hana.get_millis()
            ...     if current_time - previous_time >= 1000:
            ...         print("1 second passed")
            ...         previous_time = current_time
        
        Note:
            - Counter starts at 0 when Chaino_Hana device is powerd in or resetted.
            - Overflows approximately every 50 days (returns to 0)
            - Resolution is 1 millisecond
            - For microsecond precision, use micros() instead
        """
        return int(self.exec_func(31))
    

    
    def get_micros(self) -> int:
        """Return the current time in microseconds since program start.
        
        This method provides the same functionality as Arduino's micros() function.
        
        Returns:
            int: Current time in microseconds
            
        Example:
            >>> # Measure precise timing
            >>> start_time = hana.get_micros()
            >>> # ... do quick operation ...
            >>> execution_time = hana.get_micros() - start_time
            >>> print(f"Operation took {execution_time}µs")
            
            >>> # Generate precise delays
            >>> start = hana.get_micros()
            >>> while hana.get_micros() - start < 1000:  # Wait 1ms
            ...     pass  # Busy wait
        
        Note:
            - Counter starts at 0 when program begins
            - Overflows approximately every 70 minutes (returns to 0)
            - Resolution is 1 microsecond
            - For millisecond timing, use millis() instead
            - More precise but also more CPU intensive than millis()
        """
        return int(self.exec_func(32))
    


    # 음 발생 관련 함수들
    def start_tone(self, pin: int, freq, duration: int = 0):
        """Generate a tone of specified frequency on a digital pin.
        
        This method provides the functionality of Arduino's tone() function,
        supporting both numeric frequencies and string note names.
        
        Args:
            pin (int): The pin number to output the tone
            freq (int or str): Frequency in Hz or note name
                - int: Direct frequency specification (e.g., 440)
                - str: Note name specification (e.g., 'c4', 'a#5', 'do')
            duration (int, optional): Tone duration in milliseconds. 
                Default 0 means infinite duration.
        
        Raises:
            ValueError: When an unknown note name is provided
            
        Example:
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
        
        Note:
            - Supported note names: 'c0'~'c8', sharps('#'), flats('b'), solfege('do'~'si')
            - Case insensitive
            - Duration of 0 plays until no_tone() is called
            - Only one pin can generate tone at a time
        """
        if isinstance(freq, str):
            freq_lower = freq.lower()
            if freq_lower in _PITCHES: freq = _PITCHES[freq_lower]
            elif freq_lower in _NOTES: freq = _NOTES[freq_lower]
            else: raise ValueError(f"Unknown note: {freq}.")
        
        self.exec_func(41, pin, freq, duration)



    def stop_tone(self, pin: int):
        """Stop tone generation on the specified pin.
        
        This method provides the same functionality as Arduino's noTone() function,
        immediately stopping tone generation started by the tone() method.
        
        Args:
            pin (int): The pin number to stop tone generation
            
        Example:
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
        
        Note:
            - Only needed when tone() method's duration parameter is 0.
            - When duration is specified, tone stops automatically, no_tone() is unnecessary.
            - Calling no_tone() on an already stopped pin is harmless and no effect.
        """
        self.exec_func(42, pin)




#=============================================================================================
IS_CPYTHON = (sys.implementation.name == "cpython")

if IS_CPYTHON:
    
    class Hana(_HanaCommon, Chaino):
        """CPython: Chaino(port, i2c_addr=0) 시그니처 가정"""
        def __init__(self, port, i2c_addr: int = 0):
            Chaino.__init__(self, port, i2c_addr)
            
else:
    
    class Hana(_HanaCommon, Chaino):
        """MicroPython: Chaino(slave_addr:int) 시그니처 가정"""
        def __init__(self, i2c_addr: int):
            # MicroPython용 Chaino는 (slave_addr)만 받는다고 가정
            Chaino.__init__(self, i2c_addr)





if __name__ == "__main__":

    h = Hana("COM9")
    print(h.who())
    print(h.get_version())
    print(h.get_addr())
    #for _ in range(10000): print(h.read_analog(26))
    h.ping()
