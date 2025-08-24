"""
Penalty Shootout Dashboard
A lightweight GUI for managing penalty shootouts with automatic logic.
"""
import json
import os
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import customtkinter as ctk
from tkinter import messagebox

from src.core.gameinfo import GameInfoStore
from src.config.settings import AppConfig
from src.licensing.license_details_window import show_license_details
from src.ui import get_icon_path, get_icon
from src.ui.footer_label import create_footer
from src.core.logger import get_logger


@dataclass
class PenaltyState:
    """Data structure for penalty shootout state"""
    initial: int = 5
    starts: str = "home"  # "home" | "away"
    stage: str = "initial"  # "initial" | "sudden" | "done"
    home: List[str] = None  # type: ignore
    away: List[str] = None  # type: ignore
    next: Optional[Dict[str, Any]] = None  # {"team": "home", "index": 3} or None
    winner: Optional[str] = None  # "home" | "away" | None
    
    def __post_init__(self):
        if self.home is None:
            self.home = ["pending"] * self.initial
        if self.away is None:
            self.away = ["pending"] * self.initial
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PenaltyState':
        return cls(**data)


class PenaltyDashboard(ctk.CTkToplevel):
    """Main penalty shootout dashboard window"""
    
    def __init__(self, parent, instance_number: int = 1):
        super().__init__(parent)
        
        self.instance_number = instance_number
        self.game_store = GameInfoStore(instance_number)
        
        # Initialize penalty state
        self.penalty_state = self._load_penalty_state()
        # Ensure computed fields (stage/next/winner) are consistent at open
        self._recompute_penalty_logic()
        
        # Cache team data for fast access - load once and reuse
        self._cached_team_names = None
        self._cache_team_data()
        
        # Undo/Redo system
        self.history = deque(maxlen=200)
        self.history_index = -1
        self._save_to_history()
        
        # UI state
        self.allow_edits_after_finish = False
        self._updating_ui = False
        
        # Performance optimizations
        self._last_ui_state = None
        self._update_pending = False
        
        # Configure window
        self._configure_window()
        
        # Build UI
        self._build_ui()
        
        # Load initial state
        self._update_ui_from_state()
        
        # Start auto-save timer
        self._start_auto_save()
        self._log = get_logger(__name__)
    
    def _configure_window(self):
        """Configure window properties"""
        # Get cached team names for window title (no redundant calls)
        home_display, away_display = self._get_team_display_names()
        
        self.title(f"Penalty - Campo {self.instance_number}")
        self.geometry("585x585")
        self.minsize(585, 585)
        
        # Set icon
        try:
            self.iconbitmap(get_icon_path("field"))
        except:
            pass
        
        # Apply window configuration - use non-modal like timer window
        from src.utils import configure_window, center_window_on_parent
        non_modal_config = {
            "overrideredirect": False,
            "topmost": True,
            "grab_set": False,  # Non-modal
            "resizable": (False, False),
            "focus_force": True,
            "lift": True,
            "transient": True
        }
        configure_window(self, non_modal_config, self.master)  # type: ignore
        center_window_on_parent(self, self.master, 585, 585)  # type: ignore
        
        # Ensure window is visible and focused
        self.deiconify()
        self.lift()
        self.focus_force()
        self.grab_release()  # Ensure no grab is set
    
    def _build_ui(self):
        """Build the main UI components"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
        
        # Control panel
        self._build_control_panel(main_frame)
        
        # Penalty grid
        self._build_penalty_grid(main_frame)
        
        # Status bar
        self._build_status_bar(main_frame)

        # Footer
        try:
            create_footer(self, copyright_text=f"Campo {self.instance_number}", show_datetime=False, show_license_status=False, show_activate_button=False)
        except Exception:
            pass
    
    def _build_control_panel(self, parent):
        """Build the control panel with settings and actions"""
        control_frame = ctk.CTkFrame(parent)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Top row - Settings
        settings_frame = ctk.CTkFrame(control_frame)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # Initial penalties
        ctk.CTkLabel(settings_frame, text="Initial Penalties:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.initial_var = ctk.StringVar(value=str(self.penalty_state.initial))
        initial_entry = ctk.CTkEntry(settings_frame, textvariable=self.initial_var, width=60)
        initial_entry.grid(row=0, column=1, padx=5, pady=5)
        initial_entry.bind("<KeyRelease>", self._on_initial_changed)
        
        # Starting team
        # Get team names for display
        home_display, away_display = self._get_team_display_names()
        starts_label = ctk.CTkLabel(settings_frame, text=f"Starts:")
        starts_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Set initial value with team name display
        starts_display_value = f"home ({home_display})" if self.penalty_state.starts == "home" else f"away ({away_display})"
        self.starts_var = ctk.StringVar(value=starts_display_value)
        # Create option menu with team names but keep internal values
        starts_combo = ctk.CTkOptionMenu(
            settings_frame,
            values=[f"home ({home_display})", f"away ({away_display})"],
            variable=self.starts_var,
            command=self._on_starts_changed
        )
        starts_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Allow edits after finish
        self.allow_edits_var = ctk.BooleanVar(value=self.allow_edits_after_finish)
        allow_edits_check = ctk.CTkCheckBox(
            settings_frame,
            text="Allow edits after finish",
            variable=self.allow_edits_var,
            command=self._on_allow_edits_changed
        )
        allow_edits_check.grid(row=0, column=4, padx=20, pady=5)
        
        # Bottom row - Actions
        actions_frame = ctk.CTkFrame(control_frame)
        actions_frame.pack(fill="x", padx=10, pady=5)
        
        # Action buttons
        ctk.CTkButton(
            actions_frame,
            text="Reset",
            command=self._reset_penalties,
            width=80
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            actions_frame,
            text="Undo",
            command=self._undo,
            width=80
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            actions_frame,
            text="Redo",
            command=self._redo,
            width=80
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(
            actions_frame,
            text="Save",
            command=self._save_penalties,
            width=80
        ).pack(side="left", padx=5, pady=5)
    
    def _build_penalty_grid(self, parent):
        """Build the penalty grid with home and away teams"""
        grid_frame = ctk.CTkFrame(parent)
        grid_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Header with team names from gameinfo.json
        header_frame = ctk.CTkFrame(grid_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Get team names from gameinfo.json
        home_display, away_display = self._get_team_display_names()
        
        ctk.CTkLabel(header_frame, text=home_display, font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_SUBTITLE, "bold")).pack(side="left", padx=20)
        ctk.CTkLabel(header_frame, text=away_display, font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_SUBTITLE, "bold")).pack(side="right", padx=20)
        
        # Scrollable grid container with fixed height to show all 5 initial kicks
        self.grid_container = ctk.CTkScrollableFrame(grid_frame, height=300)
        self.grid_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Grid will be populated dynamically
        self.penalty_buttons = {"home": [], "away": []}
        self.row_frames = []  # Initialize row_frames
        self._update_penalty_grid()
    
    def _build_status_bar(self, parent):
        """Build the status bar showing current state"""
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", pady=(0, 5))
        
        # Status labels
        self.stage_label = ctk.CTkLabel(status_frame, text="Stage: Initial")
        self.stage_label.pack(side="left", padx=10, pady=5)
        
        self.next_label = ctk.CTkLabel(status_frame, text="Next: Home #1")
        self.next_label.pack(side="left", padx=10, pady=5)
        
        self.winner_label = ctk.CTkLabel(status_frame, text="Winner: None")
        self.winner_label.pack(side="right", padx=10, pady=5)
    
    def _update_penalty_grid(self):
        """Update the penalty grid based on current state"""
        # Always show at least the first 5 kicks (initial series)
        min_rows = 5
        
        # Determine max rows needed (at least 5, or more if in sudden death)
        max_rows = max(min_rows, len(self.penalty_state.home), len(self.penalty_state.away))
        
        # Check if we need to recreate the grid
        need_recreate = (
            not hasattr(self, 'penalty_buttons') or  # First time
            self._is_penalty_reset()  # Grid was reset to initial state
        )
        
        if need_recreate:
            self._create_penalty_grid(max_rows)
        elif len(self.penalty_buttons["home"]) < max_rows:
            # Smoothly expand the grid by adding new rows
            self._expand_penalty_grid(max_rows)
        else:
            # Just update existing buttons
            self._update_existing_buttons()
        
        # Auto-scroll to current yellow highlighted kick
        self._scroll_to_current_kick()
    
    def _get_team_display_names(self) -> tuple[str, str]:
        """Get display names for home and away teams from cached data"""
        # Return cached team names to avoid repeated GameInfoStore calls
        if self._cached_team_names is None:
            self._cache_team_data()
        
        return self._cached_team_names or ("Home", "Away")
    
    def _cache_team_data(self):
        """Cache team data once to avoid repeated GameInfoStore calls"""
        try:
            # Load team data once and cache it
            home_name = self.game_store.get("home_name", "Home")
            away_name = self.game_store.get("away_name", "Away")
            home_abbr = self.game_store.get("home_abbr", "")
            away_abbr = self.game_store.get("away_abbr", "")
            
            # Use abbreviations if available, otherwise use full names
            home_display = home_name if home_name else home_abbr
            away_display = away_name if away_name else away_abbr
            
            # Cache the result
            self._cached_team_names = (home_display, away_display)
            
        except Exception as e:
            try:
                get_logger(__name__).warning("penalty_cache_team_data_failed", exc_info=True)
            except Exception:
                pass
            # Fallback to defaults
            self._cached_team_names = ("Home", "Away")
    
    def _refresh_team_cache(self):
        """Refresh team data cache - call if team names change during game"""
        self._cached_team_names = None
        self._cache_team_data()
    
    def _extend_arrays_if_needed(self, index: int):
        """Extend penalty arrays to accommodate the given index"""
        while len(self.penalty_state.home) <= index:
            self.penalty_state.home.append("pending")
        while len(self.penalty_state.away) <= index:
            self.penalty_state.away.append("pending")
    
    def _update_state_and_ui(self, save_history: bool = True, persist: bool = True):
        """Unified method to update state, recompute logic, update UI, and save"""
        # Recompute logic
        self._recompute_penalty_logic()
        
        # Update UI
        self._update_ui_from_state()
        
        # Save to history if requested
        if save_history:
            self._save_to_history()
        
        # Persist immediately if requested
        if persist:
            self._persist_state()
    
    def _is_penalty_reset(self) -> bool:
        """Check if penalties were reset to initial state"""
        if not hasattr(self, 'penalty_buttons'):
            return False
        
        # Check if we have more than 5 rows but penalties are back to initial state
        if len(self.penalty_buttons["home"]) > 5:
            # Check if all penalties are pending (reset state)
            all_pending = all(
                status == "pending" 
                for status in self.penalty_state.home[:5] + self.penalty_state.away[:5]
            )
            # Check if we're back to initial stage
            is_initial_stage = self.penalty_state.stage == "initial"
            # Check if next penalty is the first one
            is_first_penalty = (
                self.penalty_state.next and 
                self.penalty_state.next["index"] == 0
            )
            
            return bool(all_pending and is_initial_stage and is_first_penalty)
    
        return False
    
    def _expand_penalty_grid(self, new_max_rows: int):
        """Smoothly expand the grid by adding new rows without recreating existing ones"""
        current_rows = len(self.penalty_buttons["home"])
        
        # Add new rows to reach new_max_rows
        for row in range(current_rows, new_max_rows):
            row_frame = ctk.CTkFrame(self.grid_container)
            row_frame.pack(fill="x", pady=3)
            self.row_frames.append(row_frame)
            
            # Row number
            ctk.CTkLabel(row_frame, text=f"#{row + 1}", width=40).pack(side="left", padx=5)
            
            # Home penalty
            home_frame = ctk.CTkFrame(row_frame)
            home_frame.pack(side="left", fill="x", expand=True, padx=5)
            
            # Always create buttons for new rows since they'll be used for penalties
            home_status = self.penalty_state.home[row] if row < len(self.penalty_state.home) else "pending"
            home_score_btn, home_miss_btn = self._create_penalty_buttons(
                home_frame, 
                home_status, 
                "home", 
                row
            )
            self.penalty_buttons["home"].append((home_score_btn, home_miss_btn))
            
            # Away penalty
            away_frame = ctk.CTkFrame(row_frame)
            away_frame.pack(side="right", fill="x", expand=True, padx=5)
            
            # Always create buttons for new rows since they'll be used for penalties
            away_status = self.penalty_state.away[row] if row < len(self.penalty_state.away) else "pending"
            away_score_btn, away_miss_btn = self._create_penalty_buttons(
                away_frame, 
                away_status, 
                "away", 
                row
            )
            self.penalty_buttons["away"].append((away_score_btn, away_miss_btn))
        
        # Update all buttons to reflect current state
        self._update_existing_buttons()
    
    def _create_penalty_grid(self, max_rows: int):
        """Create the penalty grid from scratch"""
        # Clear existing grid
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        
        self.penalty_buttons = {"home": [], "away": []}
        self.row_frames = []
        
        for row in range(max_rows):
            row_frame = ctk.CTkFrame(self.grid_container)
            row_frame.pack(fill="x", pady=3)
            self.row_frames.append(row_frame)
            
            # Row number
            ctk.CTkLabel(row_frame, text=f"#{row + 1}", width=40).pack(side="left", padx=5)
            
            # Home penalty
            home_frame = ctk.CTkFrame(row_frame)
            home_frame.pack(side="left", fill="x", expand=True, padx=5)
            
            if row < len(self.penalty_state.home):
                home_score_btn, home_miss_btn = self._create_penalty_buttons(
                    home_frame, 
                    self.penalty_state.home[row], 
                    "home", 
                    row
                )
                self.penalty_buttons["home"].append((home_score_btn, home_miss_btn))
            else:
                # Add empty space
                ctk.CTkLabel(home_frame, text="").pack(fill="both", expand=True)
            
            # Away penalty
            away_frame = ctk.CTkFrame(row_frame)
            away_frame.pack(side="right", fill="x", expand=True, padx=5)
            
            if row < len(self.penalty_state.away):
                away_score_btn, away_miss_btn = self._create_penalty_buttons(
                    away_frame, 
                    self.penalty_state.away[row], 
                    "away", 
                    row
                )
                self.penalty_buttons["away"].append((away_score_btn, away_miss_btn))
            else:
                # Add empty space
                ctk.CTkLabel(away_frame, text="").pack(fill="both", expand=True)
    
    def _update_existing_buttons(self):
        """Update existing buttons without recreating the grid"""
        # Update home team buttons
        for row, (score_btn, miss_btn) in enumerate(self.penalty_buttons["home"]):
            status = self.penalty_state.home[row] if row < len(self.penalty_state.home) else "pending"
            self._update_button_appearance(score_btn, miss_btn, status, "home", row)
        
        # Update away team buttons
        for row, (score_btn, miss_btn) in enumerate(self.penalty_buttons["away"]):
            status = self.penalty_state.away[row] if row < len(self.penalty_state.away) else "pending"
            self._update_button_appearance(score_btn, miss_btn, status, "away", row)
    
    def _update_button_appearance(self, score_btn, miss_btn, status: str, team: str, index: int):
        """Update button appearance without recreating buttons"""
        # Check if this is the next penalty
        is_next = (self.penalty_state.next and 
                  self.penalty_state.next["team"] == team and 
                  self.penalty_state.next["index"] == index)
        
        # Base colors (neutral blue)
        score_fg_color = "#2d2d5a"
        score_hover_color = "#3a3a6a"
        miss_fg_color = "#2d2d5a"
        miss_hover_color = "#3a3a6a"

        # Emphasize current status with color while keeping labels constant
        if status == "goal":
            score_fg_color = "#2d5a2d"  # green active
            score_hover_color = "#3a6a3a"
            miss_fg_color = "#1f1f3f"   # dim for the other button
            miss_hover_color = "#2a2a4f"
        elif status == "fail":
            miss_fg_color = "#5a2d2d"   # red active
            miss_hover_color = "#6a3a3a"
            score_fg_color = "#1f1f3f"  # dim for the other button
            score_hover_color = "#2a2a4f"

        # Yellow border highlight for the next pending penalty only
        border_width = 1
        border_color = "#1e1e2e"
        if status == "pending" and is_next:
            border_width = 3
            border_color = "#ffcc00"
        
        # Update button properties
        score_btn.configure(
            fg_color=score_fg_color,
            hover_color=score_hover_color,
            border_width=border_width,
            border_color=border_color
        )
        miss_btn.configure(
            fg_color=miss_fg_color,
            hover_color=miss_hover_color,
            border_width=border_width,
            border_color=border_color
        )
    
    def _scroll_to_current_kick(self):
        """Scroll to the current yellow highlighted kick"""
        if not self.penalty_state.next or not hasattr(self, 'row_frames') or not self.row_frames:
            return
            
        current_index = self.penalty_state.next["index"]
        
        # Only scroll if we're beyond the first 5 kicks (sudden death)
        if current_index >= 5 and current_index < len(self.row_frames):
            # Calculate the target row position
            target_row = current_index
            
            # Get the scrollable frame's canvas
            canvas = self.grid_container._parent_canvas
            
            # Calculate the y position of the target row
            row_frame = self.row_frames[target_row]
            row_y = row_frame.winfo_y()
            
            # Scroll to show the target row in the middle of the visible area
            canvas_height = canvas.winfo_height()
            target_y = max(0, row_y - canvas_height // 2)
            
            # Smooth scroll to the target position
            canvas.yview_moveto(target_y / canvas.winfo_reqheight())
    
    def _create_penalty_buttons(self, parent, status: str, team: str, index: int) -> Tuple[ctk.CTkButton, ctk.CTkButton]:
        """Create score and miss buttons for a specific team and index"""
        # Create container frame for the two buttons
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Check if this is the next penalty
        is_next = (self.penalty_state.next and 
                  self.penalty_state.next["team"] == team and 
                  self.penalty_state.next["index"] == index)
        
        # Colors and labels remain constant for alignment
        score_text = "Score"
        miss_text = "Miss"

        # Base colors (neutral blue)
        score_fg_color = "#2d2d5a"
        score_hover_color = "#3a3a6a"
        miss_fg_color = "#2d2d5a"
        miss_hover_color = "#3a3a6a"

        # Emphasize current status with color while keeping labels constant
        if status == "goal":
            score_fg_color = "#2d5a2d"  # green active
            score_hover_color = "#3a6a3a"
            miss_fg_color = "#1f1f3f"   # dim for the other button
            miss_hover_color = "#2a2a4f"
        elif status == "fail":
            miss_fg_color = "#5a2d2d"   # red active
            miss_hover_color = "#6a3a3a"
            score_fg_color = "#1f1f3f"  # dim for the other button
            score_hover_color = "#2a2a4f"

        # Yellow border highlight for the next pending penalty only
        border_width = 1
        border_color = "#1e1e2e"
        if status == "pending" and is_next:
            border_width = 3
            border_color = "#ffcc00"
        
        # Create score button
        score_btn = ctk.CTkButton(
            button_frame,
            text=score_text,
            fg_color=score_fg_color,
            hover_color=score_hover_color,
            width=80,
            height=50,
            border_width=border_width,
            border_color=border_color,
            command=lambda: self._on_score_click(team, index)
        )
        score_btn.pack(side="left", fill="both", expand=True, padx=(0, 1))
        
        # Create miss button
        miss_btn = ctk.CTkButton(
            button_frame,
            text=miss_text,
            fg_color=miss_fg_color,
            hover_color=miss_hover_color,
            width=80,
            height=50,
            border_width=border_width,
            border_color=border_color,
            command=lambda: self._on_miss_click(team, index)
        )
        miss_btn.pack(side="right", fill="both", expand=True, padx=(1, 0))
        
        return score_btn, miss_btn
    
    def _on_score_click(self, team: str, index: int):
        """Handle score button click"""
        if self.penalty_state.stage == "done" and not self.allow_edits_after_finish:
            messagebox.showwarning("Penalty Finished", "Penalty shootout is finished. Enable 'Allow edits after finish' to continue editing.")
            return
        
        # Extend arrays if needed
        self._extend_arrays_if_needed(index)
        
        # Set to goal
        if team == "home":
            self.penalty_state.home[index] = "goal"
        else:
            self.penalty_state.away[index] = "goal"
        
        # Update state and UI
        self._update_state_and_ui()
    
    def _on_miss_click(self, team: str, index: int):
        """Handle miss button click"""
        if self.penalty_state.stage == "done" and not self.allow_edits_after_finish:
            messagebox.showwarning("Penalty Finished", "Penalty shootout is finished. Enable 'Allow edits after finish' to continue editing.")
            return
        
        # Extend arrays if needed
        self._extend_arrays_if_needed(index)
        
        # Set to fail
        if team == "home":
            self.penalty_state.home[index] = "fail"
        else:
            self.penalty_state.away[index] = "fail"
        
        # Update state and UI
        self._update_state_and_ui()
    
    def _on_initial_changed(self, event=None):
        """Handle initial penalties count change"""
        try:
            new_initial = int(self.initial_var.get())
            if new_initial < 1:
                return
            
            self.penalty_state.initial = new_initial
            
            # Extend arrays if needed
            while len(self.penalty_state.home) < new_initial:
                self.penalty_state.home.append("pending")
            while len(self.penalty_state.away) < new_initial:
                self.penalty_state.away.append("pending")
            
            # Update state and UI
            self._update_state_and_ui()
            
        except ValueError:
            pass
    
    def _on_starts_changed(self, value):
        """Handle starting team change"""
        # Extract the internal value from display format (e.g., "home (SCP)" -> "home")
        if value.startswith("home"):
            internal_value = "home"
        elif value.startswith("away"):
            internal_value = "away"
        else:
            internal_value = value  # Fallback
            
        self.penalty_state.starts = internal_value
        self._update_state_and_ui()
    
    def _on_allow_edits_changed(self):
        """Handle allow edits after finish toggle"""
        self.allow_edits_after_finish = self.allow_edits_var.get()
    
    def _recompute_penalty_logic(self):
        """Recompute penalty logic including stage, winner, and next, based solely on data."""
        s = self.penalty_state

        def count_taken(seq: List[str], limit: int | None = None) -> int:
            rng = seq if limit is None else seq[:limit]
            return sum(1 for x in rng if x in ("goal", "fail"))

        def count_goals(seq: List[str], limit: int | None = None) -> int:
            rng = seq if limit is None else seq[:limit]
            return sum(1 for x in rng if x == "goal")

        initial = max(1, int(s.initial))
        home_taken_initial = count_taken(s.home, initial)
        away_taken_initial = count_taken(s.away, initial)
        home_goals_total = count_goals(s.home, None)
        away_goals_total = count_goals(s.away, None)
        # Goals in the initial series only
        home_goals_initial = count_goals(s.home, initial)
        away_goals_initial = count_goals(s.away, initial)

        # Default reset
        s.winner = None
        s.next = None

        # Case 1: Still in initial series
        if home_taken_initial < initial or away_taken_initial < initial:
            s.stage = "initial"

            # Check for early finish during initial series
            # Early-end test (strict ">"): Home clinches if HS - AS > Arem, Away clinches if AS - HS > Hrem
            home_goals_so_far = count_goals(s.home, home_taken_initial)
            away_goals_so_far = count_goals(s.away, away_taken_initial)
            home_remaining = initial - home_taken_initial
            away_remaining = initial - away_taken_initial

            # Home clinches now if HS - AS > Arem
            if home_goals_so_far - away_goals_so_far > away_remaining:
                s.stage = "done"
                s.winner = "home"
                s.next = None
                return

            # Away clinches now if AS - HS > Hrem
            if away_goals_so_far - home_goals_so_far > home_remaining:
                s.stage = "done"
                s.winner = "away"
                s.next = None
                return

            # Determine next based on starting order and attempts taken
            s.next = self._find_next_penalty_initial(initial, home_taken_initial, away_taken_initial)
            return

        # Case 2: Initial series complete
        if home_taken_initial >= initial and away_taken_initial >= initial:
            # Decide tie/winner using ONLY the first `initial` kicks
            if home_goals_initial == away_goals_initial:
                # Sudden death
                s.stage = "sudden"

                # Compute extra taken beyond initial
                def extra_taken(seq: List[str]) -> int:
                    extra = seq[initial:]
                    return sum(1 for x in extra if x in ("goal", "fail"))

                home_extra_taken = extra_taken(s.home)
                away_extra_taken = extra_taken(s.away)

                # Check if we can determine a winner in sudden death
                # IMPORTANT: Winner can only be determined after BOTH teams have taken the same number of sudden-death kicks
                # (i.e., after the pair completes). Never finish right after the first team's kick.
                if home_extra_taken == away_extra_taken and home_extra_taken > 0:
                    current_idx = initial + home_extra_taken - 1
                    home_completed = current_idx < len(s.home) and s.home[current_idx] in ("goal", "fail")
                    away_completed = current_idx < len(s.away) and s.away[current_idx] in ("goal", "fail")
                    if home_completed and away_completed:
                        # Compare goals within sudden-death kicks taken so far (same count for both)
                        home_goals_sudden = sum(1 for x in s.home[initial:initial + home_extra_taken] if x == "goal")
                        away_goals_sudden = sum(1 for x in s.away[initial:initial + away_extra_taken] if x == "goal")

                        if home_goals_sudden > away_goals_sudden:
                            s.stage = "done"
                            s.winner = "home"
                            s.next = None
                            return
                        if away_goals_sudden > home_goals_sudden:
                            s.stage = "done"
                            s.winner = "away"
                            s.next = None
                            return
                        # If tied, continue to next pair

                # Determine next in sudden death order
                s.next = self._find_next_penalty_sudden(initial, home_extra_taken, away_extra_taken)
                return

            # If totals differ after initial, determine winner (using initial only)
            s.stage = "done"
            s.winner = "home" if home_goals_initial > away_goals_initial else "away"
            s.next = None
            return
    
    def _find_next_penalty_initial(self, initial: int, home_taken: int, away_taken: int) -> Optional[Dict[str, Any]]:
        """Next penalty during initial series, respecting starting order and alternating kicks."""
        starts = self.penalty_state.starts
        home = self.penalty_state.home
        away = self.penalty_state.away

        def first_pending(team: str) -> Optional[int]:
            seq = home if team == "home" else away
            limit = min(initial, len(seq))
            for i in range(limit):
                if seq[i] == "pending":
                    return i
            return None

        # Determine whose turn it is based on starting order and kicks taken
        if home_taken == away_taken:
            # Both teams have taken the same number of kicks, next is the starting team
            team = starts
            idx = home_taken if team == "home" else away_taken
            if idx < initial:
                seq = home if team == "home" else away
                if idx < len(seq) and seq[idx] == "pending":
                    return {"team": team, "index": idx}
        elif home_taken < away_taken:
            # Home team is behind, their turn
            team = "home"
            idx = home_taken
            if idx < initial and idx < len(home) and home[idx] == "pending":
                return {"team": team, "index": idx}
        else:
            # Away team is behind, their turn
            team = "away"
            idx = away_taken
            if idx < initial and idx < len(away) and away[idx] == "pending":
                return {"team": team, "index": idx}

        # Fallback: find first pending kick for any team
        home_pending = first_pending("home")
        away_pending = first_pending("away")
        
        if home_pending is not None:
            return {"team": "home", "index": home_pending}
        elif away_pending is not None:
            return {"team": "away", "index": away_pending}
        
        return None

    def _find_next_penalty_sudden(self, initial: int, home_extra_taken: int, away_extra_taken: int) -> Optional[Dict[str, Any]]:
        """Next penalty during sudden death, respecting starting order. Indices grow beyond initial."""
        starts = self.penalty_state.starts
        home = self.penalty_state.home
        away = self.penalty_state.away

        def idx_for(team: str, count_taken: int) -> int:
            return initial + count_taken

        def is_pending(team: str, idx: int) -> bool:
            seq = home if team == "home" else away
            # Auto-extend visual grid behavior handled on click; here just check bounds
            return idx >= 0 and (idx >= len(seq) or seq[idx] == "pending")

        # Determine whose turn it is based on starting order and extra kicks taken
        if home_extra_taken == away_extra_taken:
            # Both teams have taken the same number of extra kicks, next is the starting team
            team = starts
            idx = idx_for(team, home_extra_taken if team == "home" else away_extra_taken)
            if is_pending(team, idx):
                return {"team": team, "index": idx}
        elif home_extra_taken < away_extra_taken:
            # Home team is behind, their turn
            team = "home"
            idx = idx_for(team, home_extra_taken)
            if is_pending(team, idx):
                return {"team": team, "index": idx}
        else:
            # Away team is behind, their turn
            team = "away"
            idx = idx_for(team, away_extra_taken)
            if is_pending(team, idx):
                return {"team": team, "index": idx}

        return None
    
    def _update_ui_from_state(self):
        """Update UI to reflect current state with performance optimizations"""
        if self._updating_ui:
            return
        
        # Create a hash of current state to avoid unnecessary updates
        # Convert dict to tuple for hashing
        next_tuple = None
        if self.penalty_state.next:
            next_tuple = (self.penalty_state.next.get("team"), self.penalty_state.next.get("index"))
        
        current_state_hash = hash((
            self.penalty_state.stage,
            self.penalty_state.winner,
            tuple(self.penalty_state.home),
            tuple(self.penalty_state.away),
            next_tuple,
            self.penalty_state.initial,
            self.penalty_state.starts
        ))
        
        # Skip update if state hasn't changed
        if self._last_ui_state == current_state_hash:
            return
        
        self._updating_ui = True
        
        try:
            # Update control panel
            self.initial_var.set(str(self.penalty_state.initial))
            self.starts_var.set(self.penalty_state.starts)
            
            # Ensure grid can grow to show the next kick (sudden death)
            if self.penalty_state.next:
                target_idx = int(self.penalty_state.next.get("index", -1))
                if target_idx >= 0:
                    # Extend both arrays to keep rows aligned
                    self._extend_arrays_if_needed(target_idx)

            # Update penalty grid
            self._update_penalty_grid()
            
            # Update status bar
            self.stage_label.configure(text=f"Stage: {self.penalty_state.stage.title()}")
            
            if self.penalty_state.next:
                # Get team names for display
                home_display, away_display = self._get_team_display_names()
                team_name = home_display if self.penalty_state.next["team"] == "home" else away_display
                self.next_label.configure(text=f"Next: {team_name} #{self.penalty_state.next['index'] + 1}")
            else:
                self.next_label.configure(text="Next: None")
            
            winner_text = "None"
            if self.penalty_state.winner:
                # Get team names for winner display
                home_display, away_display = self._get_team_display_names()
                winner_text = home_display if self.penalty_state.winner == "home" else away_display
            self.winner_label.configure(text=f"Winner: {winner_text}")
            
            # Update state hash
            self._last_ui_state = current_state_hash
            
        finally:
            self._updating_ui = False
    
    def _save_to_history(self):
        """Save current state to history for undo/redo"""
        # Remove any states after current index
        while len(self.history) > self.history_index + 1:
            self.history.pop()
        
        # Add current state
        self.history.append(PenaltyState.from_dict(self.penalty_state.to_dict()))
        self.history_index = len(self.history) - 1
    
    def _undo(self):
        """Undo last action"""
        if self.history_index > 0:
            self.history_index -= 1
            self.penalty_state = PenaltyState.from_dict(self.history[self.history_index].to_dict())
            self._update_ui_from_state()
    
    def _redo(self):
        """Redo last undone action"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.penalty_state = PenaltyState.from_dict(self.history[self.history_index].to_dict())
            self._update_ui_from_state()
    
    def _reset_penalties(self):
        """Reset penalty shootout to initial state"""
        if messagebox.askyesno("Reset Penalties", "Are you sure you want to reset the penalty shootout?"):
            self.penalty_state = PenaltyState()
            self._update_state_and_ui()
    
    def _load_penalty_state(self) -> PenaltyState:
        """Load penalty state from gameinfo.json with fast caching"""
        try:
            # GameInfoStore already caches data for fast access
            penalties_data = self.game_store.get("penalties")
            if penalties_data and isinstance(penalties_data, dict):
                return PenaltyState.from_dict(penalties_data)
        except Exception as e:
            try:
                get_logger(__name__).error("penalty_state_load_error", exc_info=True)
            except Exception:
                pass
        
        # Return default state if no data or error
        return PenaltyState()
    
    def _save_penalties(self):
        """Save penalty state to gameinfo.json with fast persistence"""
        try:
            self._persist_state()
            messagebox.showinfo("Saved", "Penalty shootout state saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save penalty state: {e}")

    def _persist_state(self) -> None:
        """Persist current penalty state immediately with optimized GameInfoStore."""
        try:
            # GameInfoStore handles buffering and efficient disk writes
            self.game_store.set("penalties", self.penalty_state.to_dict())
        except Exception as e:
            try:
                self._log.error("penalty_persist_error", exc_info=True)
            except Exception:
                pass
    
    def _start_auto_save(self):
        """Start auto-save timer with optimized GameInfoStore"""
        def auto_save():
            try:
                self._persist_state()
            except Exception as e:
                try:
                    self._log.error("penalty_auto_save_error", exc_info=True)
                except Exception:
                    pass
            finally:
                # Schedule next auto-save in 5 seconds
                self.after(5000, auto_save)
        
        # Start auto-save after 5 seconds
        self.after(5000, auto_save)
    
    def on_closing(self):
        """Handle window closing with optimized save"""
        try:
            self._persist_state()
        except Exception as e:
            try:
                self._log.error("penalty_save_on_close_error", exc_info=True)
            except Exception:
                pass
        
        self.destroy()


def open_penalty_dashboard(parent, instance_number: int = 1):
    """Open penalty dashboard window"""
    dashboard = PenaltyDashboard(parent, instance_number)
    dashboard.protocol("WM_DELETE_WINDOW", dashboard.on_closing)
    return dashboard
