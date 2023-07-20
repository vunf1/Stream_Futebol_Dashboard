obs = obslua
bit = require("bit")

function capture_last_5_seconds()
    local frames = {}

    -- Capture frames for 5 seconds
    local start_time = os.time()
    while os.time() - start_time < 5 do
        local frame = obs.video_source_get_frame("YourSourceName")
        table.insert(frames, frame)
        obs.obs_source_release(frame)
    end

    -- Concatenate the frames into a single clip
    if #frames > 0 then
        local output = obs.obs_source_create("ffmpeg_source", "YourClipName", nil, nil)
        for i, frame in ipairs(frames) do
            obs.obs_source_add_audio_frame(output, frame.audio)
            obs.obs_source_add_video_frame(output, frame.video)
            obs.obs_source_release(frame)
        end
        return output
    else
        return nil
    end
end

function script_tick(seconds)
    local source = obs.obs_get_source_by_name("YourSourceName")
    if source then
        local settings = obs.obs_source_get_settings(source)
        local activate = obs.obs_data_get_bool(settings, "activate")
        obs.obs_data_release(settings)
        obs.obs_source_release(source)

        if activate then
            local video = capture_last_5_seconds()
            if video then
                local current_datetime = os.date("*t")
                local filename = string.format("%d-%02d-%02d_%02d-%02d-%02d.mp4", current_datetime.year, current_datetime.month, current_datetime.day, current_datetime.hour, current_datetime.min, current_datetime.sec)
                obs.obs_save_sources()
                local save_path = obs.obs_get_output_directory()
                obs.obs_source_set_settings(video, obslua.obs_data_create())
                obs.obs_source_update(video, obslua.obs_data_create())
                obs.obs_source_set_enabled(video, true)
                obs.obs_frontend_save_streaming_output(filename, save_path)
                obs.obs_source_release(video)
            else
                print("No frames captured.")
            end
        end
    end
end

function script_description()
    return "Capture the last 5 seconds of a source and save it as a video when activated."
end

function script_properties()
    local props = obs.obs_properties_create()
    obs.obs_properties_add_bool(props, "activate", "Activate")
    obs.obs_properties_add_text(props, "source_name", "Source Name", obs.OBS_TEXT_DEFAULT)
    return props
end

function script_update(settings)
    local source_name = obslua.obs_data_get_string(settings, "source_name")
    local source = obs.obs_get_source_by_name(source_name)
    if source then
        obs.obs_source_release(source)
    end
end

function key_event(pressed)
    if pressed and keyboard.key == 'B' then
        script_tick()
    end
end

function script_load(settings)
    obs.obs_frontend_add_event_callback(key_event)
end

obs.obs_register_script(script_description(), script_properties(), script_update, script_load)
