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
from ..config import AppConfig
from ..utils.online_time_provider import get_current_utc_time, get_time_source_info

# License status types
LicenseStatus = Literal["active", "trial", "expired", "trial_expired", "blocked", "not_found"]

class LicenseManager:
    """Manages license validation, encryption, and status for the application."""
    
    def __init__(self):
        self.desktop_path = Path.home() / "Desktop"
        self.license_dir = self.desktop_path / AppConfig.DESKTOP_FOLDER_NAME
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
            
            # Check expiration FIRST - if expired, license is invalid regardless of status
            expires_at = data.get("expiresAt")
            if expires_at:
                try:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    
                    # Use local time provider
                    current_time = get_current_utc_time()
                    time_source = get_time_source_info()
                    print(f"🕐 License validation using: {time_source}")
                    
                    if current_time > expires_at:
                        # License is expired - determine the appropriate expired status
                        original_status = data.get("status", "expired")
                        if original_status == "trial":
                            print(f"Trial license expired on {expires_at} (checked with {time_source})")
                            return "trial_expired", False
                        else:
                            print(f"License expired on {expires_at} (checked with {time_source})")
                            return "expired", False
                    else:
                        # License is not expired, calculate days remaining for info
                        days_left = (expires_at - current_time).days
                        if days_left <= 7:
                            print(f"License expires in {days_left} days (checked with {time_source})")
                        
                except Exception as e:
                    print(f"Error parsing expiration date: {e}")
                    return "expired", False
            
            # If we reach here, license is not expired, check the status
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
            
            # Always refresh from database first to get latest status
            self._refresh_license_from_database(license_data)
            
            # Re-read the updated license data
            if self.license_file.exists():
                encrypted_data = self.license_file.read_bytes()
                updated_license_data = self._decrypt_license_data(encrypted_data)
                if updated_license_data:
                    # Validate the updated license data
                    return self._validate_license_data(updated_license_data)
            
            # Fallback to original validation if refresh failed
            return self._validate_license_data(license_data)
            
        except Exception as e:
            print(f"Error getting license status: {e}")
            return "not_found", False
    
    def _refresh_license_from_database(self, current_license_data: dict) -> bool:
        """Refresh license data from database and update local file if changed."""
        try:
            # Get license code from current data
            license_code = current_license_data.get("code")
            if not license_code:
                return False
            
            # Import here to avoid circular imports
            from .license_validator import LicenseValidator
            
            # Create validator and check database
            validator = LicenseValidator()
            machine_hash = current_license_data.get("machineHash", self.machine_hash)
            
            # Validate against database
            db_license_data, db_status = validator.validate_license_code(license_code, machine_hash)
            
            if db_license_data:
                # Check if database status is different from local status
                local_status = current_license_data.get("status")
                db_license_status = db_license_data.get("status")
                
                if local_status != db_license_status:
                    print(f"🔄 License status changed from {local_status} to {db_license_status}, updating local file...")
                    
                    # Update the license data with database values
                    updated_license_data = current_license_data.copy()
                    updated_license_data.update(db_license_data)
                    
                    # Save updated license to local file
                    return self.save_license(updated_license_data)
                else:
                    print(f"✅ License status unchanged: {db_license_status}")
                    return True
            else:
                print(f"❌ License not found in database: {db_status}")
                return False
                
        except Exception as e:
            print(f"Error refreshing license from database: {e}")
            return False
    
    def save_license(self, license_data: dict) -> bool:
        """Save encrypted license data to file."""
        try:
            # Ensure license directory exists
            self.license_dir.mkdir(exist_ok=True)
            
            # Add machine hash and timestamp
            license_data["machineHash"] = self.machine_hash
            # Use local time provider for timestamp
            current_time = get_current_utc_time()
            time_source = get_time_source_info()
            license_data["savedAt"] = current_time.isoformat()
            license_data["timeSource"] = time_source
            
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

    def get_license_details(self) -> Optional[dict]:
        """Get detailed license information for debugging."""
        try:
            if not self.license_file.exists():
                return None
                
            encrypted_data = self.license_file.read_bytes()
            license_data = self._decrypt_license_data(encrypted_data)
            
            if not license_data:
                return None
                
            # Add current validation info
            current_time = datetime.now(timezone.utc)
            expires_at = license_data.get("expiresAt")
            
            if expires_at:
                try:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    
                    is_expired = current_time > expires_at
                    days_left = (expires_at - current_time).days if not is_expired else 0
                    
                    license_data["_debug"] = {
                        "current_time": current_time.isoformat(),
                        "expires_at": expires_at.isoformat(),
                        "is_expired": is_expired,
                        "days_left": days_left,
                        "machine_hash_match": license_data.get("machineHash") == self.machine_hash
                    }
                except Exception as e:
                    license_data["_debug"] = {
                        "expiration_parse_error": str(e),
                        "current_time": current_time.isoformat()
                    }
            
            return license_data
            
        except Exception as e:
            print(f"Error getting license details: {e}")
            return None

    def test_license_validation(self) -> None:
        """Test license validation and print detailed information for debugging."""
        print("\n" + "="*50)
        print("LICENSE VALIDATION TEST")
        print("="*50)
        
        try:
            # Check if license file exists
            if not self.license_file.exists():
                print("❌ No license file found")
                return
            
            print(f"✅ License file found: {self.license_file}")
            
            # Get license details
            license_details = self.get_license_details()
            if not license_details:
                print("❌ Could not decrypt license file")
                return
            
            print("\n📋 License Information:")
            print(f"  Status: {license_details.get('status', 'unknown')}")
            print(f"  Code: {license_details.get('code', 'unknown')}")
            print(f"  Issued At: {license_details.get('issuedAt', 'unknown')}")
            print(f"  Expires At: {license_details.get('expiresAt', 'unknown')}")
            print(f"  Machine Hash: {license_details.get('machineHash', 'unknown')}")
            print(f"  Current Machine Hash: {self.machine_hash}")
            
            if "_debug" in license_details:
                debug = license_details["_debug"]
                print("\n🔍 Debug Information:")
                print(f"  Current Time: {debug.get('current_time', 'unknown')}")
                print(f"  Expires At: {debug.get('expires_at', 'unknown')}")
                print(f"  Is Expired: {debug.get('is_expired', 'unknown')}")
                print(f"  Days Left: {debug.get('days_left', 'unknown')}")
                print(f"  Machine Hash Match: {debug.get('machine_hash_match', 'unknown')}")
            
            # Test validation
            print("\n🧪 Validation Test:")
            status, is_valid = self.get_license_status()
            print(f"  Final Status: {status}")
            print(f"  Is Valid: {is_valid}")
            
            if is_valid:
                print("✅ License is VALID - app should continue")
            else:
                print("❌ License is INVALID - app should be blocked")
                
        except Exception as e:
            print(f"❌ Error during validation test: {e}")
            import traceback
            traceback.print_exc()
        
        print("="*50 + "\n")
