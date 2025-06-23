import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import FDProcessing
import PixelBoard
import sys
from enum import Enum
import os 
import random
from datetime import datetime
from Weather import Weather  # Assuming Weather.py is in the same directory
import time
import queue
import threading
import queue

class Mode(Enum):
    IMAGE_CYCLE = 0
    WEATHER = 1
    PONG = 2
    STANDBY = 3

#Cycle mode Variables
IMAGE_CYCLE_TIME = 5  # Time in seconds for image cycle mode
CYCLE_IMAGE_DIRECTORY = "TestImages/"  # Directory where images are stored
SLEEP_START = "10:00"

#Weather mode Variables
WEATHER_START_TIME = "06:30"  # Start time for weather mode
WEATHER_END_TIME = "9:30"  # End time for weather mode
WEATHER_IMAGE_DIRECTORY = "WeatherImages/"  # Directory where images are stored

def Run():
  #set the mode first, default is mode 0 
  mode = Mode.IMAGE_CYCLE
  running = True
  # Create a 10x10 pixel board
  boardSize = (28, 28)
  board = PixelBoard.PixelBoard(boardSize[0],boardSize[1])

  #variables
  last_image= ""
  current_day = datetime.now().strftime("%A")  # Get the current day of the week
  weather = Weather()  # Initialize the weather object
  last_time = time.time()
  
  input_queue = queue.Queue()

  thread = threading.Thread(target=input_thread, args=(input_queue,), daemon=True)
  thread.start()
  
  # Main loop
  while running:
      current_time = time.time()
      
      if current_day != datetime.now().strftime("%A"):
          # If the day has changed, update the current weather 
          current_day = datetime.now().strftime("%A")
          current_image_name = f"{current_day}.png"
          weather.getWeather()  # Fetch the latest weather data

      
      if IsTimeBetween(WEATHER_START_TIME, WEATHER_END_TIME):
          mode = Mode.WEATHER
      elif mode == Mode.PONG:
          mode = Mode.PONG
      else:
          mode = Mode.IMAGE_CYCLE
      if IsTimeBetween(SLEEP_START,"23:59") and IsTimeBetween("00:00",WEATHER_START_TIME):
          mode = Mode.STANDBY


      if mode == Mode.IMAGE_CYCLE:
          # Load and display the image
          image_files = [f for f in os.listdir(CYCLE_IMAGE_DIRECTORY) if os.path.isfile(os.path.join(CYCLE_IMAGE_DIRECTORY, f))]
          current_image = os.path.join(CYCLE_IMAGE_DIRECTORY, random.choice(image_files))
          if current_time - last_time >= IMAGE_CYCLE_TIME and current_image != last_image:

              img = Image.open(current_image)
              img = FDProcessing.SimpleBW(img, boardSize)
              board.loadImage(img)
              #board.PlotLocal()
              board.publishImage()
              board.refreshDisplay()
              last_time = current_time
              last_image = current_image

      elif mode == Mode.WEATHER:
          board.LoadWeather(weather)
          #board.PlotLocal()
          board.publishImage() 
          board.refreshDisplay()

      elif mode == Mode.PONG:
          # Placeholder for pong game logic
          print("Pong mode not implemented yet.")

      elif mode == Mode.STANDBY:
          print("Waiting for next mode change")

      try:
            user_input = input_queue.get_nowait()
            if user_input.lower() == 'exit':
                running = False
            elif user_input.lower() == 'next':
                print("ye")
      except queue.Empty:
            pass
  board.Shutdown()

def IsTimeBetween(start_time_str, end_time_str):
    """
    Returns True if the current time is between start_time and end_time (24-hour format 'HH:MM').
    """
    now = datetime.now().time()
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    end_time = datetime.strptime(end_time_str, "%H:%M").time()
    if start_time <= end_time:
        return start_time <= now <= end_time
    else:
        # Over midnight
        return now >= start_time or now <= end_time
    
def input_thread(q):
    while True:
        user_input = input("Enter 'next' to change mode, 'exit' to quit: ")
        q.put(user_input)

    thread = threading.Thread(target=input_thread, args=(input_queue,), daemon=True)
    thread.start()
Run()
