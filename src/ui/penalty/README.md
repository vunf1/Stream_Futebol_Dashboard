# Penalty Shootout Dashboard

A comprehensive GUI for managing penalty shootouts with automatic logic for early finish detection and sudden death handling.

## Features

### 🎯 Core Functionality
- **Automatic Logic**: Detects early finish when one team can't be caught
- **Sudden Death**: Automatically transitions to sudden death when initial round ends in a tie
- **Real-time Updates**: UI updates automatically after every change
- **Auto-save**: Saves to gameinfo.json every 5 seconds and on window close

### 🎮 Interactive Controls
- **Click to Cycle**: Click penalty buttons to cycle through states: `pending` → `goal` → `fail` → `pending`
- **Visual Indicators**: 
  - ⚽ Green buttons for goals
  - ❌ Red buttons for misses
  - ? Blue buttons for pending
  - 🟡 Yellow highlight for next penalty
- **Infinite Growth**: Grid automatically expands for sudden death penalties

### ⚙️ Configuration
- **Initial Penalties**: Set number of initial penalties (default: 5)
- **Starting Team**: Choose which team starts (home/away)
- **Edit After Finish**: Toggle to allow editing after penalty shootout is complete

### 🔄 History Management
- **Undo/Redo**: Full undo/redo system with 200-step history
- **Reset**: Reset entire penalty shootout to initial state
- **Manual Save**: Save button for immediate persistence

### 📊 Status Display
- **Stage**: Shows current stage (Initial/Sudden/Done)
- **Next**: Indicates which team and penalty number is next
- **Winner**: Displays the winner when determined

## JSON Structure

The penalty state is stored in `gameinfo.json` under the `penalties` field:

```json
{
  "penalties": {
    "initial": 5,
    "starts": "home",              // "home" | "away"
    "stage": "initial",            // "initial" | "sudden" | "done"
    "home": ["goal","goal","fail","pending","pending"],
    "away": ["fail","goal","goal","pending","pending"],
    "next": { "team": "home", "index": 3 },  // or null when done
    "winner": null                              // "home" | "away" | null
  }
}
```

## Logic Rules

### Early Finish Detection
- If one team scores more goals than the other team can possibly score with remaining penalties, the shootout ends immediately
- Example: Home has 3 goals, Away has 0 goals, and Away has only 2 penalties remaining → Home wins

### Sudden Death
- When initial round ends in a tie, automatically transitions to sudden death
- Each team takes one penalty at a time until one team scores and the other misses
- Grid expands infinitely to accommodate additional penalties

### Next Penalty Logic
- **Initial Stage**: Finds next pending penalty within the initial round
- **Sudden Death**: Finds next pending penalty in the extended grid
- **Done Stage**: No next penalty (null)

## Usage

### Opening the Dashboard
1. Click the dice icon (🎲) in the main application toolbar
2. The penalty dashboard opens as a modal window
3. The dashboard is automatically connected to the current field instance

### Managing Penalties
1. **Set Initial Count**: Enter the number of initial penalties
2. **Choose Starting Team**: Select which team starts
3. **Click Penalty Buttons**: Cycle through goal/fail/pending states
4. **Monitor Status**: Watch the status bar for current stage and next penalty
5. **Use History**: Undo/Redo changes as needed

### Saving
- **Auto-save**: Occurs every 5 seconds automatically
- **Manual Save**: Click the "Save" button for immediate save
- **Close Save**: Automatically saves when closing the window

## Technical Details

### File Integration
- Saves to `gameinfo.json` in the field-specific section (e.g., `field_1`)
- Uses the existing `GameInfoStore` class for consistency
- Integrates with the existing auto-save and caching system

### Performance
- Lightweight GUI using CustomTkinter
- Efficient state management with dataclasses
- Debounced UI updates to prevent excessive redraws
- Memory-efficient history system with 200-step limit

### Error Handling
- Graceful handling of file I/O errors
- User-friendly error dialogs
- Fallback to default state on load errors
- Validation of user inputs

## Integration

The penalty dashboard is fully integrated into the main application:

- **Button Location**: Dice icon in the top toolbar
- **Instance Support**: Works with any field instance (defaults to instance 1)
- **Consistent Styling**: Matches the application's dark theme
- **Window Management**: Proper modal behavior and positioning

## Future Enhancements

Potential improvements for future versions:

- **Team Names**: Display actual team names from the game state
- **Sound Effects**: Audio feedback for goals and misses
- **Statistics**: Track penalty conversion rates
- **Export**: Export penalty results to external formats
- **Animation**: Smooth transitions between penalty states
