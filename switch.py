import obspython as obs

def on_event(event):
    if event == obs.OBS_FRONTEND_EVENT_EXIT:
        # Clean up resources and disconnect from OBS
        obs.obs_frontend_shutdown()

def on_button_clicked(props, prop):
    scene_name = obs.obs_data_get_string(props, "scene_name")
    scene = obs.obs_scene_from_name(scene_name)
    if scene is not None:
        obs.obs_frontend_set_current_scene(scene)

def script_properties():
    props = obs.obs_properties_create()

    # Scene selection dropdown
    scene_list = obs.obs_properties_add_list(props, "scene_name", "Scene 2", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    scenes = obs.obs_frontend_get_scenes()
    for scene in scenes:
        scene_name = obs.obs_source_get_name(scene)
        obs.obs_property_list_add_string(scene_list, scene_name, scene_name)

    # Button
    obs.obs_properties_add_button(props, "button", "Switch Scene", on_button_clicked)

    return props

def script_load(settings):
    # Register an event handler to handle the OBS frontend exit event
    obs.obs_frontend_add_event_callback(on_event)

    # Connect to the local OBS instance
    obs.obs_frontend_connect()

def script_unload():
    # Disconnect from the local OBS instance
    obs.obs_frontend_disconnect()
