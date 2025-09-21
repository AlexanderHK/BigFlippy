# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 17:18:35 2024

@author: bigfl
"""
import numpy as np
import serial
import gpiod
from gpiod.line import Direction, Value
import PixelBoard as PB




  
    
   
 

class RS485Interface:

    def __init__(self):
        self.EN_485 = 4
        self.request = None
        self.t = None
        
        # Initialize GPIO with retry logic
        self._init_gpio_with_retry()
        
        # Initialize serial connection
        self._init_serial_with_retry()
        
    def _init_gpio_with_retry(self, max_retries=3):
        """Initialize GPIO with retry logic for OSError 16 (Device or resource busy)"""
        import time
        
        for attempt in range(max_retries):
            try:
                gpiod.is_gpiochip_device("/dev/gpiochip4")
                self.request = gpiod.request_lines(
                     "/dev/gpiochip4",
                     consumer="rs485-interface",
                     config={
                         self.EN_485: gpiod.LineSettings(
                             direction=Direction.OUTPUT, output_value=Value.ACTIVE
                         )
                     },
                )
                print(f"GPIO initialized successfully on attempt {attempt + 1}")
                return
                
            except OSError as e:
                if e.errno == 16:  # Device or resource busy
                    print(f"GPIO busy (attempt {attempt + 1}/{max_retries}): {e}")
                    
                    # Try to cleanup any existing GPIO connections
                    self._cleanup_gpio_connections()
                    
                    if attempt < max_retries - 1:
                        print(f"Retrying GPIO initialization in 1 second...")
                        time.sleep(1)
                    else:
                        print("Failed to initialize GPIO after all retries")
                        raise
                else:
                    # Different OSError, re-raise immediately
                    print(f"GPIO initialization failed with OSError: {e}")
                    raise
            except Exception as e:
                print(f"Unexpected error during GPIO initialization: {e}")
                raise
    
    def _cleanup_gpio_connections(self):
        """Attempt to cleanup any existing GPIO connections"""
        try:
            # If we have an existing request, try to close it
            if hasattr(self, 'request') and self.request is not None:
                self.request.release()
                self.request = None
                print("Released existing GPIO request")
                
            # Additional cleanup - try to reset the GPIO chip
            import subprocess
            try:
                # This is a more aggressive approach - reset GPIO state
                subprocess.run(['sudo', 'systemctl', 'restart', 'gpio'], 
                             capture_output=True, timeout=5)
                print("Attempted GPIO service restart")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                # Service restart failed or not available, continue anyway
                pass
                
        except Exception as e:
            print(f"Warning: GPIO cleanup failed: {e}")
    
    def _init_serial_with_retry(self, max_retries=3):
        """Initialize serial connection with retry logic"""
        import time
        
        for attempt in range(max_retries):
            try:
                self.t = serial.Serial("/dev/ttyAMA0", 19200)
                print(f"Serial initialized successfully: {self.t.portstr}")
                return
                
            except serial.SerialException as e:
                print(f"Serial initialization failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print("Retrying serial initialization in 1 second...")
                    time.sleep(1)
                else:
                    print("Failed to initialize serial after all retries")
                    raise
            except Exception as e:
                print(f"Unexpected error during serial initialization: {e}")
                raise
    
    def binary_to_hex_byte(self, binary_str):

        """Convert an 8-bit binary string to a bytes object."""
        if len(binary_str) != 8 or not all(bit in '01' for bit in binary_str):
            raise ValueError("Input must be an 8-bit binary string")
        #print(bytes([int(binary_str, 2)]))
        return bytes([int(binary_str, 2)]) 

    def getSerial(self,vBoard, command):
        serialArr=list()
        for x in range(0, vBoard.PANEL_NUM):
            serialArr.append(b'\x80') 
        match command:
        
            #send update to all panels to refresh
            case 1:
                serialArr=list()
                serialArr.append(b'\x80\x82\x8F')
                return serialArr
             
            # update panel values but dont refresh
            case 2:
                for x in range(0, vBoard.PANEL_NUM):
                    serialArr[x]+=b'\x83'
                    serialArr[x]+=(vBoard.PANEL_NUM-x).to_bytes(1, byteorder='big')
                    
                    
            #update panel values and refresh immediately
            case 3:
                for x in range(0, vBoard.PANEL_NUM):
                    serialArr[x]+=b'\x84'
            case _:
                print("invalid command")
                
        for y in range(0, len(serialArr)):
            binString=''
            for i in range(0,28):
                binString = '0'+str(vBoard.board[i,y*7+0])+str(vBoard.board[i,y*7+1])+str(vBoard.board[i,y*7+2])+str(vBoard.board[i,y*7+3])+str(vBoard.board[i,y*7+4])+str(vBoard.board[i,y*7+5])+str(vBoard.board[i,y*7+6])
                serialArr[y]+=self.binary_to_hex_byte(binString)
            serialArr[y]+=b'\x8F'
        return serialArr
    
    def is_initialized(self):
        """Check if both GPIO and serial are properly initialized"""
        return self.request is not None and self.t is not None
    
    def sendMessage(self, byteArr):
        if not self.is_initialized():
            raise RuntimeError("RS485 interface not properly initialized")
        
        try:
            for x in range(0, len(byteArr)):
                self.t.write(byteArr[x])
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
            # Attempt to reinitialize serial connection
            try:
                self._init_serial_with_retry(max_retries=1)
                # Retry the send operation once
                for x in range(0, len(byteArr)):
                    self.t.write(byteArr[x])
            except Exception as retry_error:
                print(f"Failed to recover serial connection: {retry_error}")
                raise
           
    def Close(self):
        """Properly cleanup both serial and GPIO resources"""
        try:
            if self.t is not None:
                self.t.close()
                self.t = None
                print("Serial connection closed")
        except Exception as e:
            print(f"Error closing serial connection: {e}")
            
        try:
            if self.request is not None:
                self.request.release()
                self.request = None
                print("GPIO request released")
        except Exception as e:
            print(f"Error releasing GPIO request: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup on object deletion"""
        self.Close()
