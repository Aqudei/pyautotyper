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

def ensure_unlocked(password):
    current_resolution = pyautogui.size()
    mouse_x,mouse_y = pyautogui.position()
    pyautogui.moveTo(2,2,duration=1)
    
    try:
        login_window = find_window("Workstation is Locked by")
        if not login_window:
            return
        
        if login_window.title != gw.getActiveWindow().title:
            login_window.activate()

        resized = resize_image_for_resolution("./images/login_switch.png",ORIGINAL_RESOLUTION,current_resolution)
        # Save the resized image or use it directly
        
        login_x,login_y = pyautogui.locateCenterOnScreen(resized, grayscale=True)
        pyautogui.click(login_x,login_y)
        
        pyautogui.write(f"{password}")
        pyautogui.press("enter")
        
        
    except Exception as e:
        logger.exception(e)
        logger.error(tb.format_exc())
    finally:
        pyautogui.moveTo(mouse_x,mouse_y)
    
def perform_type_job(params):
    # Get current time without microseconds
    time_now = datetime.datetime.now().replace(microsecond=0)

    # Check if current time is within the start and end range
    if not (params['start'] <= time_now <= params['end']):
        print("Not Running. Current time is outside specified range of <start> and <end>.")
        return

    ensure_unlocked(params.get('password'))
    
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
            print(f"Cannot find window with title: {params['window_name']}")
            return
        window.maximize()
        window.activate()

    # Perform action on the found/active window
    print(f"{time_now} - performing type...")
    pyautogui.write(params['to_type'])
    pyautogui.press("enter")
    
if __name__ == "__main__":
    
    try:
        current_resolution = pyautogui.size()  # (width, height)
        print(f"Current Resolution: {current_resolution}")
        
        print("Reading params...")
        params = read_params()
        last_checksum = compute_checksum(CONFIG_FILE)
        pprint.pprint(params)
        
        job = schedule.every().minute.at(":05").do(perform_type_job, params=params)
        
        print("Waiting...")
        while True:
            checksum = compute_checksum(CONFIG_FILE)
            if checksum != last_checksum:
                print("Settings chenged! Re-initializing program...")
                last_checksum = checksum
                params = read_params()
                pprint.pprint(params)

                schedule.cancel_job(job)
                job = schedule.every().minute.at(":05").do(perform_type_job, params=params)
                print("Waiting...")
                
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        logger.exception(e)
        logger.error(tb.format_exc())
    
    os.system("PAUSE")


    
