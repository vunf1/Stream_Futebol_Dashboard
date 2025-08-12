"""
Licensing system for the Stream Futebol Dashboard application.

This module contains the complete licensing infrastructure including
license management, validation, modal dialogs, and application blocking.
"""

from .license_manager import LicenseManager
from .license_validator import LicenseValidator
from .license_modal import LicenseModal, LicenseActivationDialog
from .license_blocker import LicenseBlocker
from .license_integration import (
    integrate_licensing,
    check_license_status,
    get_license_display_info,
    is_license_valid,
    force_license_check
)

__all__ = [
    'LicenseManager',
    'LicenseValidator',
    'LicenseModal',
    'LicenseActivationDialog',
    'LicenseBlocker',
    'integrate_licensing',
    'check_license_status',
    'get_license_display_info',
    'is_license_valid',
    'force_license_check',
]
