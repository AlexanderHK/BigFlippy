import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Board import FDProcessing
from Board import PixelBoard
from Modes.CycleMode import CycleMode
from Modes.WeatherMode import WeatherMode
from Modes.StandbyMode import StandbyMode
from enum import Enum
import random
from datetime import datetime
import time
import queue
import threading
import queue
import zmq
import json
from constants import boardSize
from Modes.WeatherMode import WEATHER_START_TIME, WEATHER_END_TIME
from Modes.CycleMode import SLEEP_START
from Board.PixelBoard import board

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
    # Add delay to ensure Flask has fully started
    print("Waiting for Flask to initialize...", flush=True)
    time.sleep(3)
    
    connected = False
    for attempt in range(5):  # Try for up to 5 attempts
        try:
            socket.connect("tcp://localhost:5555")
            print("ZMQ Subscriber connected to Flask on port 5555", flush=True)
            connected = True
            break
        except zmq.ZMQError as e:
            try:
                socket.connect("tcp://localhost:5556")
                print("ZMQ Subscriber connected to Flask on port 5556", flush=True)
                connected = True
                break
            except zmq.ZMQError as e2:
                print(f"Attempt {attempt + 1}: Waiting for Flask ZMQ to be ready...", flush=True)
                time.sleep(1)
    
    if not connected:
        print("Failed to connect to Flask after multiple attempts", flush=True)
        return
    
    try:
        while is_running_func():
            try:
                message = socket.recv_string(zmq.NOBLOCK)
                data = json.loads(message)
                print(f"Received ZMQ message: {data}", flush=True)
                
                # Put the command into the queue for processing
                if 'force' in data:
                    q.put(f"force {data['command']}")
                elif 'image_path' in data:
                    q.put(f"next {data['image_path']}")
                else:
                    q.put(data['command'])
                    
            except zmq.Again:
                # No message available
                time.sleep(0.1)
            except Exception as e:
                print(f"ZMQ error: {e}", flush=True)
                time.sleep(1)
                
    finally:
        # Clean up ZMQ resources
        socket.close()
        context.term()
        print("ZMQ subscriber thread terminated", flush=True)
    
def get_current_mode():
    now = datetime.now().time()
    if IsTimeBetween(WEATHER_START_TIME, WEATHER_END_TIME):
        return WeatherMode()
    elif IsTimeBetween(SLEEP_START, "23:59") or IsTimeBetween("00:00", WEATHER_START_TIME):
        return StandbyMode()
    else:
        return CycleMode()

def status_broadcast_thread(status_socket, is_running_func, mode_lock, get_mode_func, get_force_mode_func):
    """Thread to broadcast status updates to frontend every 3 seconds"""
    while is_running_func():
        try:
            with mode_lock:
                current_mode = get_mode_func()
                force_mode = get_force_mode_func()
                
            status_data = {
                'current_mode': type(current_mode).__name__ if current_mode else 'None',
                'is_forced': force_mode is not None,
                'forced_mode': type(force_mode).__name__ if force_mode else None,
                'timestamp': datetime.now().isoformat()
            }
            
            status_socket.send_string(json.dumps(status_data))
            
        except Exception as e:
            print(f"Status broadcast error: {e}", flush=True)
            
        time.sleep(3)  # Broadcast every 3 seconds
    
    print("Status broadcast thread terminated", flush=True)
    
#====================================================================
#                          Main Run loop
#====================================================================


def Run(run_in_plot=False):
    running = True
    command_queue = queue.Queue()
    force_mode = None
    mode = None
    mode_thread = None
    mode_lock = threading.Lock()  # Thread safety for mode operations
    
    # Setup ZMQ publisher for status updates to frontend
    status_context = zmq.Context()
    status_socket = status_context.socket(zmq.PUB)
    try:
        status_socket.bind("tcp://*:5557")
        print("Backend status publisher bound to tcp://*:5557", flush=True)
    except zmq.ZMQError as e:
        print(f"Failed to bind status publisher: {e}", flush=True)
    
    def is_running():
        return running
        
    def get_current_mode_wrapper():
        return mode
        
    def get_force_mode_wrapper():
        return force_mode
    
    # Start ZMQ subscriber thread as primary control method
    zmq_thread = threading.Thread(target=zmq_subscriber_thread, args=(command_queue, is_running), daemon=True)
    zmq_thread.start()
    
    # Start status broadcast thread
    status_thread = threading.Thread(target=status_broadcast_thread, 
                                   args=(status_socket, is_running, mode_lock, get_current_mode_wrapper, get_force_mode_wrapper), 
                                   daemon=True)
    status_thread.start()
    
    print("FlipDisk started - Browser control active on tcp://localhost:5555", flush=True)
    print("Waiting for commands from web interface...", flush=True)

    with mode_lock:
        mode = get_current_mode()
        mode_thread = threading.Thread(target=mode.run, kwargs={'run_in_plot': run_in_plot}, daemon=True)
        mode_thread.start()

    while running:
        # Check for commands from ZMQ (web interface)
        try:
            command = command_queue.get(timeout=0.1)
            print(f"Received command: {command}", flush=True)


            if command == 'exit':
                running = False
                with mode_lock:
                    if mode:
                        mode.shutdown()

            elif command.startswith('force '):
                arg = command.split(' ', 1)[1]
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
                    print(f"Unknown mode: {arg}", flush=True)
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
                    print(f"Forced mode: {type(mode).__name__}", flush=True)


            elif command == 'release':
                force_mode = None
                print("Released forced mode. Returning to automatic mode switching.", flush=True)
            
            else:
                with mode_lock:
                    if mode:
                        try:
                            mode.receive_data(command)
                        except Exception as e:
                            print(f"Error processing command '{command}': {e}", flush=True)
                
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
                    print("Current mode:", type(mode).__name__, flush=True)

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
