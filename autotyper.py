import datetime
import os
import pprint
import time
import pygetwindow as gw
import pyautogui
import yaml
import schedule
import logging
import traceback as tb
import hashlib
from PIL import Image


try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    
# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('app.log')

# Set the log level for handlers
console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.WARNING)

# Create formatters and add them to handlers
console_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_handler.setFormatter(console_format)
file_handler.setFormatter(file_format)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

CONFIG_FILE = "./input.yaml"
ORIGINAL_RESOLUTION = (2560, 1440) # Resolution of my Laptop

def resize_image_for_resolution(sample_image_path, original_resolution, current_resolution):
    # Open the sample image
    sample_image = Image.open(sample_image_path)

    # Calculate the scaling factor
    width_ratio = current_resolution[0] / original_resolution[0]
    height_ratio = current_resolution[1] / original_resolution[1]

    # Resize the sample image based on the current resolution
    new_width = int(sample_image.width * width_ratio)
    new_height = int(sample_image.height * height_ratio)
    resized_image = sample_image.resize((new_width, new_height))

    return resized_image

def compute_checksum(file_path, algorithm='md5'):
    hash_func = hashlib.new(algorithm)
    
    # Read the file in chunks to avoid memory overload with large files
    with open(file_path, 'rb') as file:
        while chunk := file.read(8192):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def read_params():

    with open(CONFIG_FILE,'r') as infile:
        params = yaml.load(infile,Loader=Loader)
        return params

def find_window(window_name):
    windows =gw.getAllWindows()
    for w in windows:
        if not window_name.lower() in w.title.lower():
            continue        
        return w

def prevent_idle():
    logger.info("Generating mouse movement...")
    screen_width, screen_height = pyautogui.size()
    mouse_x,mouse_y = pyautogui.position()
    mouse_x = (mouse_x + 256) % screen_width
    mouse_y =  (mouse_y + 256) % screen_height
    pyautogui.moveTo(mouse_x,mouse_y,duration=3)
    
def perform_type_job(params):
    # Get current time without microseconds
    time_now = datetime.datetime.now().replace(microsecond=0)

    # Check if current time is within the start and end range
    if not (params['start'] <= time_now <= params['end']):
        logger.info("Not Running. Current time is outside specified range of <start> and <end>.")
        return
    
    # Calculate minutes delta and check divisibility by interval
    delta_minutes = (time_now - params['start']).total_seconds() // 60
    if delta_minutes % params['interval'] != 0:
        return
    
    # Check active window title for match
    window = gw.getActiveWindow()
    
    if not (window and params['window_name'].lower() in window.title.lower()):
        # Try to find the window if the active window doesn't match
        window = find_window(params['window_name'])
        if not window:
            logger.info(f"Cannot find window with title: {params['window_name']}")
            return
        window.maximize()
        window.activate()

    # Perform action on the found/active window
    logger.info(f"{time_now} - performing type...")
    pyautogui.write(params['to_type'])
    pyautogui.press("enter")
    
if __name__ == "__main__":
    
    
    try:
    
        current_resolution = pyautogui.size()  # (width, height)
        logger.info(f"Current Resolution: {current_resolution}")
        
        logger.info("Reading params...")
        params = read_params()
        no_idle_interval = params.get('no_idle_interval',3)
        last_checksum = compute_checksum(CONFIG_FILE)
        logger.info(params)
        
        job = schedule.every().minute.at(":05").do(perform_type_job, params=params)
        no_idle_job = schedule.every(no_idle_interval).minute.do(prevent_idle)

        logger.info("Waiting...")
        while True:
            checksum = compute_checksum(CONFIG_FILE)
            if checksum != last_checksum:
                logger.info("Settings chenged! Re-initializing program...")
                last_checksum = checksum
                params = read_params()
                no_idle_interval = params.get('no_idle_interval',3)

                logger.info(params)

                schedule.cancel_job(job)
                schedule.cancel_job(no_idle_job)
                
                job = schedule.every().minute.at(":05").do(perform_type_job, params=params)
                no_idle_job = schedule.every(no_idle_interval).minute.do(prevent_idle)

                logger.info("Waiting...")
            
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        logger.exception(e)
        logger.error(tb.format_exc())
    
    os.system("PAUSE")