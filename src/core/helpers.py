# helpers/helpers.py
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import customtkinter as ctk

from .filenames import BASE_FOLDER_PATH, get_env
from .path_finder import get_path_finder
import time
import json as _json
from ..core.file_cache import read_json_cached, write_json_sync
from ..core.logger import get_logger
from ..config import AppConfig


_log = get_logger(__name__)

def save_teams_to_json(teams):
    json_path = os.path.join(BASE_FOLDER_PATH, AppConfig.TEAMS_BACKUP_FILENAME)
    try:
        # Atomic write via file cache
        write_json_sync(json_path, teams if isinstance(teams, dict) else {})
        try:
            _log.info("teams_backup_saved", extra={"path": json_path})
        except Exception:
            pass
    except Exception as e:
        try:
            _log.error("teams_backup_save_failed", extra={"path": json_path}, exc_info=True)
        except Exception:
            pass
        return
        
def load_teams_from_json():
    json_path = os.path.join(BASE_FOLDER_PATH, AppConfig.TEAMS_BACKUP_FILENAME)
    try:
        data = read_json_cached(json_path, {})
        try:
            _log.info("teams_backup_loaded", extra={"path": json_path})
        except Exception:
            pass
        return data or False
    except Exception as e:
        try:
            _log.error("teams_backup_load_failed", extra={"path": json_path}, exc_info=True)
        except Exception:
            pass
        return False
    
