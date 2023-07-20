import cv2
import keyboard
import time
from datetime import datetime
import os
'''breaks OBS - because is not using pre define function from OBS to LOAD scripts'''
def capture_last_5_seconds():
    cap = cv2.VideoCapture(0)  # Replace 0 with the appropriate video capture device index if needed
    frames = []
    start_time = time.time()

    # Capture frames for 5 seconds
    while time.time() - start_time < 5:
        ret, frame = cap.read()
        if not ret:
            print("Error capturing frame.")
            break
        frames.append(frame)

    # Concatenate the frames into a single video
    if frames:
        output = cv2.vconcat(frames)
        return output
    else:
        return None

try:
    # Specify the file save directory
    save_directory = 'C:\\Users\\Joaom\\Videos\\replays\\'

    while True:
        if keyboard.is_pressed('B'):
            print("b pressed")
            video = capture_last_5_seconds()
            if video is not None:
                # Get the current date and time
                current_datetime = datetime.now()
                current_date = current_datetime.date()
                save_directory = f'{save_directory}{current_date}\\'
                current_time = current_datetime.time()
                filename = f'{current_date}_{current_time}.mp4'

                # Create the full file path
                file_path = os.path.join(save_directory, filename)

                # Save the video using cv2.VideoWriter
                frame_height, frame_width, _ = video.shape
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')#The * operator before the string 'mp4v' is used to unpack the characters of the string as separate arguments for the cv2.VideoWriter_fourcc function.
                writer = cv2.VideoWriter(file_path, fourcc, 25, (frame_width, frame_height))
                writer.write(video)
                writer.release()

                print(f"Video saved: {file_path}")
            else:
                print("No frames captured.")
            # Remove the break statement here
        time.sleep(0.1)  # Add a small delay to reduce CPU usage

except Exception as e:
    print(f"An error occurred: {str(e)}")
