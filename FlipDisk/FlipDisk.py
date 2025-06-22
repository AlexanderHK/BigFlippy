import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import FDProcessing
import PixelBoard
import sys

# Create a 10x10 pixel board
boardSize = (28, 28)
board = PixelBoard.PixelBoard(boardSize[0],boardSize[1])

#load file

if len(sys.argv) > 1:
  print("Displaying: " + sys.argv[1])
else:
    print("No arguments provided.")
file = "TestImages/"+sys.argv[1]
img = Image.open(file)

#process
img=FDProcessing.SimpleBW(img, boardSize)

# Display the board
board.loadImage(img)
#board.PlotLocal()
board.publishImage()
board.refreshDisplay()
board.Shutdown()

