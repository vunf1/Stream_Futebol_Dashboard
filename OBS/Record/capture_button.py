import obspython as obs
import os

def on_event(event):
    if event == obs.OBS_FRONTEND_EVENT_EXIT:
        # Clean up resources and disconnect from OBS
        obs.obs_frontend_shutdown()

def on_button_clicked(props, prop):
    scene_name = obs.obs_data_get_string(props, "scene_name")
    scene = obs.obs_scene_from_name(scene_name)

    if scene is not None:
        obs.obs_frontend_set_current_scene(scene)

        # Get the selected directory from the properties
        selected_dir = obs.obs_data_get_string(props, "selected_directory")

        # Check if the directory exists and is a valid directory
        if os.path.isdir(selected_dir):
            # List all files in the selected directory
            files = [file for file in os.listdir(selected_dir) if os.path.isfile(os.path.join(selected_dir, file))]

            # Display the list of files in the OBS log
            for file_name in files:
                print(file_name)

            # Add a media source for each file in the list - NOT DISPLAYING - OBS LIMITATION
            for file_name in files:
                file_path = os.path.join(selected_dir, file_name)
                source = obs.obs_source_create("ffmpeg_source", file_name, None, None)
                settings = obs.obs_data_create()
                obs.obs_data_set_string(settings, "local_file", file_path)
                obs.obs_source_update(source, settings)
                obs.obs_scene_add(scene, source)
                obs.obs_data_release(settings)
                obs.obs_source_release(source)

def script_properties():
    props = obs.obs_properties_create()

    # Scene selection dropdown
    scene_list = obs.obs_properties_add_list(props, "scene_name", "Scene", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    scenes = obs.obs_frontend_get_scenes()
    for scene in scenes:
        scene_name = obs.obs_source_get_name(scene)
        obs.obs_property_list_add_string(scene_list, scene_name, scene_name)

    # Button
    obs.obs_properties_add_button(props, "button", "Switch Scene and Add Videos", on_button_clicked)

    # Text Input for directory selection
    obs.obs_properties_add_path(props, "selected_directory", "Directory", obs.OBS_PATH_DIRECTORY, "", None)

    return props

def script_load(settings):
    # Register an event handler to handle the OBS frontend exit event
    obs.obs_frontend_add_event_callback(on_event)

    # Connect to the local OBS instance
    obs.obs_frontend_connect()

def script_unload():
    # Disconnect from the local OBS instance
    obs.obs_frontend_disconnect()
