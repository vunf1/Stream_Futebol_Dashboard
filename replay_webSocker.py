import obswebsocket
import obswebsocket.requests as obsrequests
import time

# Replay via WebSocket
ip = "ipaddress"
port = 4455
passWebSocket = "dumdum"
ws = obswebsocket.obsws(ip, port, passWebSocket)
ws.connect()

# Set the replay buffer lengths in seconds
replay_durations = [5, 8, 10]

# Function to handle saving replays
def save_replay(replay_duration):
    replay_name = f"Replay_{replay_duration}_seconds"
    print(f"Saving replay for {replay_duration} seconds.")
    ws.call(obsrequests.SaveReplayBuffer(replay_name, "", obsrequests.SaveReplayBuffer.ACTION_STOP, replay_duration * 1000))

# Function to handle hotkey presses
def on_hotkey(pressed, hotkey_id):
    for replay_duration in replay_durations:
        hotkey_name = f"Replay_{replay_duration}_seconds"
        if hotkey_id == hotkey_name and pressed:
            save_replay(replay_duration)

# Register hotkeys
for replay_duration in replay_durations:
    hotkey_name = f"Replay_{replay_duration}_seconds"
    hotkey_id = ws.call(obsrequests.GetSceneItemProperties(hotkey_name))
    ws.call(obsrequests.RegisterHotkey(hotkey_id.getHotkeyId(), hotkey_name))

# Register the hotkey press callback
ws.register(on_hotkey)

try:
    # Keep the script running to listen for hotkey presses
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

# Disconnect from OBS
ws.disconnect()
