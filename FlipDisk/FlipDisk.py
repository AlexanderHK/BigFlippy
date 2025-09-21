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
import zmq
import json
from global_state import boardSize, board
from Modes.WeatherMode import WEATHER_START_TIME, WEATHER_END_TIME
from Modes.CycleMode import SLEEP_START

class Mode(Enum):
    IMAGE_CYCLE = 0
    WEATHER = 1
    PONG = 2
    STANDBY = 3

#run plotted version
run_in_plot = True



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
    
def zmq_subscriber_thread(q, is_running_func):
    """ZMQ subscriber thread to receive messages from Flask app"""
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
    
    # Connect to Flask publisher (Flask binds, we connect)
    try:
        socket.connect("tcp://localhost:5555")
        print("ZMQ Subscriber connected to Flask on port 5555")
    except zmq.ZMQError as e:
        try:
            socket.connect("tcp://localhost:5556")
            print("ZMQ Subscriber connected to Flask on port 5556")
        except zmq.ZMQError as e2:
            print(f"Failed to connect to Flask: {e2}")
            return
    
    try:
        while is_running_func():
            try:
                message = socket.recv_string(zmq.NOBLOCK)
                data = json.loads(message)
                print(f"Received ZMQ message: {data}")
                
                # Put the command into the queue for processing
                if 'command' in data:
                    q.put(f"force {data['command']}")
                elif 'image_path' in data:
                    q.put(f"image {data['image_path']}")
                    
            except zmq.Again:
                # No message available
                time.sleep(0.1)
            except Exception as e:
                print(f"ZMQ error: {e}")
                time.sleep(1)
                
    finally:
        # Clean up ZMQ resources
        socket.close()
        context.term()
        print("ZMQ subscriber thread terminated")
    
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
    command_queue = queue.Queue()
    force_mode = None
    mode_thread = None
    mode_lock = threading.Lock()  # Thread safety for mode operations
    
    def is_running():
        return running
    
    # Start ZMQ subscriber thread as primary control method
    zmq_thread = threading.Thread(target=zmq_subscriber_thread, args=(command_queue, is_running), daemon=True)
    zmq_thread.start()
    print("FlipDisk started - Browser control active on tcp://localhost:5555")
    print("Waiting for commands from web interface...")

    with mode_lock:
        mode = get_current_mode()
        mode_thread = threading.Thread(target=mode.run, kwargs={'run_in_plot': run_in_plot}, daemon=True)
        mode_thread.start()

    while running:
        # Check for commands from ZMQ (web interface)
        try:
            command = command_queue.get(timeout=0.1)
            command_lower = command.lower()
            print(f"Received command: {command_lower}")


            if command_lower == 'exit':
                running = False
                with mode_lock:
                    if mode:
                        mode.shutdown()

            elif command_lower.startswith('force '):
                arg = command_lower.split(' ', 1)[1]
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

                with mode_lock:
                    force_mode = type(new_mode)
                    if mode:
                        mode.shutdown()

                    if mode_thread and mode_thread.is_alive():
                        mode_thread.join(timeout=1)

                    mode = new_mode
                    mode_thread = threading.Thread(target=mode.run, kwargs={'run_in_plot': run_in_plot}, daemon=True)
                    mode_thread.start()
                    print(f"Forced mode: {type(mode).__name__}")

            elif command_lower.startswith('image '):
                # Handle image processing from web interface
                image_path = command_lower.split(' ', 1)[1]
                print(f"Processing image: {image_path}")
                # Send image to current mode for processing
                with mode_lock:
                    if mode:
                        try:
                            mode.receive_data(f"image {image_path}")
                        except Exception as e:
                            print(f"Error processing image command: {e}")

            elif command_lower == 'release':
                force_mode = None
                print("Released forced mode. Returning to automatic mode switching.")
            
            else:
                with mode_lock:
                    if mode:
                        try:
                            mode.receive_data(command)
                        except Exception as e:
                            print(f"Error processing command '{command}': {e}")
                
        except queue.Empty:
            pass

        # Check for mode change only if not forced
        if force_mode is None:
            new_mode = get_current_mode()
            with mode_lock:
                if type(new_mode) != type(mode):
                    if mode is not None:
                        mode.shutdown()
                        if mode_thread and mode_thread.is_alive():
                            mode_thread.join(timeout=1)
                    mode = new_mode
                    mode_thread = threading.Thread(target=mode.run, kwargs={'run_in_plot': run_in_plot}, daemon=True)
                    mode_thread.start()
                    print("Current mode:", type(mode).__name__)

    # Clean shutdown
    with mode_lock:
        if mode_thread and mode_thread.is_alive():
            mode_thread.join(timeout=1)
        if mode:
            mode.shutdown()
    
    # Wait for ZMQ thread to finish
    if zmq_thread.is_alive():
        zmq_thread.join(timeout=2)
    
    board.Shutdown()

Run(run_in_plot)
