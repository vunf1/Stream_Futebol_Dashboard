"""
License Manager for Stream Futebol Dashboard
Handles license validation, encryption, and status management with machine binding.
"""

import os
import json
import hashlib
import uuid
import platform
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, Literal
Fernet = None  # lazy import
from ..config import AppConfig
from ..utils.online_time_provider import get_current_utc_time, get_time_source_info
from src.core.logger import get_logger
from .native_verifier import verify_signature as native_verify_signature

log = get_logger(__name__)

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
                # Get disk info if available (import psutil lazily)
                import psutil
                disk_info = psutil.disk_partitions()
                if disk_info:
                    system_info.append(disk_info[0].device)
            except:
                pass
            
            # Create stable hash
            combined = "|".join(filter(None, system_info)).encode()
            return hashlib.sha256(combined).hexdigest()[:16]
            
        except Exception as e:
            log.warning("license_machine_hash_compute_failed", extra={"error": str(e)})
            # Fallback to basic system info
            fallback = f"{platform.node()}-{platform.machine()}"
            return hashlib.sha256(fallback.encode()).hexdigest()[:16]
    
    def _encrypt_license_data(self, data: dict) -> bytes:
        """Encrypt license data using AES-GCM equivalent (Fernet)."""
        global Fernet
        if Fernet is None:
            from cryptography.fernet import Fernet as _F
            Fernet = _F
        fernet = Fernet(self.app_key)
        json_data = json.dumps(data, default=str)
        return fernet.encrypt(json_data.encode())
    
    def _decrypt_license_data(self, encrypted_data: bytes) -> Optional[dict]:
        """Decrypt license data."""
        try:
            global Fernet
            if Fernet is None:
                from cryptography.fernet import Fernet as _F
                Fernet = _F
            fernet = Fernet(self.app_key)
            decrypted = fernet.decrypt(encrypted_data)
            return json.loads(decrypted.decode())
        except Exception as e:
            log.error("license_decrypt_failed", extra={"error": str(e)})
            return None
    
    def _verify_license_signature(self, data: dict, signature: str) -> bool:
        """Verify the license signature (native when available)."""
        try:
            # Check required fields (except expiresAt which is validated later)
            required_fields = ["status", "code", "issuedAt", "machineHash"]
            if not all(field in data for field in required_fields):
                log.error("license_signature_missing_fields")
                return False

            # Verify machine hash binding early
            if data.get("machineHash") != self.machine_hash:
                log.error("license_signature_machine_hash_mismatch")
                return False

            ok = native_verify_signature(data, signature, logger=log)
            return bool(ok)

        except Exception as e:
            log.error("license_signature_verification_failed", extra={"error": str(e)})
            return False
    
    def _validate_license_data(self, data: dict) -> Tuple[LicenseStatus, bool]:
        """Validate license data and return status and validity."""
        try:
            log.info("license_validating", extra={"status": data.get("status"), "expires_at": str(data.get("expiresAt"))})
            
            # Check if machine hash matches
            if data.get("machineHash") != self.machine_hash:
                log.warning("license_machine_hash_mismatch")
                return "blocked", False
            
            # Validate required fields
            required_fields = ["status", "code", "issuedAt", "machineHash"]
            if not all(field in data for field in required_fields):
                log.error("license_missing_required_fields")
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
                    log.debug("license_expiration_check", extra={
                        "time_source": time_source,
                        "current_time": current_time.isoformat(),
                        "expires_at": expires_at.isoformat(),
                        "is_expired": current_time > expires_at,
                    })
                    
                    if current_time > expires_at:
                        # License is expired - determine the appropriate expired status
                        original_status = data.get("status", "expired")
                        if original_status == "trial":
                            log.info("license_trial_expired", extra={"expires_at": expires_at.isoformat(), "time_source": time_source})
                            return "trial_expired", False
                        else:
                            log.info("license_expired", extra={"expires_at": expires_at.isoformat(), "time_source": time_source})
                            return "expired", False
                    else:
                        # License is not expired, calculate days remaining for info
                        days_left = (expires_at - current_time).days
                        if days_left <= 7:
                            log.warning("license_expires_soon", extra={"days_left": days_left, "time_source": time_source})
                        
                except Exception as e:
                    log.error("license_expiration_parse_error", extra={"error": str(e)})
                    return "expired", False
            
            # If we reach here, license is not expired, check the status
            status = data.get("status", "not_found")
            is_valid = status in ["active", "trial"]
            
            if is_valid:
                log.info("license_validation_success", extra={"status": status})
            else:
                log.warning("license_validation_failed", extra={"status": status})
                
            return status, is_valid
            
        except Exception as e:
            log.error("license_validation_error", extra={"error": str(e)})
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
            log.error("license_get_status_error", extra={"error": str(e)})
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
                
                # Always update if status changed OR if database shows expired but local doesn't
                should_update = (
                    local_status != db_license_status or
                    (db_status in ["expired", "trial_expired"] and local_status not in ["expired", "trial_expired"])
                )
                
                if should_update:
                    log.info("license_status_changed", extra={"from": local_status, "to": db_status})
                    
                    # Update the license data with database values
                    updated_license_data = current_license_data.copy()
                    updated_license_data.update(db_license_data)
                    
                    # Ensure the status field is correctly set from database validation
                    if db_status in ["expired", "trial_expired"]:
                        updated_license_data["status"] = db_status
                        log.info("license_status_set_expired", extra={"status": db_status})
                    
                    # Save updated license to local file
                    if self.save_license(updated_license_data):
                        log.info("license_save_success", extra={"status": db_status})
                        return True
                    else:
                        log.error("license_save_failed")
                        return False
                else:
                    log.debug("license_status_unchanged", extra={"status": db_status})
                    return True
            else:
                log.warning("license_not_found_in_database", extra={"status": db_status})
                return False
                
        except Exception as e:
            log.error("license_refresh_error", extra={"error": str(e)})
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
            
            log.info("license_saved", extra={"status": license_data.get("status", "unknown")})
            return True
            
        except Exception as e:
            log.error("license_save_failed", extra={"error": str(e)})
            return False
    
    def delete_license(self) -> bool:
        """Delete the license file."""
        try:
            if self.license_file.exists():
                self.license_file.unlink()
                log.info("license_file_deleted")
            return True
        except Exception as e:
            log.error("license_delete_failed", extra={"error": str(e)})
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
            log.error("license_get_details_error", extra={"error": str(e)})
            return None

    def test_license_validation(self) -> None:
        """Test license validation and print detailed information for debugging."""
        log.info("license_validation_test_start")
        
        try:
            # Check if license file exists
            if not self.license_file.exists():
                log.error("license_validation_test_no_file")
                return
            
            log.info("license_validation_test_file_found", extra={"path": str(self.license_file)})
            
            # Get license details
            license_details = self.get_license_details()
            if not license_details:
                log.error("license_validation_test_decrypt_failed")
                return
            
            log.info("license_validation_test_info", extra={
                "status": license_details.get("status", "unknown"),
                "issued_at": str(license_details.get("issuedAt", "unknown")),
                "expires_at": str(license_details.get("expiresAt", "unknown")),
                "machine_hash_match": license_details.get("machineHash") == self.machine_hash,
            })
            
            if "_debug" in license_details:
                debug = license_details["_debug"]
                log.debug("license_validation_test_debug", extra={
                    "current_time": debug.get("current_time", "unknown"),
                    "expires_at": debug.get("expires_at", "unknown"),
                    "is_expired": debug.get("is_expired", "unknown"),
                    "days_left": debug.get("days_left", "unknown"),
                    "machine_hash_match": debug.get("machine_hash_match", "unknown"),
                })
            
            # Test validation
            status, is_valid = self.get_license_status()
            log.info("license_validation_test_result", extra={"status": status, "is_valid": is_valid})
            
            if is_valid:
                log.info("license_validation_test_valid")
            else:
                log.warning("license_validation_test_invalid")
                
        except Exception as e:
            log.error("license_validation_test_error", extra={"error": str(e)}, exc_info=True)
        
        log.info("license_validation_test_end")
