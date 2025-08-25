"""
Footer label utility for creating consistent footer labels across UI components.
Provides a reusable footer with copyright text, datetime, license status, and close button.
"""

import customtkinter as ctk
import tkinter as tk
from src.utils import get_current_portugal_time
import threading
import webbrowser
from urllib import request as _urlrequest
from urllib import error as _urlerror
from src.core.server_launcher import get_server_launcher
import subprocess as _subprocess
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass


@dataclass
class FooterConfig:
    """Configuration for footer customization."""
    show_copyright: bool = True
    show_datetime: bool = True
    show_license_status: bool = True
    show_activate_button: bool = True
    show_close_button: bool = True  # Note: Close button is always visible regardless of this setting
    copyright_text: str = "© 2025 Vunf1"
    datetime_format: str = "default"  # "default", "short", "custom"
    custom_datetime: str = ""
    license_clickable: bool = True
    close_command: Optional[Callable] = None
    custom_padding: tuple = (6, 2, 6, 2)  # (left, top, right, bottom)
    custom_spacing: int = 10
    footer_height: int = 25  # Reduced default height for better proportions
    close_button_size: int = 24
    activate_button_height: int = 20
    # Server status dot
    show_server_status_dot: bool = False  # Disabled by default
    server_status_url: str = "http://localhost:5000/"
    server_status_poll_ms: int = 2500