def prompt_for_pin(parent):
    """
    Shows a modal, centered PIN prompt with a clean professional design.
    Returns True if the user enters `correct_pin`, False otherwise (or on Cancel).
    """
    correct_pin = get_env("PIN")
    if not correct_pin:
        # No PIN configured
        return False
    # PIN lockout/backoff state (persisted per user under LOCALAPPDATA)
    pf = get_path_finder()
    lock_dir = pf.user_local_appdir(AppConfig.LOCAL_APP_DIRNAME, "security")
    try:
        Path(lock_dir).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    lock_path = Path(lock_dir) / "pin.lock.json"

    max_attempts = 5
    lockout_minutes = 15
    backoff_cap_sec = 8

    def _read_lock():
        try:
            if lock_path.exists():
                return _json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"attempts": 0, "next_allowed": 0}

    def _write_lock(attempts: int, next_allowed: float):
        try:
            data = {"attempts": int(attempts), "next_allowed": float(next_allowed)}
            lock_path.write_text(_json.dumps(data), encoding="utf-8")
        except Exception:
            pass

    def _clear_lock():
        try:
            if lock_path.exists():
                lock_path.unlink()
        except Exception:
            pass

    # Read initial state; allow UI prompt unless hard lockout has been set by max attempts
    state = _read_lock()
    now = time.time()
    # Non-interactive test mode: simulate a wrong attempt without opening UI
    if os.getenv("PIN_PROMPT_NONINTERACTIVE") == "1":
        attempts = int(state.get("attempts", 0)) + 1
        if attempts >= max_attempts:
            _write_lock(0, now + (lockout_minutes * 60))
        else:
            _write_lock(attempts, now)
        return False

    # Compute remaining attempts for UI hint
    attempts_so_far = int(state.get("attempts", 0))
    attempts_left = max(0, max_attempts - attempts_so_far)

    while True:
        # Create modal dialog using window_utils but with minimal initial configuration
        # Create PIN prompt window
        from ..utils import create_modal_dialog, center_window_on_screen_with_offset
        
        # Create window with minimal configuration to prevent flickering
        win = ctk.CTkToplevel(parent)
        win.title("PIN")
        win.geometry("320x156")
        
        # Hide window immediately to prevent any visual flash
        win.withdraw()
        
        # Position window while hidden
        center_window_on_screen_with_offset(win, 320, 156, -50)
        
        # Window created
        
        # Create all UI components while window is hidden
        # Main container with modern styling
        main_frame = ctk.CTkFrame(
            win, 
            fg_color=("gray95", "gray15"),
            corner_radius=16
        )
        main_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Header section (reduced size)
        header_frame = ctk.CTkFrame(
            main_frame,
            fg_color=("gray90", "gray20"),
            corner_radius=8
        )
        header_frame.pack(fill="x", padx=12, pady=(6, 2))
        
        # Title with icon (smaller font and padding)
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔐 Admin Access Required",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90")
        )
        title_label.pack(pady=0)
        
        # Subtitle (smaller font and padding)
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Please enter PIN to continue",
            font=("Segoe UI", 9),
            text_color=("gray50", "gray60")
        )
        # Pack directly above attempts with zero gap
        subtitle_label.pack(pady=0)

        # (moved) Attempts/lock info will render below the input box
        
        # Input section (adjusted spacing)
        input_frame = ctk.CTkFrame(
            main_frame,
            fg_color="transparent"
        )
        input_frame.pack(fill="x", padx=20, pady=2)
        
        # PIN entry with better styling (reduced height)
        entry = ctk.CTkEntry(
            input_frame,
            show="•",
            width=240,
            height=22,
            font=("Segoe UI", 12),
            placeholder_text="Enter PIN...",
            corner_radius=8,
            border_width=2,
            border_color=("gray70", "gray40")
        )
        entry.pack(pady=2)

        # Attempts/lock info (moved below input, colored red for visibility)
        try:
            attempts_text = f"Attempts left: {attempts_left}"
            attempts_label = ctk.CTkLabel(
                input_frame,
                text=attempts_text,
                font=("Segoe UI", 9),
                text_color=(AppConfig.COLOR_ERROR, AppConfig.COLOR_ERROR)
            )
            attempts_label.pack(pady=(0, 0))
        except Exception:
            pass
        
        # Ensure proper cleanup
        result: dict[str, Optional[str]] = {"value": None}
        
        def cleanup():
            try:
                if win.winfo_exists():
                    # Avoid noisy prints; window cleanup
                    win.destroy()
            except Exception as e:
                # Swallow cleanup issues silently
                pass
        
        # Add custom compact footer near the PIN entry
        from src.ui.footer_label import create_footer
        footer = create_footer(
            main_frame, 
            show_datetime=False, 
            show_license_status=False, 
            show_activate_button=False,
            # Use layout that places footer higher
            custom_padding=(8, 2, 8, 6),
            footer_height=18
        )
        try:
            footer.pack_configure(pady=(1, 0))
        except Exception:
            pass
        
        # Now apply all window configuration at once while still hidden
        win.overrideredirect(True)
        win.resizable(False, False)
        
        # Ensure all UI updates are complete before showing
        win.update_idletasks()
        
        # Now show the fully configured and positioned window
        win.deiconify()
        
        # Apply modal behavior and focus only after window is visible
        win.grab_set()
        win.attributes('-topmost', True)
        win.lift()
        
        # Defer focus to entry until event loop is idle to ensure it takes effect
        def _set_focus():
            try:
                if entry.winfo_exists():
                    entry.focus_force()
            except Exception:
                pass

        win.after_idle(_set_focus)
        
        # Define event handlers
        def on_submit(event=None):
            val = entry.get().strip()
            if val == correct_pin:
                _clear_lock()
                result["value"] = val
                cleanup()
                return
            # Wrong PIN: update attempts immediately and keep window open (no flicker)
            state_now = _read_lock()
            attempts_now = int(state_now.get("attempts", 0)) + 1
            if attempts_now >= max_attempts:
                _write_lock(0, time.time() + (lockout_minutes * 60))
                try:
                    attempts_label.configure(text="Locked out; try again later")
                except Exception:
                    pass
                result["value"] = None  # deny
                try:
                    win.after(600, cleanup)
                except Exception:
                    cleanup()
                return
            else:
                _write_lock(attempts_now, time.time())
                try:
                    attempts_label.configure(text=f"Attempts left: {max(0, max_attempts - attempts_now)}")
                    entry.delete(0, 'end')
                    _set_focus()
                except Exception:
                    pass
                return
            
        def on_cancel(event=None):
            result["value"] = None
            cleanup()
            
        def on_close(event=None):
            result["value"] = None
            cleanup()
        
        # Bind keyboard events only
        entry.bind("<Return>", on_submit)
        entry.bind("<Escape>", on_cancel)
        
        # Wait for user input
        
        win.wait_window()
        # Window closed (only on success, cancel, or lockout path)
        if result["value"] is None:
            return False
        if result["value"] == correct_pin:
            _clear_lock()
            return True
        return False