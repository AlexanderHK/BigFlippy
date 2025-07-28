import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import FDProcessing
import PixelBoard
import CycleMode
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
from global_state import boardSize, board

class Mode(Enum):
    IMAGE_CYCLE = 0
    WEATHER = 1
    PONG = 2
    STANDBY = 3

#run plotted version
run_in_plot = True
#==================================================================
#                   Weather mode Variables
#==================================================================
WEATHER_START_TIME = "06:30"  # Start time for weather mode
WEATHER_END_TIME = "9:30"  # End time for weather mode
WEATHER_IMAGE_DIRECTORY = "WeatherImages/"  # Directory where images are stored

def Run():
  #set the mode first, default is mode 0 
  mode = Mode.IMAGE_CYCLE
  running = True
  # Create a 10x10 pixel board


  #variables
  last_image= ""
  current_day = datetime.now().strftime("%A")  # Get the current day of the week
  print("day: ", datetime.now().strftime("%A"))
  weather = Weather()  # Initialize the weather object
  last_time = time.time()
  
  input_queue = queue.Queue()

  CycleMode.loadContentObjects(boardSize)

  thread = threading.Thread(target=input_thread, args=(input_queue,), daemon=True)
  thread.start()
  
  # Main loop
  while running:
      current_time = time.time()
      
      if current_day != datetime.now().strftime("%A"):
          # If the day has changed, update the current weather 
          print("day: ", datetime.now().strftime("%A"))
          current_day = datetime.now().strftime("%A")
          current_image_name = f"{current_day}.png"
          weather.getWeather()  # Fetch the latest weather data

      
      if IsTimeBetween(WEATHER_START_TIME, WEATHER_END_TIME):
          mode = Mode.WEATHER
      elif mode == Mode.PONG:
          mode = Mode.PONG
      else:
          mode = Mode.IMAGE_CYCLE

      if IsTimeBetween(CycleMode.SLEEP_START,"23:59") and IsTimeBetween("00:00",WEATHER_START_TIME):
          mode = Mode.STANDBY

      if mode == Mode.IMAGE_CYCLE:
          # Load and display the image
            CycleMode.cycle(current_time, run_in_plot)

      elif mode == Mode.WEATHER:
          board.LoadWeather(weather)
          if not run_in_plot:
           board.publishImage()
           board.refreshDisplay()
          else:
           board.PlotLocal()

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

#==================================================================
#                   Helper functions
#==================================================================
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