def create_footer(parent, **kwargs):
    """
    Create and configure a footer label with all available options.
    
    This is the single function that handles all footer configuration.
    
    Args:
        parent: The parent widget to add the footer to
        **kwargs: All footer configuration options (see FooterConfig for available options)
    
    Returns:
        The footer frame widget for further customization if needed
    
    Examples:
        # Simple footer with just copyright
        create_footer(parent, show_datetime=False, show_license_status=False, show_activate_button=False)
        
        # Full footer with custom copyright
        create_footer(parent, copyright_text="© 2025 My Company")
        
        # License-only footer
        create_footer(parent, show_copyright=False, show_datetime=False)
        
        # Custom footer with specific settings
        create_footer(parent, 
                     copyright_text="© 2025 Custom",
                     datetime_format="short",
                     custom_spacing=30,
                     footer_height=30)
    
    Note:
        The close button (X) is always visible regardless of configuration
        for user convenience and consistent UI behavior.
    """
    # Create config with defaults and override with kwargs
    config = FooterConfig()
    
    # Override config with kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    # Create footer frame to hold all elements - ensure it fills full width
    footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
    
    # Pack with proper fill and expansion to ensure full width coverage
    # Respect top and bottom from custom_padding (index 1 and 3)
    footer_frame.pack(
        side="bottom",
        pady=(config.custom_padding[1], config.custom_padding[3]),
        fill="x",
        expand=False,
        padx=0,
    )
    
    # Set minimum height but allow expansion
    footer_frame.configure(height=config.footer_height)
    footer_frame.pack_propagate(True)  # Allow height to adjust to content
    
    # Force footer to update its layout and ensure proper width
    def force_footer_layout():
        """Force footer to update its layout and ensure proper width."""
        if parent.winfo_exists() and footer_frame.winfo_exists():
            try:
                # Force layout update
                footer_frame.update_idletasks()
                parent.update_idletasks()
                
                # Ensure footer takes full available width
                footer_frame.pack_configure(fill="x", expand=False)
                
            except Exception as e:
                pass  # Silently ignore layout errors
    
    # Bind to parent resize events
    parent.bind("<Configure>", lambda e: force_footer_layout())
    
    # Initial layout setup after a short delay to ensure parent has dimensions
    parent.after(50, force_footer_layout)
    
    # Create a centered row layout for all footer components
    # Main row container that centers all elements
    row_container = ctk.CTkFrame(footer_frame, fg_color="transparent")
    row_container.pack(expand=True, fill="both", pady=2)
    
    # Left side container for copyright and datetime
    left_container = ctk.CTkFrame(row_container, fg_color="transparent")
    left_container.pack(side="left", fill="y", padx=(4, 0))
    
    # Optional server status dot (before copyright)
    server_status_label = None
    _server_is_up = {"value": False}

    if getattr(config, "show_server_status_dot", False):
        server_status_label = ctk.CTkLabel(
            left_container,
            text="●",
            font=("Segoe UI", 12, "bold"),
            text_color="#dc3545",  # default red
            cursor="hand2",
        )
        server_status_label.pack(side="left", padx=(0, 3))

        def _apply_status_color(is_up: bool):
            try:
                if not server_status_label or not server_status_label.winfo_exists():
                    return
                server_status_label.configure(text_color=("#4CAF50" if is_up else "#dc3545"))
            except Exception:
                pass

        # Track detailed state for tooltip content
        _server_state = {"http_ok": False, "proc_ok": False, "restarting": False}

        def _check_status_background():
            try:
                # Perform HTTP HEAD/GET in background thread
                req = _urlrequest.Request(config.server_status_url, method="GET")
                with _urlrequest.urlopen(req, timeout=1.5) as resp:
                    code = getattr(resp, "status", None) or resp.getcode()
                    http_ok = (code == 200)
            except (_urlerror.URLError, _urlerror.HTTPError, Exception):
                http_ok = False

            # Check server process state as well
            proc_ok = True
            try:
                launcher = get_server_launcher()
                # Primary check
                proc_ok = bool(launcher.is_server_running())
                # Fallback in non-frozen/dev environments to real system-wide check
                if not proc_ok:
                    try:
                        proc_ok = bool(launcher._any_server_running())  # type: ignore[attr-defined]
                    except Exception:
                        pass
            except Exception:
                proc_ok = False

            # Persist for tooltip
            _server_state["http_ok"] = bool(http_ok)
            _server_state["proc_ok"] = bool(proc_ok)
            is_up = (http_ok and proc_ok)
            _server_is_up["value"] = is_up
            try:
                if parent and parent.winfo_exists():
                    parent.after(0, lambda: _apply_status_color(is_up))
            except Exception:
                pass

        def _schedule_status_check():
            # Stop scheduling if widget destroyed
            if not server_status_label or not server_status_label.winfo_exists():
                return
            t = threading.Thread(target=_check_status_background, daemon=True)
            t.start()
            try:
                parent.after(max(500, int(config.server_status_poll_ms)), _schedule_status_check)
            except Exception:
                pass

        def _on_server_dot_click(_event=None):
            is_up = bool(_server_is_up["value"])  # snapshot (http AND proc)

            # Helper: ensure server is started, with dev-mode fallback
            def _ensure_started_or_restart():
                try:
                    launcher = get_server_launcher()

                    # Re-check running state quickly
                    try:
                        running = bool(launcher.is_server_running())
                        if not running:
                            try:
                                running = bool(launcher._any_server_running())  # type: ignore[attr-defined]
                            except Exception:
                                pass
                    except Exception:
                        running = False

                    if running and not is_up:
                        # Process is up but HTTP not OK -> restart
                        try:
                            _server_state["restarting"] = True
                            try:
                                if parent and parent.winfo_exists():
                                    parent.after(0, _update_tooltip)
                            except Exception:
                                pass
                            launcher.restart_server()
                        except Exception:
                            pass
                        finally:
                            _server_state["restarting"] = False
                            try:
                                if parent and parent.winfo_exists():
                                    parent.after(0, _update_tooltip)
                            except Exception:
                                pass
                    elif not running:
                        # Try regular start (works in bundled mode)
                        try:
                            launcher.start_server()
                        except Exception:
                            pass

                        # After a brief wait, if still not running, try direct spawn (dev fallback)
                        try:
                            import time as _t
                            _t.sleep(0.2)
                            running2 = False
                            try:
                                running2 = bool(launcher._any_server_running())  # type: ignore[attr-defined]
                            except Exception:
                                running2 = False
                            if not running2:
                                exe_path = launcher.get_server_path()
                                if exe_path and exe_path.exists():
                                    _subprocess.Popen(
                                        [str(exe_path)],
                                        cwd=str(exe_path.parent),
                                        stdin=_subprocess.DEVNULL,
                                        stdout=_subprocess.DEVNULL,
                                        stderr=_subprocess.DEVNULL,
                                        creationflags=getattr(_subprocess, 'CREATE_NO_WINDOW', 0),
                                    )
                        except Exception:
                            pass
                except Exception:
                    pass

            if is_up:
                try:
                    webbrowser.open(config.server_status_url)
                except Exception:
                    pass
            else:
                threading.Thread(target=_ensure_started_or_restart, daemon=True).start()

        server_status_label.bind("<Button-1>", _on_server_dot_click)

        # ---------------- Tooltip ----------------
        _tooltip_window: Dict[str, Any] = {"win": None}
        _tooltip_job: Dict[str, Any] = {"id": None}
        _tooltip_label_ref: Dict[str, Any] = {"lbl": None}

        def _get_tooltip_text() -> str:
            if bool(_server_state.get("restarting")):
                return "Restarting"
            http_ok = bool(_server_state.get("http_ok"))
            proc_ok = bool(_server_state.get("proc_ok"))
            is_up = http_ok and proc_ok
            if is_up:
                return "Online — click to open"
            if proc_ok and not http_ok:
                return "Restarting"
            if (not proc_ok) and http_ok:
                return "Restarting"
            return "Offline — click to start"

        def _position_tooltip(win):
            try:
                if not (server_status_label and server_status_label.winfo_exists() and win and win.winfo_exists()):
                    return
                # Compute geometry above the dot
                win.update_idletasks()
                dot_x = server_status_label.winfo_rootx()
                dot_y = server_status_label.winfo_rooty()
                dot_w = server_status_label.winfo_width()
                win_w = win.winfo_width()
                win_h = win.winfo_height()
                x = int(dot_x + (dot_w // 2) - (win_w // 2))
                y = int(dot_y - win_h - 8)
                # Clamp to screen
                scr_w = server_status_label.winfo_screenwidth()
                scr_h = server_status_label.winfo_screenheight()
                x = max(4, min(x, scr_w - win_w - 4))
                y = max(4, min(y, scr_h - win_h - 4))
                win.geometry(f"{win_w}x{win_h}+{x}+{y}")
                try:
                    win.attributes("-topmost", True)
                except Exception:
                    pass
            except Exception:
                pass

        def _update_tooltip():
            win = _tooltip_window.get("win")
            if not (win and win.winfo_exists()):
                _tooltip_job["id"] = None
                return
            try:
                # Update text and reposition
                lbl = _tooltip_label_ref.get("lbl")
                if lbl and lbl.winfo_exists():
                    lbl.configure(text=_get_tooltip_text())
                _position_tooltip(win)
            except Exception:
                pass
            # Reschedule
            try:
                _tooltip_job["id"] = parent.after(300, _update_tooltip)
            except Exception:
                _tooltip_job["id"] = None

        def _show_tooltip(_e=None):
            try:
                win = _tooltip_window.get("win")
                if win and win.winfo_exists():
                    # Already visible; just refresh
                    _update_tooltip()
                    return
                win = tk.Toplevel(parent)
                win.overrideredirect(True)
                try:
                    win.attributes("-topmost", True)
                except Exception:
                    pass
                # Build content
                win.configure(bg="#2b2b2b", bd=0, highlightthickness=0)
                lbl = tk.Label(
                    win,
                    text=_get_tooltip_text(),
                    font=("Segoe UI", 8),
                    fg="#ffffff",
                    bg="#2b2b2b",
                    padx=2,
                    pady=0,
                    bd=0,
                    highlightthickness=0,
                )
                lbl.pack(padx=0, pady=0)
                _tooltip_label_ref["lbl"] = lbl
                # Initial size and position
                win.update_idletasks()
                _position_tooltip(win)
                _tooltip_window["win"] = win
                # Start periodic refresh
                _update_tooltip()
            except Exception:
                pass

        def _hide_tooltip(_e=None):
            try:
                jid = _tooltip_job.get("id")
                if jid is not None:
                    try:
                        parent.after_cancel(jid)
                    except Exception:
                        pass
                    _tooltip_job["id"] = None
                win = _tooltip_window.get("win")
                if win and win.winfo_exists():
                    win.destroy()
                _tooltip_window["win"] = None
            except Exception:
                pass

        # Keep tooltip anchored and contextual
        server_status_label.bind("<Enter>", _show_tooltip)
        server_status_label.bind("<Leave>", _hide_tooltip)
        # Also refresh tooltip when status color updates
        _orig_apply_status_color = _apply_status_color
        def _apply_status_color_wrapper(is_up: bool):
            _orig_apply_status_color(is_up)
            win = _tooltip_window.get("win")
            if win and win.winfo_exists():
                _update_tooltip()
        _apply_status_color = _apply_status_color_wrapper  # type: ignore

        # Kick off initial check shortly after layout stabilizes
        try:
            parent.after(200, _schedule_status_check)
        except Exception:
            pass

    # Copyright label
    if config.show_copyright:
        copyright_label = ctk.CTkLabel(
            left_container, 
            text=config.copyright_text, 
            font=("Segoe UI Emoji", 10), 
            text_color="gray"
        )
        copyright_label.pack(side="left", padx=(0, 4))
    
    # Datetime label
    if config.show_datetime:
        datetime_label = ctk.CTkLabel(
            left_container, 
            text="", 
            font=("Segoe UI", 10), 
            text_color="gray"
        )
        datetime_label.pack(side="left", padx=(0, 4))
        
        def update_datetime():
            """Update datetime display based on config."""
            try:
                # Check if widget still exists before performing operations
                if not datetime_label.winfo_exists():
                    return  # Stop the timer if widget was destroyed
                    
                if config.datetime_format == "custom" and config.custom_datetime:
                    datetime_label.configure(text=config.custom_datetime)
                elif config.datetime_format == "short":
                    now = get_current_portugal_time()
                    datetime_label.configure(text=now.strftime("%Y-%m-%d"))  # Date only (Lisbon time)
                else:  # default
                    now = get_current_portugal_time()
                    datetime_label.configure(text=now.strftime("%Y-%m-%d %H:%M:%S"))  # Lisbon time
                
                # Only schedule next update if widget still exists and datetime should be shown
                if config.show_datetime and datetime_label.winfo_exists():
                    parent.after(1000, update_datetime)
            except Exception as e:
                # Widget was destroyed or error occurred, stop the timer
                try:
                    from src.core.logger import get_logger
                    get_logger(__name__).debug("footer_datetime_update_error", exc_info=True)
                except Exception:
                    pass
                return
        
        update_datetime()
    
    # Center container for license status and activate button
    if config.show_license_status:
        center_container = ctk.CTkFrame(row_container, fg_color="transparent")
        center_container.pack(side="left", expand=True, fill="x", padx=(config.custom_spacing, 0))
        
        # Create a horizontal container for license status and activate button
        license_row = ctk.CTkFrame(center_container, fg_color="transparent")
        license_row.pack(expand=True, fill="x")
        
        license_status_label = ctk.CTkLabel(
            license_row, 
            text="", 
            font=("Segoe UI", 10, "bold"),
            text_color="gray",
            cursor="arrow"
        )
        license_status_label.pack(side="left", expand=True, fill="x")  # Position on the left
        
        # License manager initialization
        from src.licensing import LicenseManager
        from src.licensing import LicenseActivationDialog
        from src.licensing import show_license_details
        
        license_manager = LicenseManager()
        
        # Create activate button early so it can be referenced
        activate_button = None
        if config.show_activate_button:
            def show_license_activation():
                try:
                    from src.core.logger import get_logger
                    get_logger(__name__).info("license_activation_modal_open")
                    
                    def on_license_activated(license_data):
                        if license_manager.save_license(license_data):
                            update_license_status()
                            try:
                                from src.core.logger import get_logger
                                get_logger(__name__).info("license_activated_success")
                            except Exception:
                                pass
                        else:
                            try:
                                from src.core.logger import get_logger
                                get_logger(__name__).warning("license_save_failed")
                            except Exception:
                                pass
                    
                    result = LicenseActivationDialog.show(parent, on_license_activated)
                    try:
                        from src.core.logger import get_logger
                        get_logger(__name__).info("license_modal_result", extra={"result": str(result)})
                    except Exception:
                        pass
                    
                except Exception as e:
                    try:
                        from src.core.logger import get_logger
                        get_logger(__name__).error("license_activation_modal_error", exc_info=True)
                    except Exception:
                        pass
            
            activate_button = ctk.CTkButton(
                license_row,  # Use license_row instead of center_container
                text="🔑 Activate",
                command=show_license_activation,
                font=("Segoe UI", 9),
                height=config.activate_button_height,
                width=config.activate_button_height,  # Make it square by using height as width
                fg_color="transparent",
                hover_color="#2b2b2b",
                text_color="#888888"
            )
            # Don't pack the button yet - it will be shown/hidden by update_license_status
        
        def update_license_status():
            """Update the license status display."""
            try:
                # Check if widget still exists before performing operations
                if not license_status_label.winfo_exists():
                    return  # Stop if widget was destroyed
                    
                status, is_valid = license_manager.get_license_status()
                
                # Get display text and color
                display_text = license_manager.get_status_display_text(status)
                status_color = license_manager.get_status_color(status)
                
                # Check if label is in pressed state (green color)
                current_color = license_status_label.cget("text_color")
                is_pressed = current_color == "#4CAF50"
                
                # Update the license status label
                if is_pressed and display_text not in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    final_color = "#4CAF50"  # Keep pressed state only for valid licenses
                else:
                    final_color = status_color  # Use status color for invalid/no license
                    if display_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                        is_pressed = False
                
                license_status_label.configure(text=display_text, text_color=final_color)
                
                # Update cursor based on license status and config
                if config.license_clickable and display_text not in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    license_status_label.configure(cursor="hand2")
                else:
                    license_status_label.configure(cursor="arrow")
                
                # Show/hide activate button based on license status and config
                if config.show_activate_button and activate_button:
                    # Show activate button when license is invalid OR when status indicates need for activation
                    should_show_button = (
                        not is_valid or 
                        display_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED", "EXPIRED", "TRIAL EXPIRED"]
                    )
                    
                    if should_show_button:
                        activate_button.pack(side="right", padx=(4, 0))  # Position on the right of the license row
                    else:
                        activate_button.pack_forget()
                
            except Exception as e:
                # Widget was destroyed or error occurred
                if license_status_label.winfo_exists():
                    try:
                        from src.core.logger import get_logger
                        get_logger(__name__).error("license_status_update_error", exc_info=True)
                    except Exception:
                        pass
                    final_color = "#dc3545"
                    license_status_label.configure(text="LICENSE ERROR", text_color=final_color)
                    license_status_label.configure(cursor="arrow")
                    
                    # Show activate button when there's a license error
                    if config.show_activate_button and activate_button:
                        activate_button.pack(side="right", padx=(8, 0))
                else:
                    # Widget was destroyed, just return
                    return
        
        # Initial license status check
        update_license_status()

        # ----- Server metrics indicator (optional) -----
        try:
            import json as _json
            from pathlib import Path as _Path
            from src.config.settings import AppConfig as _AppConfig
            from src.core.path_finder import get_path_finder as _get_pf
            _pf = _get_pf()
            _metrics_path = _pf.user_local_appdir(_AppConfig.LOCAL_APP_DIRNAME, "server") / getattr(_AppConfig, 'SERVER_METRICS_FILENAME', 'server_metrics.json')
            _metrics_label = ctk.CTkLabel(license_row, text="", font=("Segoe UI", 10), text_color="#888888")
            _metrics_label.pack(side="right")

            def _refresh_metrics():
                try:
                    if _metrics_path.exists():
                        data = _json.loads(_metrics_path.read_text(encoding="utf-8"))
                        status = str(data.get("status", "")).upper()
                        _metrics_label.configure(text=f"Server: {status}")
                    else:
                        _metrics_label.configure(text="")
                except Exception:
                    _metrics_label.configure(text="")
                finally:
                    try:
                        parent.after(2000, _refresh_metrics)
                    except Exception:
                        pass

            parent.after(1000, _refresh_metrics)
        except Exception:
            pass
        
        # Hover effects for clickable license status
        if config.license_clickable:
            def on_enter(e):
                current_text = license_status_label.cget("text")
                if current_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    return
                
                current_color = license_status_label.cget("text_color")
                if current_color != "#4CAF50":
                    license_status_label.configure(text_color="#ffffff")
            
            def on_leave(e):
                current_text = license_status_label.cget("text")
                if current_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    return
                
                current_color = license_status_label.cget("text_color")
                if current_color != "#4CAF50":
                    license_status_label.configure(text_color="gray")
            
            license_status_label.bind("<Enter>", on_enter)
            license_status_label.bind("<Leave>", on_leave)
            
            # Make license status label clickable
            def show_license_details_window():
                current_text = license_status_label.cget("text")
                if current_text in ["NO LICENSE", "LICENSE ERROR", "BLOCKED"]:
                    return
                
                license_status_label.configure(text_color="#4CAF50")
                show_license_details(parent)
            
            license_status_label.bind("<Button-1>", lambda e: show_license_details_window())
        
        # Activate button
        if config.show_activate_button:
            # The activate_button is now managed by update_license_status
            pass
    
    # Right side container for close button
    right_container = ctk.CTkFrame(row_container, fg_color="transparent")
    right_container.pack(side="right", fill="y", padx=(0, 4))
    
    # Close button - ALWAYS visible for user convenience
    def close_action():
        """Handle close button action."""
        if config.close_command:
            config.close_command()
        else:
            # Default close behavior - find and close root window
            current = parent
            while hasattr(current, 'winfo_toplevel'):
                current = current.winfo_toplevel()
                if hasattr(current, 'destroy'):
                    current.destroy()
                    break
    
    close_button = ctk.CTkButton(
        right_container, 
        text="✕", 
        width=config.close_button_size, 
        height=config.close_button_size,
        font=("Segoe UI Emoji", 12, "bold"),
        fg_color="transparent",
        hover_color="#2b2b2b",
        text_color="#888888",
        corner_radius=config.close_button_size // 2,
        command=close_action
    )
    close_button.pack(side="right", padx=(2, 0))
    
    return footer_frame


# Legacy function for backward compatibility
def add_footer_label(parent, config: Optional[FooterConfig] = None, **kwargs):
    """
    Legacy function for backward compatibility.
    This function is deprecated - use create_footer() instead.
    """
    return create_footer(parent, **kwargs)


# Legacy function for backward compatibility
def add_footer_label_legacy(parent, text: str = "© 2025 Vunf1"):
    """
    Legacy function for backward compatibility.
    This function is deprecated - use create_footer() instead.
    """
    return create_footer(parent, copyright_text=text)
