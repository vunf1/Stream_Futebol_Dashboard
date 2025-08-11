# edit_teams_ui.py
import customtkinter as ctk
from helpers.helpers import prompt_for_pin
from helpers.icons_provider import get_icon_path, get_icon
from helpers.notification.toast import show_message_notification
from assets.colors import COLOR_WARNING, COLOR_SUCCESS, COLOR_STOP
from helpers.top_c_child_parent import top_centered_child_to_parent
import re

class TeamManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, mongo):
        super().__init__(parent)
        self.mongo = mongo
        self.all_teams = {}  # Store all teams for filtering
        self.team_buttons = []  # Store team buttons for filtering
        self._icon_refs = []  # Store icon references
        self.selected_index = -1  # Track currently selected team
        self.visible_buttons = []  # Track visible buttons for navigation
        self.search_query = ""  # Current search query
        self.empty_state_widget = None  # Track empty state widget
        self._is_loading = True  # Track loading state

        if not self._prompt_for_pin():  # ask PIN first
            self.destroy()
            return
        
        # Configure window properties before showing
        child_w, child_h = 500, 600  # Increased size for better layout
        self.title("Team Manager")
        self.geometry("500x600")
        self.iconbitmap(get_icon_path("gear"))
        # Stagger window operations for smooth appearance
        self.after(50, lambda: self.attributes("-topmost", True))  # Faster (was 100ms, now 50ms)
        
        # Center the child window at the top of the parent
        top_centered_child_to_parent(self, parent, child_w, child_h)
        
        # Build UI structure first (without content)
        self._build_header()
        self._build_search_bar()
        self._build_team_list()
        
        # Show loading state
        self._show_loading_state()
        
        # Defer team loading for smooth appearance
        self.after(50, self._deferred_load_teams)  # Faster (was 100ms, now 50ms)
        
        # Focus and grab after a short delay
        self.after(25, self.focus_force)  # Faster (was 50ms, now 25ms)
        self.after(25, self.grab_set)  # Make this window modal - Faster (was 50ms, now 25ms)
        
        # Focus search entry after UI is ready
        self.after(75, lambda: self.search_entry.focus_set())  # Faster (was 150ms, now 75ms)
        
        # Show ready indicator
        self.after(150, self._show_ready_indicator)  # Faster (was 300ms, now 150ms)

    def _prompt_for_pin(self):
        return prompt_for_pin(self)
    
    def _show_ready_indicator(self):
        """Show a brief visual indicator that the window is ready"""
        # Flash the window title briefly
        original_title = self.title()
        self.title("Team Manager - Ready! ✅")
        self.after(1000, lambda: self.title(original_title))

    def _build_header(self):
        """Build the header section with title and subtitle"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Team Management",
            font=("Segoe UI", 24, "bold"),
            text_color=("gray20", "gray80")
        )
        title_label.pack(anchor="w")
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Manage your team database with advanced search and editing capabilities",
            font=("Segoe UI", 12),
            text_color=("gray50", "gray60")
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def _build_search_bar(self):
        """Build the search bar with icon and advanced filtering"""
        search_container = ctk.CTkFrame(self, fg_color="transparent")
        search_container.pack(fill="x", padx=20, pady=(0, 20))
        
        # Search bar frame with rounded corners and shadow effect
        search_frame = ctk.CTkFrame(
            search_container,
            corner_radius=15,
            fg_color=("gray95", "gray25"),
            border_width=1,
            border_color=("gray80", "gray30")
        )
        search_frame.pack(fill="x")
        
        # Search icon and entry
        search_icon = get_icon("search", 20)
        self._icon_refs.append(search_icon)
        
        # Create a frame for the search content
        search_content = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_content.pack(fill="x", padx=15, pady=12)
        
        # Search icon on the left
        icon_label = ctk.CTkLabel(
            search_content,
            text="",
            image=search_icon,
            fg_color="transparent"
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_content,
            placeholder_text="Search teams by name or abbreviation...",
            font=("Segoe UI", 14),
            height=35,
            fg_color="transparent",
            border_width=0,
            text_color=("gray20", "gray80")
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        
        # Bind search events
        self.search_entry.bind("<KeyRelease>", self._filter_teams)
        self.search_entry.bind("<Control-a>", lambda e: self.search_entry.select_range(0, "end"))
        
        # Search info label
        self.search_info = ctk.CTkLabel(
            search_container,
            text="",
            font=("Segoe UI", 11),
            text_color=("gray60", "gray50")
        )
        self.search_info.pack(anchor="w", pady=(8, 0))

    def _filter_teams(self, event=None):
        """Advanced search filter with letter-by-letter matching"""
        if self._is_loading:
            return  # Don't filter while loading
            
        query = self.search_entry.get().strip().lower()
        self.search_query = query
        
        # Clear previous visible buttons
        self.visible_buttons.clear()
        
        if not query:
            # Show all teams if no search query
            self.visible_buttons = self.team_buttons.copy()
            self.search_info.configure(text=f"Showing all {len(self.visible_buttons)} teams")
        else:
            # Advanced search: check if all letters in query exist in team name/abbreviation
            filtered_teams = []
            
            for name, abrev in self.all_teams.items():
                name_lower = name.lower()
                abrev_lower = abrev.lower()
                full_text = f"{name_lower} {abrev_lower}"
                
                # Check if all letters in query exist in the team data
                if self._letters_match(query, full_text):
                    filtered_teams.append((name, abrev))
            
            # Update visible buttons based on filtered results
            self.visible_buttons = []
            for name, abrev in filtered_teams:
                # Find the corresponding button
                for btn in self.team_buttons:
                    if btn.cget("text") == f"{name} — {abrev}":
                        self.visible_buttons.append(btn)
                        break
            
            # Update search info
            if self.visible_buttons:
                self.search_info.configure(
                    text=f"Found {len(self.visible_buttons)} team(s) matching '{query}'"
                )
            else:
                self.search_info.configure(
                    text=f"No teams found matching '{query}'"
                )
        
        # Update UI
        self._update_team_display()
        
        # Reset selection
        self.selected_index = -1
        if self.visible_buttons:
            self.selected_index = 0
            self._update_selection()

    def _letters_match(self, query, text):
        """Check if all letters in query exist in text (in order)"""
        query_chars = list(query)
        text_chars = list(text)
        
        # Remove spaces and special characters for matching
        query_chars = [c for c in query_chars if c.isalnum()]
        text_chars = [c for c in text_chars if c.isalnum()]
        
        if not query_chars:
            return True
            
        # Check if all query characters exist in text (allowing for order flexibility)
        for char in query_chars:
            if char in text_chars:
                # Remove the found character to avoid double counting
                text_chars.remove(char)
            else:
                return False
        return True

    def _update_team_display(self):
        """Update the display of teams based on current filter"""
        if self._is_loading:
            return  # Don't update display while loading
            
        # Clear empty state widget if it exists
        if self.empty_state_widget:
            self.empty_state_widget.destroy()
            self.empty_state_widget = None
            
        # Hide all buttons first
        for btn in self.team_buttons:
            btn.pack_forget()
        
        # Show only visible buttons
        for btn in self.visible_buttons:
            btn.pack(fill="x", pady=2, padx=5)
        
        # Show empty state if no results
        if not self.visible_buttons:
            self._show_empty_state()

    def _show_empty_state(self):
        """Show empty state when no teams are found"""
        # Clear any existing empty state
        if self.empty_state_widget:
            self.empty_state_widget.destroy()
        
        empty_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent"
        )
        self.empty_state_widget = empty_frame
        empty_frame.pack(expand=True, pady=50)
        
        # Empty state icon (you can replace with an actual icon)
        empty_label = ctk.CTkLabel(
            empty_frame,
            text="🔍",
            font=("Segoe UI", 48),
            text_color=("gray60", "gray50")
        )
        empty_label.pack()
        
        # Empty state message
        if self.search_query:
            message = f"No teams found matching '{self.search_query}'"
            subtitle = "Try adjusting your search terms"
        else:
            message = "No teams available"
            subtitle = "Add teams to get started"
        
        message_label = ctk.CTkLabel(
            empty_frame,
            text=message,
            font=("Segoe UI", 16, "bold"),
            text_color=("gray50", "gray60")
        )
        message_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            empty_frame,
            text=subtitle,
            font=("Segoe UI", 12),
            text_color=("gray60", "gray50")
        )
        subtitle_label.pack()

    def _build_team_list(self):
        """Build the team list with improved styling"""
        # Create container for team list
        list_container = ctk.CTkFrame(self, fg_color="transparent")
        list_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create scrollable frame with modern styling
        self.scrollable_frame = ctk.CTkScrollableFrame(
            list_container, 
            corner_radius=15,
            fg_color=("gray95", "gray25"),
            border_width=1,
            border_color=("gray80", "gray30")
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bind keyboard events to the scrollable frame
        self.scrollable_frame.bind("<Key>", self._handle_keyboard)
        self.scrollable_frame.bind("<Up>", self._handle_up)
        self.scrollable_frame.bind("<Down>", self._handle_down)
        self.scrollable_frame.bind("<Return>", self._handle_return)
        self.scrollable_frame.bind("<Tab>", self._handle_tab)
        
        # Make the scrollable frame focusable by binding focus events
        self.scrollable_frame.bind("<Button-1>", lambda e: self.scrollable_frame.focus_set())
        
        # Teams will be loaded by _deferred_load_teams after UI is built

    def _load_teams(self):
        """Load teams and create buttons - now handled by _deferred_load_teams"""
        # This method is kept for backward compatibility but now delegates to _deferred_load_teams
        self._deferred_load_teams()

    def _handle_keyboard(self, event):
        """Handle keyboard navigation"""
        # Don't handle navigation if user is typing in search bar
        if self.focus_get() == self.search_entry:
            return
            
        if not self.visible_buttons:
            return
            
        if event.keysym == "Up":
            self._navigate_up()
            return "break"
        elif event.keysym == "Down":
            self._navigate_down()
            return "break"
        elif event.keysym == "Return":
            self._select_current()
            return "break"
        elif event.keysym == "Tab":
            # Allow tab navigation between search and list
            if self.focus_get() == self.search_entry:
                self._focus_first_visible_button()
            else:
                self.search_entry.focus_set()

    def _handle_up(self, event):
        """Handle Up arrow key"""
        if self.focus_get() != self.search_entry and self.visible_buttons:
            self._navigate_up()
            return "break"
        return None

    def _handle_down(self, event):
        """Handle Down arrow key"""
        if self.focus_get() != self.search_entry and self.visible_buttons:
            self._navigate_down()
            return "break"
        return None

    def _handle_return(self, event):
        """Handle Return key"""
        if self.focus_get() != self.search_entry and self.visible_buttons:
            self._select_current()
            return "break"
        return None

    def _handle_tab(self, event):
        """Handle Tab key"""
        if self.focus_get() == self.search_entry:
            self._focus_first_visible_button()
            return "break"
        else:
            self.search_entry.focus_set()
            return "break"

    def _navigate_up(self):
        """Navigate to previous team"""
        if not self.visible_buttons:
            return
            
        if self.selected_index <= 0:
            # Wrap to last item
            self.selected_index = len(self.visible_buttons) - 1
        else:
            self.selected_index -= 1
            
        self._update_selection()

    def _navigate_down(self):
        """Navigate to next team"""
        if not self.visible_buttons:
            return
            
        if self.selected_index >= len(self.visible_buttons) - 1:
            # Wrap to first item
            self.selected_index = 0
        else:
            self.selected_index += 1
            
        self._update_selection()

    def _update_selection(self):
        """Update visual selection of current team"""
        if not self.visible_buttons or self.selected_index < 0:
            return
            
        # Reset all button colors
        for btn in self.visible_buttons:
            btn.configure(
                fg_color=("gray90", "gray30"),
                border_color=("gray80", "gray40")
            )
        
        # Highlight selected button
        if 0 <= self.selected_index < len(self.visible_buttons):
            selected_btn = self.visible_buttons[self.selected_index]
            selected_btn.configure(
                fg_color=("gray80", "gray40"),
                border_color=("blue", "lightblue")
            )

    def _select_current(self):
        """Select the currently highlighted team"""
        if 0 <= self.selected_index < len(self.visible_buttons):
            selected_btn = self.visible_buttons[self.selected_index]
            # Extract team info from button text
            text = selected_btn.cget("text")
            if " — " in text:
                name, abrev = text.split(" — ", 1)
                self._open_edit_popup(name, abrev)

    def _focus_first_visible_button(self):
        """Focus the first visible button for keyboard navigation"""
        if self.visible_buttons:
            self.scrollable_frame.focus_set()
            self.selected_index = 0
            self._update_selection()

    def _open_edit_popup(self, name, abrev):
        """Open the edit popup for a team"""
        EditTeamPopup(
            parent=self,
            mongo=self.mongo,
            original_name=name,
            original_abrev=abrev,
            on_done=self._on_change
        )

    def _on_change(self):
        """Handle changes from edit popup"""
        self._load_teams()
        # Re-apply current search filter
        if self.search_query:
            self._filter_teams()

    def _show_loading_state(self):
        """Show a loading state while teams are being loaded"""
        loading_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent"
        )
        loading_frame.pack(expand=True, pady=50)
        
        # Loading spinner with smooth animation
        loading_label = ctk.CTkLabel(
            loading_frame,
            text="⏳",
            font=("Segoe UI", 48),
            text_color=("gray60", "gray50")
        )
        loading_label.pack()
        
        # Loading message
        message_label = ctk.CTkLabel(
            loading_frame,
            text="Loading teams...",
            font=("Segoe UI", 16, "bold"),
            text_color=("gray50", "gray60")
        )
        message_label.pack(pady=(10, 5))
        
        # Subtitle for better UX
        subtitle_label = ctk.CTkLabel(
            loading_frame,
            text="Please wait while we prepare your team database",
            font=("Segoe UI", 12),
            text_color=("gray60", "gray50")
        )
        subtitle_label.pack()
        
        self.loading_widget = loading_frame

    def _deferred_load_teams(self):
        """Load teams after a brief delay to allow smooth UI rendering"""
        try:
            # Load teams from database
            self.all_teams = self.mongo.load_teams()
            
            # Remove loading state after a short delay
            self.after(25, lambda: self._remove_loading_state())  # Faster (was 50ms, now 25ms)
            
            # Create team buttons in batch
            self._create_team_buttons()
            
            # Update UI state
            self._is_loading = False
            
            # Update search info
            search_text = f"Showing all {len(self.visible_buttons)} teams"
            self.search_info.configure(text=search_text)
            
        except Exception as e:
            # Handle any loading errors gracefully
            if hasattr(self, 'loading_widget') and self.loading_widget:
                self.loading_widget.destroy()
                self.loading_widget = None
            self._show_error_state(f"Error loading teams: {str(e)}")

    def _remove_loading_state(self):
        """Remove loading state with smooth transition"""
        if hasattr(self, 'loading_widget') and self.loading_widget:
            self.loading_widget.destroy()
            self.loading_widget = None

    def _create_team_buttons(self):
        """Create team buttons efficiently"""
        # Clear existing buttons
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.team_buttons = []
        self.visible_buttons = []
        self.selected_index = -1
        
        if not self.all_teams:
            # Show empty state
            self._show_empty_state()
            return
        
        # Create all buttons first (without packing)
        button_frames = []
        for name, abrev in self.all_teams.items():
            # Create team button with improved styling
            btn = ctk.CTkButton(
                self.scrollable_frame,
                text=f"{name} — {abrev}",
                anchor="w",
                font=("Segoe UI", 13),
                height=45,
                corner_radius=10,
                fg_color=("gray90", "gray30"),
                hover_color=("gray85", "gray35"),
                border_width=1,
                border_color=("gray80", "gray40"),
                command=lambda n=name, a=abrev: self._open_edit_popup(n, a)
            )
            self.team_buttons.append(btn)
            self.visible_buttons.append(btn)
            button_frames.append(btn)
        
        # Pack all buttons at once to prevent progressive rendering
        for btn in button_frames:
            btn.pack(fill="x", pady=2, padx=5)
        
        # Set initial selection
        if self.visible_buttons:
            self.selected_index = 0
            self._update_selection()

    def _show_error_state(self, error_message):
        """Show error state when loading fails"""
        error_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent"
        )
        error_frame.pack(expand=True, pady=50)
        
        # Error icon
        error_label = ctk.CTkLabel(
            error_frame,
            text="❌",
            font=("Segoe UI", 48),
            text_color=COLOR_STOP
        )
        error_label.pack()
        
        # Error message
        message_label = ctk.CTkLabel(
            error_frame,
            text="Failed to load teams",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_STOP
        )
        message_label.pack(pady=(10, 5))
        
        # Error details
        details_label = ctk.CTkLabel(
            error_frame,
            text=error_message,
            font=("Segoe UI", 12),
            text_color=("gray60", "gray50")
        )
        details_label.pack()
        
        # Retry button
        retry_btn = ctk.CTkButton(
            error_frame,
            text="Retry",
            command=self._deferred_load_teams,
            fg_color=COLOR_WARNING,
            hover_color=("orange", "darkorange")
        )
        retry_btn.pack(pady=(20, 0))
        
        self.error_widget = error_frame


class EditTeamPopup(ctk.CTkToplevel):
    def __init__(self, parent, mongo, original_name, original_abrev, on_done):
        super().__init__(parent)
        self.mongo = mongo
        self.orig_name = original_name.strip().upper()
        self.orig_abrev = original_abrev.strip().upper()
        self.on_done = on_done

        self.title("Edit Team")
        self.geometry("400x320")
        self.iconbitmap(get_icon_path("icon_soft")) 
        self.grab_set()
        self.attributes("-topmost", True)
        
        # Center the popup
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (320 // 2)
        self.geometry(f"400x320+{x}+{y}")

        self._build_form()

    def _build_form(self):
        """Build the edit form with improved styling"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Edit Team Information",
            font=("Segoe UI", 18, "bold"),
            text_color=("gray20", "gray80")
        )
        title_label.pack()
        
        # Form container
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Team Name field
        name_label = ctk.CTkLabel(
            form_frame,
            text="Team Name",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray30", "gray70")
        )
        name_label.pack(anchor="w", pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(
            form_frame,
            font=("Segoe UI", 14),
            height=40,
            corner_radius=8,
            fg_color=("gray95", "gray25"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("gray20", "gray80")
        )
        self.name_entry.insert(0, self.orig_name)
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        # Abbreviation field
        abrev_label = ctk.CTkLabel(
            form_frame,
            text="Abbreviation",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray30", "gray70")
        )
        abrev_label.pack(anchor="w", pady=(0, 5))
        
        self.abrev_entry = ctk.CTkEntry(
            form_frame,
            font=("Segoe UI", 14),
            height=40,
            corner_radius=8,
            fg_color=("gray95", "gray25"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("gray20", "gray80")
        )
        self.abrev_entry.insert(0, self.orig_abrev)
        self.abrev_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons container
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Save button
        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Changes",
            font=("Segoe UI", 12, "bold"),
            height=40,
            corner_radius=8,
            fg_color=COLOR_SUCCESS,
            hover_color=("green", "darkgreen"),
            command=self._save
        )
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Delete button
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Delete Team",
            font=("Segoe UI", 12, "bold"),
            height=40,
            corner_radius=8,
            fg_color=COLOR_STOP,
            hover_color=("red", "darkred"),
            command=self._delete
        )
        delete_btn.pack(side="left", fill="x", expand=True, padx=(5, 5))
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=("Segoe UI", 12, "bold"),
            height=40,
            corner_radius=8,
            fg_color=("gray70", "gray50"),
            hover_color=("gray60", "gray40"),
            command=self.destroy
        )
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Set focus to name entry
        self.name_entry.focus_set()
        self.name_entry.select_range(0, "end")

    def _save(self):
        """Save team changes"""
        new_name = self.name_entry.get().strip().upper()
        new_abrev = self.abrev_entry.get().strip().upper()
        
        if not (new_name and new_abrev):
            show_message_notification(
                "⚠️ Validation Error",
                "Both team name and abbreviation are required.",
                icon="⚠️",
                bg_color=COLOR_WARNING
            )
            return

        # Save new team
        self.mongo.save_team(new_name, new_abrev)

        # Delete old team if renamed
        if new_name != self.orig_name:
            self.mongo.delete_team(self.orig_name)

        show_message_notification(
            "✅ Team Updated",
            f"Team '{new_name}' has been successfully updated.",
            icon="✅",
            bg_color=COLOR_SUCCESS
        )

        self.destroy()
        self.on_done()

    def _delete(self):
        """Delete team with confirmation"""
        # Create confirmation dialog
        dlg = ctk.CTkToplevel(self)
        dlg.title("Confirm Deletion")
        dlg.geometry("400x200")
        dlg.grab_set()
        dlg.attributes("-topmost", True)
        
        # Center the dialog
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - (400 // 2)
        y = (dlg.winfo_screenheight() // 2) - (200 // 2)
        dlg.geometry(f"400x200+{x}+{y}")

        # Warning icon and message
        warning_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        warning_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        warning_label = ctk.CTkLabel(
            warning_frame,
            text="⚠️",
            font=("Segoe UI", 48),
            text_color=COLOR_WARNING
        )
        warning_label.pack()
        
        message_label = ctk.CTkLabel(
            warning_frame,
            text=f"Are you sure you want to delete '{self.orig_name}'?",
            font=("Segoe UI", 14, "bold"),
            text_color=("gray20", "gray80"),
            wraplength=300
        )
        message_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            warning_frame,
            text="This action cannot be undone.",
            font=("Segoe UI", 12),
            text_color=("gray50", "gray60")
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Confirmation input
        confirm_label = ctk.CTkLabel(
            warning_frame,
            text="Type 'DELETE' to confirm:",
            font=("Segoe UI", 11),
            text_color=("gray40", "gray70")
        )
        confirm_label.pack(pady=(0, 5))
        
        confirm_entry = ctk.CTkEntry(
            warning_frame,
            placeholder_text="DELETE",
            font=("Segoe UI", 12),
            height=35,
            corner_radius=6
        )
        confirm_entry.pack(fill="x", pady=(0, 20))
        confirm_entry.focus_set()

        result = {"confirmed": False}
        
        def on_submit(event=None):
            if confirm_entry.get().strip().upper() == "DELETE":
                result["confirmed"] = True
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        # Bind Enter key
        confirm_entry.bind("<Return>", on_submit)
        
        # Buttons
        btn_frame = ctk.CTkFrame(warning_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=("Segoe UI", 11),
            height=35,
            corner_radius=6,
            fg_color=("gray70", "gray50"),
            hover_color=("gray60", "gray40"),
            command=on_cancel
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            btn_frame,
            text="Delete Team",
            font=("Segoe UI", 11, "bold"),
            height=35,
            corner_radius=6,
            fg_color=COLOR_STOP,
            hover_color=("red", "darkred"),
            command=on_submit
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

        dlg.wait_window()

        if not result["confirmed"]:
            return

        # Delete the team
        self.mongo.delete_team(self.orig_name)
        show_message_notification(
            "❌ Team Deleted",
            f"Team '{self.orig_name}' has been permanently removed.",
            icon="❌",
            bg_color=COLOR_STOP
        )
        
        self.destroy()
        self.on_done()
