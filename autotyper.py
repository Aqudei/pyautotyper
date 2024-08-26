import datetime
import os
import pprint
import time
import pygetwindow as gw
import pyautogui
import yaml
import schedule
import logging

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

def read_params():
    with open("./input.yaml",'r') as infile:
        params = yaml.load(infile,Loader=Loader)
        return params

def find_window(window_name):
    windows =gw.getAllWindows()
    for w in windows:
        if not window_name.lower() in w.title.lower():
            continue        
        return w
    
def job(params):
    # Get current time without microseconds
    time_now = datetime.datetime.now().replace(microsecond=0)

    # Check if current time is within the start and end range
    if not (params['start'] <= time_now <= params['end']):
        print("Not Running. Current time is outside specified range of <start> and <end>.")
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
            print(f"Cannot find window with title: {params['window_name']}")
            return
        window.maximize()
        window.activate()

    # Perform action on the found/active window
    print(f"{time_now} - performing type...")
    pyautogui.write(params['to_type'])
    
if __name__ == "__main__":
    
    try:
        print("Reading params...")
        params = read_params()
        pprint.pprint(params)
        
        
        schedule.every().minute.at(":05").do(job, params=params)
        
        print("Waiting...")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.exception(e)
    
    
    os.system("PAUSE")


    
