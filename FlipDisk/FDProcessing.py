# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 17:55:29 2024

@author: bigfl
"""

import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import ultralytics
from ultralytics import YOLO



def SimpleBW(img,newsize, invert=False):
    # Crop the center of the image
    width, height = img.size   # Get dimensions
    WH=min(width, height)
    left = (width - WH)/2
    top = (height - WH)/2
    right = (width + WH)/2
    bottom = (height + WH)/2
    img = img.crop((left, top, right, bottom))

    #Convert to black and white
    img=img.convert("1")
    
    if invert:
        # Invert the image colors
        img = Image.eval(img, lambda x: 255 - x)
    #downsample image
    img = img.resize(newsize)
    return img

def EdgeDetection(img,newsize):
    # Crop the center of the image
    width, height = img.size  
    # Get dimensions
    WH=min(width, height)
    left = (width - WH)/2
    top = (height - WH)/2
    right = (width + WH)/2
    bottom = (height + WH)/2
    img = img.crop((left, top, right, bottom))
    
    cvImg=np.array(img)
    #Edge detection 
    # Convert the image to grayscale
    gray = cv2.cvtColor(cvImg, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Use the Canny edge detector
    edges = cv2.Canny(blurred, 100, 200)
    img = Image.fromarray(edges) 
    #Image.fromarray(color_coverted) 
    #downsample image
    img = img.resize(newsize)
    return img

def yoloSeg(img,newsize):
    ultralytics.checks()
    # Load a model
    # You can use different YOLOv8 variants (yolov8n-seg, yolov8s-seg, yolov8m-seg, yolov8l-seg, yolov8nx-seg)
    model = YOLO('yolov8n-seg.pt')  # load a pretrained model
    # Use the model
    results = model(img)  # predict on an image
    
    #add all the masks to single array
    maskImg=np.zeros(np.shape(results[0].masks.data[0].numpy()),dtype=("uint8"))
    for r in results[0].masks.data:
        maskImg+=(r.numpy()*255).astype("uint8")
    img = Image.fromarray(maskImg)
    
    # Crop the center of the image
    width, height = img.size  
    # Get dimensions
    WH=min(width, height)
    left = (width - WH)/2
    top = (height - WH)/2
    right = (width + WH)/2
    bottom = (height + WH)/2
    img = img.crop((left, top, right, bottom))
    
    #downsample image
    img = img.resize(newsize)
    return img
