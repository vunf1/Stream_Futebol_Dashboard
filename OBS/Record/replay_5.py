import cv2
import time
import os
import obspython as obs

# Global variables
recording_started = False
output_file = None
out = None
start_time = None
frames = []

def start_recording(props, prop):
    global recording_started, output_file, out, start_time, frames

    output_directory = "C:\\Users\\Joaom\\Videos\\recordings\\"

    current_time = time.strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_directory, f"output_{current_time}.mp4")

    cap = cv2.VideoCapture(0)

    # Check if the capture device was successfully opened
    if not cap.isOpened():
        print("Failed to open video capture device")
        return

    frames = []
    start_time = time.time()
    recording_started = True
    print("Recording started.")

def stop_recording(props, prop):
    global recording_started, out, output_file, frames

    recording_started = False
    print("Recording stopped.")

    # Save the recorded frames to a video file
    if frames:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_file, fourcc, 30.0, (640, 480))

        for frame in frames:
            out.write(frame)

        out.release()
        print("Video saved successfully:", output_file)

    frames = []

def script_description():
    return "Script to record the last 5 seconds from a video capture feed in OBS."

def script_update(settings):
    pass

def script_properties():
    props = obs.obs_properties_create()

    # Button for starting and stopping recording
    obs.obs_properties_add_button(props, "start_recording", "Start/Stop Recording", start_recording)

    return props

def script_tick(seconds):
    global recording_started, frames, start_time

    if recording_started:
        # Get the current frame from the video capture feed
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)

        # Check if 5 seconds have elapsed for the recording
        if time.time() - start_time > 5:
            stop_recording(None, None)

        cap.release()
