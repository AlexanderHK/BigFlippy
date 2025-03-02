import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import FDProcessing
import PixelBoard



def StartRealtimePixelFlip(pixelboard):
    # Initialize the camera
    #capture state can be edge, bw, or yolo
    captureState=["edge","bw","yolo"]
    currState=0;
    cap = cv2.VideoCapture(0)  # 0 indicates the default camera
    running=True
    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()
        running=False
     
    while(running):
        # Capture a frame
        ret, frame = cap.read()
        
        # Check if the frame was captured successfully
        if ret:
            # Display the frame
            cv2.imshow("Camera Image", frame)
            k = cv2.waitKey(33)
            if k==27:
                running=False# Esc key to stop
                break
            elif k==ord(' '):
                currState+=1
                currState=currState%3 
                
            elif k==-1:  # normally -1 returned,so don't print it
                img = Image.fromarray(frame)
                if captureState[currState] =="edge":
                    img=FDProcessing.EdgeDetection(img, pixelboard.getSize())
                elif captureState[currState] =="bw":
                    img=FDProcessing.SimpleBW(img, pixelboard.getSize())
                elif captureState[currState] =="yolo":
                    img=FDProcessing.yoloSeg(img, pixelboard.getSize())
                
                # Display the board
                pixelboard.clear()
                pixelboard.renderImage(img)
                pixelboard.display()
        
    
    # Release the camera
    cap.release()
    cv2.destroyAllWindows()
    

# Create a pixel board
boardSize = (28, 28)
board = PixelBoard.PixelBoard(boardSize[0],boardSize[1])

StartRealtimePixelFlip(board)


