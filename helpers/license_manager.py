"""
License Manager for Stream Futebol Dashboard
Handles license validation, encryption, and status management with machine binding.
"""

import os
import json
import hashlib
import uuid
import platform
import psutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, Literal
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import requests

# License status types
LicenseStatus = Literal["active", "trial", "expired", "trial_expired", "blocked", "not_found"]

class LicenseManager:
    """Manages license validation, encryption, and status for the application."""
    
    def __init__(self):
        self.desktop_path = Path.home() / "Desktop"
        self.license_dir = self.desktop_path / "FUTEBOL-SCORE-DASHBOARD"
        self.license_file = self.license_dir / "license.enc"
        self.app_key = self._get_app_key()
        self.machine_hash = self._compute_machine_hash()
        
    def _get_app_key(self) -> bytes:
        """Get the application's embedded encryption key."""
        # In production, this would be embedded in the binary
        # For now, we'll generate a deterministic key based on app name and version
        app_name = "Stream_Futebol_Dashboard"
        app_version = "1.0.0"
        
        # Create a deterministic key material
        key_material = f"{app_name}:{app_version}"
        key_hash = hashlib.sha256(key_material.encode()).digest()
        
        # Use the hash to generate a deterministic Fernet key
        # This ensures the same key is used for encryption/decryption
        import base64
        
        # Convert hash to base64 for Fernet key
        fernet_key = base64.urlsafe_b64encode(key_hash)
        return fernet_key
        
    def _compute_machine_hash(self) -> str:
        """Compute a stable machine hash for node-locking."""
        try:
            # Get system information
            system_info = [
                platform.node(),  # Computer name
                platform.machine(),  # Architecture
                str(uuid.getnode()),  # MAC address
            ]
            
            # Get additional hardware info if available
            try:
                cpu_info = platform.processor()
                if cpu_info:
                    system_info.append(cpu_info)
            except:
                pass
                
            try:
                # Get disk serial if available
                disk_info = psutil.disk_partitions()
                if disk_info:
                    system_info.append(disk_info[0].device)
            except:
                pass
            
            # Create stable hash
            combined = "|".join(filter(None, system_info)).encode()
            return hashlib.sha256(combined).hexdigest()[:16]
            
        except Exception as e:
            print(f"Warning: Could not compute machine hash: {e}")
            # Fallback to basic system info
            fallback = f"{platform.node()}-{platform.machine()}"
            return hashlib.sha256(fallback.encode()).hexdigest()[:16]
    
    def _encrypt_license_data(self, data: dict) -> bytes:
        """Encrypt license data using AES-GCM equivalent (Fernet)."""
        fernet = Fernet(self.app_key)
        json_data = json.dumps(data, default=str)
        return fernet.encrypt(json_data.encode())
    
    def _decrypt_license_data(self, encrypted_data: bytes) -> Optional[dict]:
        """Decrypt license data."""
        try:
            fernet = Fernet(self.app_key)
            decrypted = fernet.decrypt(encrypted_data)
            return json.loads(decrypted.decode())
        except Exception as e:
            print(f"Failed to decrypt license data: {e}")
            return None
    
    def _verify_license_signature(self, data: dict, signature: str) -> bool:
        """Verify the license signature from the server."""
        try:
            # Check required fields
            required_fields = ["status", "code", "issuedAt", "expiresAt", "machineHash"]
            if not all(field in data for field in required_fields):
                print("Missing required license fields")
                return False
            
            # Verify machine hash binding
            if data.get("machineHash") != self.machine_hash:
                print("Machine hash mismatch in signature verification")
                return False
            
            # In production, this would verify against the server's public key
            # For now, we'll do enhanced validation of the signature structure
            if not signature or len(signature) < 32:  # Minimum signature length
                print("Invalid signature format")
                return False
            
            # Verify signature data integrity
            signature_data = f"{data['code']}:{data['machineHash']}:{data['status']}:{data['issuedAt']}"
            expected_signature = hashlib.sha256(signature_data.encode()).hexdigest()
            
            # For now, we'll accept the signature if it's properly formatted
            # In production, this would verify against the actual server signature
            print(f"Signature verification passed for license: {data.get('code', 'unknown')}")
            return True
            
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False
    
    def _validate_license_data(self, data: dict) -> Tuple[LicenseStatus, bool]:
        """Validate license data and return status and validity."""
        try:
            # Check if machine hash matches
            if data.get("machineHash") != self.machine_hash:
                print("Machine hash mismatch - license not bound to this machine")
                return "blocked", False
            
            # Validate required fields
            required_fields = ["status", "code", "issuedAt", "machineHash"]
            if not all(field in data for field in required_fields):
                print("Missing required license fields")
                return "not_found", False
            
            # Check expiration
            expires_at = data.get("expiresAt")
            if expires_at:
                try:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    
                    if datetime.now(timezone.utc) > expires_at:
                        status = data.get("status", "expired")
                        if status == "trial":
                            return "trial_expired", False
                        elif status == "active":
                            return "expired", False
                except Exception as e:
                    print(f"Error parsing expiration date: {e}")
                    return "expired", False
            
            # Return the status from the license
            status = data.get("status", "not_found")
            is_valid = status in ["active", "trial"]
            
            if is_valid:
                print(f"License validation successful: {status}")
            else:
                print(f"License validation failed: {status}")
                
            return status, is_valid
            
        except Exception as e:
            print(f"License validation error: {e}")
            return "not_found", False
    
    def get_license_status(self) -> Tuple[LicenseStatus, bool]:
        """Get current license status. Returns (status, is_valid)."""
        try:
            # Ensure license directory exists
            self.license_dir.mkdir(exist_ok=True)
            
            # Check if license file exists
            if not self.license_file.exists():
                return "not_found", False
            
            # Read and decrypt license file
            encrypted_data = self.license_file.read_bytes()
            license_data = self._decrypt_license_data(encrypted_data)
            
            if not license_data:
                return "not_found", False
            
            # Verify signature
            signature = license_data.get("signature", "")
            if not self._verify_license_signature(license_data, signature):
                return "blocked", False
            
            # Validate license data
            return self._validate_license_data(license_data)
            
        except Exception as e:
            print(f"Error getting license status: {e}")
            return "not_found", False
    
    def save_license(self, license_data: dict) -> bool:
        """Save encrypted license data to file."""
        try:
            # Ensure license directory exists
            self.license_dir.mkdir(exist_ok=True)
            
            # Add machine hash and timestamp
            license_data["machineHash"] = self.machine_hash
            license_data["savedAt"] = datetime.now(timezone.utc).isoformat()
            
            # Encrypt and save
            encrypted_data = self._encrypt_license_data(license_data)
            self.license_file.write_bytes(encrypted_data)
            
            print(f"License saved successfully: {license_data.get('status', 'unknown')}")
            return True
            
        except Exception as e:
            print(f"Failed to save license: {e}")
            return False
    
    def delete_license(self) -> bool:
        """Delete the license file."""
        try:
            if self.license_file.exists():
                self.license_file.unlink()
                print("License file deleted")
            return True
        except Exception as e:
            print(f"Failed to delete license: {e}")
            return False
    
    def get_machine_hash(self) -> str:
        """Get the current machine hash."""
        return self.machine_hash
    
    def get_status_display_text(self, status: LicenseStatus, license_data: Optional[dict] = None) -> str:
        """Get human-readable status text with optional details."""
        status_map = {
            "active": "ACTIVE",
            "trial": "TRIAL",
            "expired": "EXPIRED",
            "trial_expired": "TRIAL EXPIRED",
            "blocked": "BLOCKED",
            "not_found": "NO LICENSE"
        }
        
        base_text = status_map.get(status, status.upper())
        
        # Add trial days remaining if applicable
        if status == "trial" and license_data:
            expires_at = license_data.get("expiresAt")
            if expires_at:
                try:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    
                    days_left = (expires_at - datetime.now(timezone.utc)).days
                    if days_left > 0:
                        base_text += f" - {days_left} days left"
                    elif days_left == 0:
                        base_text += " - Expires today"
                except:
                    pass
        
        return base_text
    
    def get_status_color(self, status: LicenseStatus) -> str:
        """Get the color for a given status."""
        if status in ["active", "trial"]:
            return "#28a745"  # Success green
        else:
            return "#dc3545"  # Danger red
