import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import FDProcessing
import PixelBoard

# Create a 10x10 pixel board
boardSize = (28, 28)
board = PixelBoard.PixelBoard(boardSize[0],boardSize[1])

#load file
file = "TestImages/eye.png"
img = Image.open(file)

#process
img=FDProcessing.SimpleBW(img, boardSize)

# Display the board
board.loadImage(img)
board.PlotLocal()
board.publishImage()
board.refreshDisplay()

