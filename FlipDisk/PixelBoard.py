# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 17:18:35 2024

@author: bigfl
"""
import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
from BoardFont import BoardFont  # Assuming BoardFont.py is in the same directory
from FDProcessing import SimpleBW, EdgeDetection
#import RS485Interface as ser

#virtual pixelboard
class PixelBoard:

    def __init__(self, width, height, enable_rs485=False):
        self.width = width
        self.height = height
        self.board = np.zeros((height, width), dtype=np.uint8)
        self.FRAME_START = 0x80
        self.CMD_REFRESH_ALL_DISPLAYS = 0x82  # Commit buffers on all panels
        self.CMD_SEND_AND_REFRESH = 0x83      # Write buffer to a panel and commit immediately
        self.CMD_SEND_NO_REFRESH = 0x84       # Write buffer to a panel, but don't commit until we send the refresh command (useful for painting all displays at the same time)
        self.FRAME_END = 0x8F
        self.PANEL_NUM = 4
        self.rs485 = None
        self.rs485_enabled = enable_rs485
        
        # Initialize RS485 interface if requested
        if self.rs485_enabled:
            self._init_rs485_interface()
        
        # Max number of data bytes to be sent for 28x7 controller
        DATA_BYTES = 28
        # Max size of a frame that holds a command for a 28x7 controller
        CMD_FRAME_SIZE = 32
    
    def _init_rs485_interface(self):
        """Initialize RS485 interface with robust error handling"""
        try:
            import RS485Interface as ser
            self.rs485 = ser.RS485Interface()
            print("RS485 interface initialized successfully")
        except ImportError as e:
            print(f"RS485Interface module not available: {e}")
            self.rs485 = None
            self.rs485_enabled = False
        except OSError as e:
            if e.errno == 16:
                print(f"RS485 interface busy, initialization failed: {e}")
            else:
                print(f"RS485 interface initialization failed with OSError: {e}")
            self.rs485 = None
            self.rs485_enabled = False
        except Exception as e:
            print(f"Unexpected error initializing RS485 interface: {e}")
            self.rs485 = None
            self.rs485_enabled = False
    
    def enable_rs485_interface(self):
        """Enable and initialize RS485 interface if not already enabled"""
        if not self.rs485_enabled:
            self.rs485_enabled = True
            self._init_rs485_interface()
            return self.rs485 is not None
        return True
    
    def disable_rs485_interface(self):
        """Disable and cleanup RS485 interface"""
        if self.rs485_enabled and self.rs485 is not None:
            try:
                self.rs485.Close()
            except Exception as e:
                print(f"Error closing RS485 during disable: {e}")
        self.rs485 = None
        self.rs485_enabled = False

    def loadImage(self, image):
        self.clear()
        array=np.array(image)
        if(not np.shape(array)==np.shape(image)):
            print("warning")
            return
        for x in range(0,self.width):
            for y in range(0,self.height):
                if(array[y,x]>0):
                    self.set_pixel(x, y, 1)
                
    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.board[y, x] = color
    def clear(self):
        self.board.fill(0)

    def PlotLocal(self):
        plt.imshow(self.board)
        plt.axis('off')
        plt.show()
    
    def getSize(self):
        return (self.width, self.height)
   
    def publishImage(self):
        if self.rs485_enabled and self.rs485 is not None:
            try:
                if not self.rs485.is_initialized():
                    print("Warning: RS485 interface not initialized, skipping image publish")
                    return
                serialMessage = self.rs485.getSerial(self,2)
                self.rs485.sendMessage(serialMessage)
                self.rs485.sendMessage(serialMessage)
            except Exception as e:
                print(f"Error during image publish: {e}")
        else:
            print("RS485 interface not available, image publish skipped")
        
    def refreshDisplay(self):
        if self.rs485_enabled and self.rs485 is not None:
            try:
                if not self.rs485.is_initialized():
                    print("Warning: RS485 interface not initialized, skipping display refresh")
                    return
                serialMessage = self.rs485.getSerial(self,1)
                self.rs485.sendMessage(serialMessage)
                self.rs485.sendMessage(serialMessage)
            except Exception as e:
                print(f"Error during display refresh: {e}")
        else:
            print("RS485 interface not available, display refresh skipped")
            
    def Shutdown(self):
        if self.rs485_enabled and self.rs485 is not None:
            try:
                self.rs485.Close()
                print("RS485 interface closed successfully")
            except Exception as e:
                print(f"Error closing RS485 interface: {e}")
        else:
            print("No RS485 interface to close")

    def WriteOnTop(self, text, font = BoardFont(), y_offset=0, x_offset=0, spacing=1):
        """
        Writes a text string on the top of the board using the provided font.
        :param board: PixelBoard instance
        :param text: String to display
        :param font: BoardFont instance (with CHARACTER_FONT attribute)
        :param y_offset: Vertical offset from the top (default 0)
        :param x_offset: Horizontal offset from the left (default 0)
        :param spacing: Number of blank columns between characters (default 1)
        """

        char_height = 5
        char_width = 3

        max_chars = (self.width - x_offset + spacing) // (char_width + spacing)
        if len(text) > max_chars:
            print(f"Warning: Text too long for board width, truncating to {max_chars} characters.")
            text = text[:max_chars]

        for idx, char in enumerate(text):
            char = char.upper()
            char_matrix = font.font.get(char)
            if char_matrix is None:
                print(f"Warning: Character '{char}' not in font, skipping.")
                continue

            x_start = x_offset + idx * (char_width + spacing)
            if x_start + char_width > self.width:
                print("Reached board edge, stopping text rendering.")
                break

            for y in range(char_height):
                for x in range(char_width):
                    if y + y_offset < self.height and x_start + x < self.width:
                        self.set_pixel(x_start + x, y + y_offset, char_matrix[y][x])


                
            
        
