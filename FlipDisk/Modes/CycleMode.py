from PIL import Image, ImageSequence
import os
import random
from datetime import datetime
import time
import FDProcessing
import PixelBoard
from global_state import boardSize, board
from .ModeBase import ModeBase

#global variables
STATE = "RUNNING"

#Cycle mode Variables
ACCEPTABLE_EXTENSIONS = ['jpg', 'jpeg', 'png']
ACCEPTABLE_PROCESSING_MODES = ['EdgeDetection', 'SimpleBW', 'Yolo']
IMAGE_CYCLE_TIME = 5  # Time in seconds for image cycle mode
ANIMATION_FRAME_RATE = 0.1  # Time in seconds for each frame in animation
CYCLE_IMAGE_DIRECTORY = "TestImages"  # Directory where images are stored
SLEEP_START = "23:00"
GIF_LOOPS = 3

#Instance variables
LOADED_FILES = []
last_cycle_name = ""
last_time = time.time()


#=================================================================
#                   Content Class
#=================================================================
class ContentObject:
    '''Class representing a FlipDisk object, which can be a photo or an animation.'''
    def __init__(self, filepath, mode):
            

        self.filepath = filepath

        if filepath.endswith(".gif"):
            self.name = filepath.split("\\")[-1].split(".")[0]
            self.content_type = "GIF"

        elif os.path.isdir(filepath):
            self.name = filepath.split("/")[-1]
            #folders in this directory are animations
            self.content_type = "Animation"
        
        elif "." in filepath.split("\\")[-1]:
            self.name = filepath.split("\\")[-1].split(".")[0]
            self.content_type = "Photo"
            

        #chooses processing mode based on the folder above the file with a lil error handling bb
        self.processing_mode = mode
        if self.processing_mode not in ACCEPTABLE_PROCESSING_MODES:
            print(f"Processing mode {self.processing_mode} not recognized. Defaulting to 'SimpleBW'.")
            self.processing_mode = "SimpleBW"
   
    def to_string(self):
        return f"ContentObject(name={self.name}, type={self.content_type}, processing_mode={self.processing_mode})"

#=================================================================
#                   Content publish functions
#=================================================================
def publish_gif(content, run_in_plot=False):
    """Publishes a GIF by extracting its frames and displaying them.
    :param filepath: Path to the GIF file.
    """
    frames = parse_gif(content.filepath)
    for frame in frames:
        img = frame
        match content.processing_mode:
            case "EdgeDetection":
                img = FDProcessing.EdgeDetection(img, boardSize)
            case "SimpleBW":
                img = FDProcessing.SimpleBW(img, boardSize)
            case "Yolo":
                img = FDProcessing.yoloSeg(img, boardSize)
        
        board.loadImage(img)
        if not run_in_plot:
            board.publishImage()
            board.refreshDisplay()
            time.sleep(ANIMATION_FRAME_RATE)
        else:
            board.PlotLocal()

def publish_animation(content, run_in_plot=False):
    """Publishes an animation by cycling through images in a folder.
    :param folder: Path to the folder containing images.
    """
    for file in os.listdir(content.filepath):
        if file.split('.')[-1].lower() in ACCEPTABLE_EXTENSIONS:
            img_path = os.path.join(content.filepath, file)
            img = Image.open(img_path)
            match content.processing_mode:
                case "EdgeDetection":
                    img = FDProcessing.EdgeDetection(img, boardSize)
                case "SimpleBW":
                    img = FDProcessing.SimpleBW(img, boardSize)
                case "Yolo":
                    img = FDProcessing.yoloSeg(img, boardSize)
            board.loadImage(img)
            if not run_in_plot:
                board.publishImage()
                board.refreshDisplay()
                time.sleep(ANIMATION_FRAME_RATE)
            else:
                board.PlotLocal()

def publish_photo(content, run_in_plot=False):
    """Publishes a photo by loading and displaying it.
    :param filepath: Path to the photo file.
    """
    img = Image.open(content.filepath)
    match content.processing_mode:
        case "EdgeDetection":
            img = FDProcessing.EdgeDetection(img, boardSize)
        case "SimpleBW":
            img = FDProcessing.SimpleBW(img, boardSize)
        case "Yolo":
            img = FDProcessing.yoloSeg(img, boardSize)
    board.loadImage(img)
    if not run_in_plot:
        board.publishImage()
        board.refreshDisplay()
    else:
        board.PlotLocal()


