# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 17:18:35 2024

@author: bigfl
"""
import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance


class PixelBoard:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = np.zeros((height, width, 3), dtype=np.uint8)

    def renderImage(self, image):
        array=np.array(image)
        if(not np.shape(array)==np.shape(image)):
            print("warning")
            return;
        for x in range(0,self.width):
            for y in range(0,self.width):
                if(array[y,x]>0):
                    self.set_pixel(x, y, (255,255,255))
                
    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.board[y, x] = color

    def clear(self):
        self.board.fill(0)

    def display(self):
        plt.imshow(self.board)
        plt.axis('off')
        plt.show()
    
    def getSize(self):
        return (self.width, self.height)
    

                
            
        
