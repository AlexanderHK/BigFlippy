import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import FDProcessing
import PixelBoard
from Modes.CycleMode import CycleMode
from Modes.WeatherMode import WeatherMode
from Modes.StandbyMode import StandbyMode
import sys
from enum import Enum
import os 
import random
from datetime import datetime
import time
import queue
import threading
import queue
from global_state import boardSize, board
from Modes.WeatherMode import WEATHER_START_TIME, WEATHER_END_TIME
from Modes.CycleMode import SLEEP_START

class Mode(Enum):
    IMAGE_CYCLE = 0
    WEATHER = 1
    PONG = 2
    STANDBY = 3

#run plotted version
run_in_plot = False



#==================================================================
#                   Helper functions
#==================================================================
def IsTimeBetween(start_time_str, end_time_str):
    """
    Returns True if the current time is between start_time and end_time (24-hour format 'HH:MM').
    Handles intervals that cross midnight.
    """
    now = datetime.now().time()
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    end_time = datetime.strptime(end_time_str, "%H:%M").time()
    if start_time < end_time:
        return start_time <= now < end_time
    else:
        # Interval crosses midnight
        return now >= start_time or now < end_time
    
def input_thread(q):
    while True:
        user_input = input("Enter 'next' to change mode, 'exit' to quit: ")
        q.put(user_input)
    
def get_current_mode():
    now = datetime.now().time()
    if IsTimeBetween(WEATHER_START_TIME, WEATHER_END_TIME):
        return WeatherMode()
    elif IsTimeBetween(SLEEP_START, "23:59") or IsTimeBetween("00:00", WEATHER_START_TIME):
        return StandbyMode()
    else:
        return CycleMode()
    
#====================================================================
#                          Main Run loop
#====================================================================


def Run(run_in_plot=False):
    running = True
    input_queue = queue.Queue()
    force_mode = None
    mode_thread = None

    def input_thread(q):
        while True:
            user_input = input("Enter 'force <mode>' to change mode, 'exit' to quit: ")
            q.put(user_input)

    thread = threading.Thread(target=input_thread, args=(input_queue,), daemon=True)
    thread.start()

    mode = get_current_mode()
    mode_thread = threading.Thread(target=mode.run, kwargs={'run_in_plot': run_in_plot}, daemon=True)
    mode_thread.start()

    while running:
        # Check for user input asynchronously
        try:
            user_input = input_queue.get(timeout=0.1)
            user_input_lower = user_input.lower()

            if user_input_lower == 'exit':
                running = False
                mode.shutdown()

            elif user_input_lower.startswith('force '):
                arg = user_input_lower.split(' ', 1)[1]
                #======================================
                #             Define Modes
                #======================================
                if arg == 'weather':
                    new_mode = WeatherMode()
                elif arg == 'cycle':
                    new_mode = CycleMode()
                elif arg == 'standby':
                    new_mode = StandbyMode()
                else:
                    print(f"Unknown mode: {arg}")
                    continue

                force_mode = type(new_mode)
                mode.shutdown()

                if mode_thread and mode_thread.is_alive():
                    mode_thread.join(timeout=1)

                mode = new_mode
                mode_thread = threading.Thread(target=mode.run, kwargs={'run_in_plot': run_in_plot}, daemon=True)
                mode_thread.start()
                print(f"Forced mode: {type(mode).__name__}")

            elif user_input_lower == 'release':
                force_mode = None
                print("Released forced mode. Returning to automatic mode switching.")
            
            else:
                mode.receive_data(user_input)
                
        except queue.Empty:
            pass

        # Check for mode change only if not forced
        if force_mode is None:
            new_mode = get_current_mode()
            if type(new_mode) != type(mode):
                if mode is not None:
                    mode.shutdown()
                    if mode_thread and mode_thread.is_alive():
                        mode_thread.join(timeout=1)
                mode = new_mode
                mode_thread = threading.Thread(target=mode.run, kwargs={'run_in_plot': run_in_plot}, daemon=True)
                mode_thread.start()
                print("Current mode:", type(mode).__name__)

    if mode_thread and mode_thread.is_alive():
        mode_thread.join(timeout=1)
    mode.shutdown()
    board.Shutdown()

Run(run_in_plot)
