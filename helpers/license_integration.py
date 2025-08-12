"""
License Integration Helper
Simple integration functions to add licensing to any application window.
"""

from typing import Optional
from helpers.license_manager import LicenseManager
from helpers.license_blocker import LicenseBlocker
from helpers.footer_label import add_footer_label

def integrate_licensing(parent_widget, show_footer: bool = True) -> Optional[LicenseBlocker]:
    """
    Integrate licensing system into a parent widget.
    
    Args:
        parent_widget: The parent widget to integrate with
        show_footer: Whether to show the footer with license status
        
    Returns:
        LicenseBlocker instance if successful, None if failed
    """
    try:
        # Create license blocker
        blocker = LicenseBlocker(parent_widget)
        
        # Check license and block if needed
        if not blocker.check_and_block():
            # Application is blocked, return blocker for further control
            return blocker
        
        # Add footer with license status if requested
        if show_footer:
            add_footer_label(parent_widget)
        
        return blocker
        
    except Exception as e:
        print(f"Failed to integrate licensing: {e}")
        return None

def check_license_status() -> tuple[str, bool]:
    """
    Check the current license status.
    
    Returns:
        Tuple of (status, is_valid)
    """
    try:
        manager = LicenseManager()
        return manager.get_license_status()
    except Exception as e:
        print(f"Failed to check license status: {e}")
        return "not_found", False

def get_license_display_info() -> tuple[str, str]:
    """
    Get license display information.
    
    Returns:
        Tuple of (display_text, status_color)
    """
    try:
        manager = LicenseManager()
        status, _ = manager.get_license_status()
        display_text = manager.get_status_display_text(status)
        status_color = manager.get_status_color(status)
        return display_text, status_color
    except Exception as e:
        print(f"Failed to get license display info: {e}")
        return "LICENSE ERROR", "#dc3545"

def is_license_valid() -> bool:
    """
    Check if the current license is valid.
    
    Returns:
        True if license is valid, False otherwise
    """
    try:
        _, is_valid = check_license_status()
        return is_valid
    except Exception as e:
        print(f"Failed to check license validity: {e}")
        return False

def force_license_check(parent_widget) -> bool:
    """
    Force a license check and show blocking if needed.
    
    Args:
        parent_widget: The parent widget to block if needed
        
    Returns:
        True if license is valid, False if blocked
    """
    try:
        blocker = LicenseBlocker(parent_widget)
        return blocker.check_and_block()
    except Exception as e:
        print(f"Failed to force license check: {e}")
        return False
