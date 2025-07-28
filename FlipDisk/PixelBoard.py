# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 17:18:35 2024

@author: bigfl
"""
import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
from Weather import Weather  # Assuming Weather.py is in the same directory
from BoardFont import BoardFont  # Assuming BoardFont.py is in the same directory
from FDProcessing import SimpleBW, EdgeDetection
#import RS485Interface as ser

#virtual pixelboard
class PixelBoard:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = np.zeros((height, width), dtype=np.uint8)
        self.FRAME_START = 0x80
        self.CMD_REFRESH_ALL_DISPLAYS = 0x82  # Commit buffers on all panels
        self.CMD_SEND_AND_REFRESH = 0x83      # Write buffer to a panel and commit immediately
        self.CMD_SEND_NO_REFRESH = 0x84       # Write buffer to a panel, but don't commit until we send the refresh command (useful for painting all displays at the same time)
        self.FRAME_END = 0x8F
        self.PANEL_NUM = 4
        #self.rs485 = ser.RS485Interface()
        
        # Max number of data bytes to be sent for 28x7 controller
        DATA_BYTES = 28
        # Max size of a frame that holds a command for a 28x7 controller
        CMD_FRAME_SIZE = 32

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
    def LoadWeather(self, weather):
        """
        Loads weather data onto the board.
        :param weather: Weather object containing high, low, and status attributes.
        """
        self.clear()
        img = Image.open(f"WeatherImages/{weather.status}.png")  # Load the weather image
        img = SimpleBW(img, self.getSize(), invert=True)  # Convert to black and white
        self.loadImage(img)
        self.WriteOnTop(f"LO   HI", y_offset=0,font=BoardFont(), x_offset=0, spacing=1)
        self.WriteOnTop(f"{weather.low}   {weather.high}", y_offset=6,font=BoardFont(), x_offset=0, spacing=1)
    def clear(self):
        self.board.fill(0)

    def PlotLocal(self):
        plt.imshow(self.board)
        plt.axis('off')
        plt.show()
    
    def getSize(self):
        return (self.width, self.height)
   
    def publishImage(self):
        serialMessage = self.rs485.getSerial(self,2)
        print(serialMessage)
        self.rs485.sendMessage(serialMessage)
        self.rs485.sendMessage(serialMessage)
        
    def refreshDisplay(self):
        serialMessage = self.rs485.getSerial(self,1)
        self.rs485.sendMessage(serialMessage)
        print(serialMessage)
        self.rs485.sendMessage(serialMessage)
    def Shutdown(self):
        self.rs485.Close()

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


                
            
        
