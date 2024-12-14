import cv2
import time
from datetime import datetime
import os
import obspython as obs

# Global variables
recording_started = False
output_file = None
out = None
start_time = None

def start_recording(props, prop):
    """
    Parameters:
    props (obs_properties_t): The properties object associated with the script.
    prop (obs_property_t): The property associated with the button.

    Returns:
    None
    """
    global recording_started, output_file, out, start_time

    # Specify the output directory
    output_directory = "C:\\Users\\Joaom\\Videos\\replays\\"

    # Generate the output filename with current date and time
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_directory, f"output_{current_time}.mp4")

    # Open the video capture device
    cap = cv2.VideoCapture(0)

    # Check if the capture device was successfully opened
    if not cap.isOpened():
        print("Failed to open video capture device")
        return

    # Set the video codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')#The * operator before the string 'mp4v' is used to unpack the characters of the string as separate arguments for the cv2.VideoWriter_fourcc function.
    out = cv2.VideoWriter(output_file, fourcc, 30.0, (640, 480))

    # Get the start time
    start_time = time.time()
    recording_started = True
    print("Recording started.")

def stop_recording(props, prop):
    """

    Parameters:
    props (obs_properties_t): The properties object associated with the script.
    prop (obs_property_t): The property associated with the button.

    Returns:
    None - save in global
    """
    global recording_started, out, output_file

    out.release()
    recording_started = False
    print("Recording stopped. Video saved successfully:", output_file)

def script_description():
    """
    Function to return the description of the script.

    Parameters:
    None

    Returns:
    str: The description of the script.
    """
    return "Script to record video in OBS when the 'B' key is pressed."

def script_update(settings):
    """
    Function to update the script settings.

    Parameters:
    settings (obs_data_t): The script settings.

    Returns:
    None
    """
    pass

def script_properties():
    """
    Function to define the script properties - UI.

    Parameters:
    None

    Returns:
    obs_properties_t: The properties for the script.
    """
    '''props = obs.obs_properties_create()
    obs.obs_properties_add_button(props, "start_recording", "Start Recording", start_recording)
    obs.obs_properties_add_button(props, "stop_recording", "Stop Recording", stop_recording)
    return props'''

def script_tick(seconds):
    """
    Function called by OBS at regular intervals to check for keypress and stop the recording after 5 seconds.

    Parameters:
    seconds (float): The time elapsed since the last call to the script_tick function.

    Returns:
    None
    """
    global recording_started, start_time

    # Check if the 'B' key is pressed
    if cv2.waitKey(1) == ord('B'):
        if not recording_started:
            start_recording(None, None)
        else:
            stop_recording(None, None)

    # Check if 5 seconds have elapsed for the recording
    if recording_started and time.time() - start_time > 5:
        stop_recording(None, None)