#=================================================================
#                   Helper functions
#=================================================================
def loadContentObjects(boardSize=(28, 28)):
    '''Load all content objects from the specified directory.'''
    global LOADED_FILES, CYCLE_IMAGE_DIRECTORY
    LOADED_FILES = []
    
    for mode in ACCEPTABLE_PROCESSING_MODES:
        #Load files from the directory
        for root, dirs, files in os.walk(os.path.join(CYCLE_IMAGE_DIRECTORY, mode)):
            for file in files:
                filepath = os.path.join(root, file)
                if os.path.isfile(filepath) or os.path.isdir(filepath):
                    content_object = ContentObject(filepath, mode)
                    LOADED_FILES.append(content_object)
    
    return LOADED_FILES

def parse_gif(filepath):
    """
    Parses the frames of a GIF and saves them as PNGs in a new folder in the same directory.
    :param gif_path: Path to the GIF file.

    returns: List of paths to the extracted frames.
    """
    frames = []
    # Get the base directory and gif name (without extension)
    base_dir = os.path.dirname(filepath)
    gif_name = os.path.splitext(os.path.basename(filepath))[0]
    output_folder = os.path.join(base_dir, f"{gif_name}_frames")
    
    

    frames = []
    try:
        img = Image.open(filepath)
        for frame in ImageSequence.Iterator(img):
            frames.append(frame.copy())  # Append a copy to avoid issues with subsequent seeks
    except FileNotFoundError:
        print(f"Error: GIF file not found at {filepath}")
    except Exception as e:
        print(f"An error occurred while loading GIF frames: {e}")
    
    og_frames = frames.copy()
    for _ in range(GIF_LOOPS):
            frames.extend(og_frames)
    return frames
#=================================================================
#                   Main function
#=================================================================
def cycle(current_time, run_in_plot=False):
    """Cycles through images in a specified directory and displays them on the board.
    :param board: The PixelBoard object to display images on.   
    """
    global last_cycle_name, last_time, LOADED_FILES
    #chooses a random object from the loaded files
    
    #have to do some error checking here for some reason
    if len(LOADED_FILES)==0:
        return
    current_image_obj = random.choice(LOADED_FILES)
    current_image = current_image_obj.name

    if current_time - last_time >= IMAGE_CYCLE_TIME and current_image != last_cycle_name:
        print(f"Loading image: {current_image}")

        # Check the type of the content object and process accordingly
        match current_image_obj.content_type:

            case "GIF":
                # If the object is an animation, cycle through its frames
                print(f"Cycling through animation: {current_image}")
                publish_gif(current_image_obj, run_in_plot)
            case "Animation":
                # If the object is a folder with images, cycle through the images in that folder
                print(f"Cycling through animation folder: {current_image}")
                publish_animation(current_image_obj, run_in_plot)
            case "Photo":
                print(f"Displaying photo: {current_image}")
                publish_photo(current_image_obj, run_in_plot)

        last_time = current_time
        last_cycle_name = current_image
    return
import threading

class CycleMode(ModeBase):
    def __init__(self):
        self.last_cycle_name = ""
        self.last_time = time.time()
        loadContentObjects(boardSize)
        self.state = "RUNNING"
        self.input_event = threading.Event()
        self.input_data = None
        self.lock = threading.Lock()

    def run(self, run_in_plot=False):
        
        while self.state == "RUNNING":
            current_time = time.time()
            
            # If input_event is set and input_data is 'next', cycle immediately
            if self.input_event.is_set():
                with self.lock:
                    if self.input_data and self.input_data.lower() == 'next':
                        cycle(current_time, run_in_plot)
                        self.input_event.clear()
                        self.input_data = None
                        continue
                        
            # Otherwise, cycle normally
            cycle(current_time, run_in_plot)
            if not run_in_plot:
                board.refreshDisplay()
            else:
                board.PlotLocal()

    def shutdown(self):
        self.state = "STOPPED"

    def receive_data(self, data):
        with self.lock:
            self.input_data = data
            self.input_event.set()
