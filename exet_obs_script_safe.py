import obspython as obs
import os
import tkinter as tk
from tkinter import filedialog

def on_event(event):
    if event == obs.OBS_FRONTEND_EVENT_EXIT:
        # Clean up resources and disconnect from OBS
        obs.obs_frontend_shutdown()

def on_button_clicked(props, prop):
    scene_name = obs.obs_data_get_string(props, "scene_name")
    scene = obs.obs_scene_from_name(scene_name)
    if scene is not None:
        obs.obs_frontend_set_current_scene(scene)

    # Open dialog to select a video file
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi;*.mkv")])#The * operator before the string 'mp4v' is used to unpack the characters of the string as separate arguments for the cv2.VideoWriter_fourcc function.
    if file_path:
        source_name = os.path.basename(file_path)
        source_settings = obs.obs_data_create()
        obs.obs_data_set_string(source_settings, "local_file", file_path)
        source = obs.obs_source_create("ffmpeg_source", source_name, source_settings, None)
        obs.obs_scene_add(scene, source)
        obs.obs_source_release(source)
        obs.obs_data_release(source_settings)

def script_properties():
    props = obs.obs_properties_create()

    # Scene selection dropdown
    scene_list = obs.obs_properties_add_list(props, "scene_name", "Scene", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    scenes = obs.obs_frontend_get_scenes()
    for scene in scenes:
        scene_name = obs.obs_source_get_name(scene)
        obs.obs_property_list_add_string(scene_list, scene_name, scene_name)

    # Button
    obs.obs_properties_add_button(props, "button", "Switch Scene and Add Video", on_button_clicked)

    return props

def script_load(settings):
    # Register an event handler to handle the OBS frontend exit event
    obs.obs_frontend_add_event_callback(on_event)

    # Connect to the local OBS instance
    obs.obs_frontend_connect()

if __name__ == "__main__":
    # Initialize the tkinter root for file dialog
    root = tk.Tk()
    root.withdraw()

    # Run the OBS script
    script_load(None)
