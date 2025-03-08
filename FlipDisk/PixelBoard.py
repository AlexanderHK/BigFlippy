# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 17:18:35 2024

@author: bigfl
"""
import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import RS485Interface as ser

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
        self.rs485 = ser.RS485Interface()
        
        # Max number of data bytes to be sent for 28x7 controller
        DATA_BYTES = 28
        # Max size of a frame that holds a command for a 28x7 controller
        CMD_FRAME_SIZE = 32

    def loadImage(self, image):
        array=np.array(image)
        if(not np.shape(array)==np.shape(image)):
            print("warning")
            return;
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
        serialMessage = self.rs485.getSerial(self,2)
        print(serialMessage)
        #self.rs485.sendMessage(serialMessage)
        
    def refreshDisplay(self):
        serialMessage = self.rs485.getSerial(self,1)
        print(serialMessage)
        #self.rs485.sendMessage(serialMessage)

                
            
        
