local obs = obslua

-- Set the replay buffer lengths in seconds
local replayDurations = {5, 8, 10}

-- Store the timestamp when each replay hotkey is pressed
local replayTimestamps = {}

-- Function to handle saving replays
function saveReplay(replayDuration)
    local replayName = string.format("Replay_%d_seconds", replayDuration)
    obs.script_log(obs.LOG_INFO, "Saving replay for " .. replayDuration .. " seconds.")
    obs.obs_frontend_save_replay_buffer(replayName, "", obs.OBS_SAVE_REPLAY_BUFFER_STOPPED, replayDuration * 1000)
end

-- Function to check for replay hotkey presses
function checkReplayHotkeys()
    for i, replayDuration in ipairs(replayDurations) do
        if replayTimestamps[replayDuration] then
            local currentTime = os.time()
            if currentTime - replayTimestamps[replayDuration] >= replayDuration then
                saveReplay(replayDuration)
                replayTimestamps[replayDuration] = nil
            end
        end
    end
end

-- Function to handle hotkey presses
function onHotkey(pressed)
    if pressed then
        local hotkeyId = obs.obs_hotkey_id()
        for i, replayDuration in ipairs(replayDurations) do
            if hotkeyId == obs.OBS_INVALID_HOTKEY_ID then
                return
            end

            if hotkeyId == obs.obs_hotkey_id_from_name(string.format("Replay_%d_seconds", replayDuration)) then
                replayTimestamps[replayDuration] = os.time()
            end
        end
    end
end

-- Function to handle script load
function script_load(settings)
    for i, replayDuration in ipairs(replayDurations) do
        local hotkeyId = obs.obs_hotkey_register_frontend(string.format("Replay_%d_seconds", replayDuration),
                                                          "Replay " .. replayDuration .. " Seconds", onHotkey)
        local hotkeySaveArray = obs.obs_data_get_array(settings, string.format("Replay_%d_seconds", replayDuration))
        obs.obs_hotkey_load(hotkeyId, hotkeySaveArray)
        obs.obs_data_array_release(hotkeySaveArray)
    end
end

-- Function to handle script save
function script_save(settings)
    for i, replayDuration in ipairs(replayDurations) do
        local hotkeyId = obs.obs_hotkey_id_from_name(string.format("Replay_%d_seconds", replayDuration))
        local hotkeyArray = obs.obs_hotkey_save(hotkeyId)
        obs.obs_data_set_array(settings, string.format("Replay_%d_seconds", replayDuration), hotkeyArray)
        obs.obs_data_array_release(hotkeyArray)
    end
end

-- Function to handle script update (tick)
function script_tick(seconds)
    checkReplayHotkeys()
end

-- Function to handle script description (optional)
function script_description()
    return "Replay Script\n\nThis script enables replay functionality for the last 5, 8, and 10 seconds using hotkeys."
end

-- Register script callbacks with OBS
function script_load(settings)
    obs.obs_frontend_add_tick_callback(script_tick)
end

function script_unload()
    obs.obs_frontend_remove_tick_callback(script_tick)
end

function script_defaults(settings)
    for i, replayDuration in ipairs(replayDurations) do
        local hotkeyArray = obs.obs_data_get_array(settings, string.format("Replay_%d_seconds", replayDuration))
        local hotkeyId = obs.obs_hotkey_register_frontend(string.format("Replay_%d_seconds", replayDuration),
                                                          "Replay " .. replayDuration .. " Seconds", onHotkey)
        obs.obs_hotkey_load(hotkeyId, hotkeyArray)
        obs.obs_data_array_release(hotkeyArray)
    end
end

function script_properties()
    local props = obs.obs_properties_create()
    for i, replayDuration in ipairs(replayDurations) do
        local hotkeyId = obs.obs_hotkey_register_frontend(string.format("Replay_%d_seconds", replayDuration),
                                                          "Replay " .. replayDuration .. " Seconds", onHotkey)
        obs.obs_properties_add_path(props, string.format("Replay_%d_seconds", replayDuration), "Replay " .. replayDuration .. " Seconds",
                                    obs.OBS_PATH_FILE, "", "json files (*.json)")
    end
    return props
end
