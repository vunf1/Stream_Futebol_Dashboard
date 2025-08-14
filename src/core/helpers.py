# helpers/helpers.py
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import customtkinter as ctk

from .filenames import BASE_FOLDER_PATH, get_env
from ..config import AppConfig


def save_teams_to_json(teams):
    json_path = os.path.join(BASE_FOLDER_PATH, AppConfig.TEAMS_BACKUP_FILENAME)
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        print(f"📁 Backup JSON criado: {json_path}")
    except Exception as e:
        print(f"❌ Falha ao criar backup JSON: {e}")
        return
        
def load_teams_from_json():
    json_path = os.path.join(BASE_FOLDER_PATH, AppConfig.TEAMS_BACKUP_FILENAME)
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            teams = json.load(f)
        print(f"📥 Backup JSON carregado: {json_path}")
        return teams
    except FileNotFoundError:
        print(f"⚠️ Arquivo de backup não encontrado: {json_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Falha ao decodificar JSON em '{json_path}': {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao carregar backup JSON: {e}")
        return False
    
def prompt_for_pin(parent):
    """
    Shows a modal, centered PIN prompt with a clean professional design.
    Returns True if the user enters `correct_pin`, False otherwise (or on Cancel).
    """
    correct_pin = get_env("PIN")
    print(f"🔐 PIN loaded from environment: {correct_pin}")
    if not correct_pin:
        print("❌ No PIN found in environment variables")
        return False
    while True:
        # Create modal dialog using window_utils but with minimal initial configuration
        print("🔐 Creating PIN prompt window...")
        from ..ui.window_utils import create_modal_dialog, center_window_on_screen_with_offset
        
        # Create window with minimal configuration to prevent flickering
        win = ctk.CTkToplevel(parent)
        win.title("PIN")
        win.geometry("320x176")
        
        # Hide window immediately to prevent any visual flash
        win.withdraw()
        
        # Position window while hidden
        center_window_on_screen_with_offset(win, 320, 176, -50)
        
        print(f"🔐 PIN window created: {win}")
        print(f"🔐 PIN window exists: {win.winfo_exists()}")
        
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
        header_frame.pack(fill="x", padx=12, pady=(8, 6))
        
        # Title with icon (smaller font and padding)
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔐 Admin Access Required",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90")
        )
        title_label.pack(pady=4)
        
        # Subtitle (smaller font and padding)
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Please enter your PIN to continue",
            font=("Segoe UI", 9),
            text_color=("gray50", "gray60")
        )
        subtitle_label.pack(pady=(0, 4))
        
        # Input section (adjusted spacing)
        input_frame = ctk.CTkFrame(
            main_frame,
            fg_color="transparent"
        )
        input_frame.pack(fill="x", padx=20, pady=8)
        
        # PIN entry with better styling (reduced height)
        entry = ctk.CTkEntry(
            input_frame,
            show="•",
            width=240,
            height=32,
            font=("Segoe UI", 12),
            placeholder_text="Enter PIN...",
            corner_radius=8,
            border_width=2,
            border_color=("gray70", "gray40")
        )
        entry.pack(pady=6)
        
        # Ensure proper cleanup
        result: dict[str, Optional[str]] = {"value": None}
        
        def cleanup():
            try:
                if win.winfo_exists():
                    print("🔐 Cleaning up PIN window...")
                    win.destroy()
            except Exception as e:
                print(f"🔐 Error during cleanup: {e}")
                pass
        
        # Add custom compact footer near the PIN entry
        # Create footer frame with limited width
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=25)
        footer_frame.pack(fill="x", padx=8, pady=(2, 8))
        footer_frame.pack_propagate(False)  # Maintain height
        
        # Create a constrained row container for footer elements
        footer_row = ctk.CTkFrame(footer_frame, fg_color="transparent")
        footer_row.pack(expand=True, fill="both", pady=2)
        
        # Left side - Copyright (constrained width)
        copyright_container = ctk.CTkFrame(footer_row, fg_color="transparent")
        copyright_container.pack(side="left", fill="y", padx=(4, 0))
        
        copyright_label = ctk.CTkLabel(
            copyright_container, 
            text="© 2025 Vunf1", 
            font=("Segoe UI Emoji", 9), 
            text_color="gray"
        )
        copyright_label.pack(side="left")
        
        # Center spacer to push close button to right
        spacer = ctk.CTkFrame(footer_row, fg_color="transparent")
        spacer.pack(side="left", expand=True, fill="x")
        
        # Right side - Close button (constrained width)
        close_container = ctk.CTkFrame(footer_row, fg_color="transparent")
        close_container.pack(side="right", fill="y", padx=(0, 4))
        
        close_button = ctk.CTkButton(
            close_container, 
            text="✕", 
            width=20, 
            height=20,
            font=("Segoe UI Emoji", 10, "bold"),
            fg_color="transparent",
            hover_color="#2b2b2b",
            text_color="#888888",
            corner_radius=10,
            command=cleanup
        )
        close_button.pack(side="right")
        
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
        
        # Focus management
        print("🔐 Setting window focus...")
        win.focus_force()
        entry.focus_set()
        
        # Define event handlers
        def on_submit(event=None):
            result["value"] = entry.get().strip()
            cleanup()
            
        def on_cancel(event=None):
            result["value"] = None
            cleanup()
            
        def on_close(event=None):
            result["value"] = None
            cleanup()
        
        # Bind keyboard events only
        entry.bind("<Return>", on_submit)
        entry.bind("<Escape>", on_cancel)
        
        print("🔐 Waiting for window to close...")
        
        win.wait_window()
        print("🔐 Window closed, checking result...")
        
        if result["value"] is None:
            print("🔒 PIN prompt cancelled")
            return False
        if result["value"] == correct_pin:
            print("🔓 PIN validated successfully")
            return True
        
        print("🔒 Access Denied")
        print("Incorrect PIN. Please try again.")