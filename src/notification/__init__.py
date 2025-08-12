"""
Notification system for the Stream Futebol Dashboard application.

This module provides toast notifications and notification server functionality
for displaying user messages and system alerts.
"""

from .notification_server import server_main
from .toast import init_notification_queue, show_message_notification, prompt_notification

__all__ = [
    'server_main',
    'init_notification_queue',
    'show_message_notification',
    'prompt_notification',
]
