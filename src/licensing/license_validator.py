"""
License Validator Service
Communicates with MongoDB to validate license codes and return signed payloads.
"""

import os
import json
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
import requests
from src.core import SecureEnvLoader
from src.core import get_env
from src.core import _get_mongo_client
from src.core.env_loader import ensure_env_loaded

class LicenseValidator:
    """Validates license codes against MongoDB and returns signed payloads."""
    
    def __init__(self):
        # Defer environment loading until actually needed to avoid PyInstaller import issues
        self._env_loaded = False
        
        # Get MongoDB configuration
        try:
            self._ensure_env_loaded()
            self.mongo_uri = get_env("MONGO_URI")
            self.mongo_db_name = get_env("MONGO_DB_license")
            self.mongo_collection_name = get_env("MONGO_COLLECTION_licences")
        except RuntimeError as e:
            print(f"Warning: MongoDB environment variables not set: {e}")
            self.mongo_uri = None
            self.mongo_db_name = "license_db"
            self.mongo_collection_name = "licenses"
        
        # Get API configuration with fallbacks
        try:
            self.api_base_url = get_env("LICENSE_API_URL")
        except RuntimeError:
            self.api_base_url = "http://localhost:3000"
            
        try:
            self.api_key = get_env("LICENSE_API_KEY")
        except RuntimeError:
            self.api_key = ""
    
    def _ensure_env_loaded(self):
        """Ensure environment variables are loaded before using them"""
        if not self._env_loaded:
            ensure_env_loaded()
            self._env_loaded = True
    
    def _get_mongo_connection(self):
        """Get MongoDB connection for license validation."""
        try:
            if not self.mongo_uri:
                print("Warning: No MongoDB URI configured, using mock validation")
                return None
                
            client = _get_mongo_client()
            db = client[self.mongo_db_name]
            collection = db[self.mongo_collection_name]
            return collection
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return None
    
    def validate_license_code(self, code: str, machine_hash: str) -> Tuple[Dict, str]:
        """
        Validate a license code against MongoDB.
        
        Args:
            code: The license code to validate
            machine_hash: The machine hash for node-locking
            
        Returns:
            Tuple of (license_data, status)
        """
        try:
            # Try to validate against MongoDB first
            collection = self._get_mongo_connection()
            if collection is not None:
                return self._validate_against_mongodb(code, machine_hash, collection)
            
            # Fallback to API validation if MongoDB not available
            return self._validate_against_api(code, machine_hash)
                
        except Exception as e:
            # Fallback to mock validation for development
            print(f"License validation error: {e}, using mock validation")
            return self.validate_mock_license(code, machine_hash)
    
    def _validate_against_mongodb(self, code: str, machine_hash: str, collection) -> Tuple[Dict, str]:
        """Validate license code against MongoDB collection."""
        try:
            # Clean the code
            clean_code = code.strip().upper()
            
            # Query the licenses collection using the actual field name from your schema
            license_doc = collection.find_one({"license_key": clean_code})
            
            if not license_doc:
                return {"error": "License not found"}, "not_found"
            
            # Check if license is blocked (assuming blocked status is in the status field)
            if license_doc.get("status") == "blocked":
                return {"error": "License is blocked"}, "blocked"
            
            # Check expiration using the actual field name from your schema
            expires_at = license_doc.get("expiry")
            if expires_at:
                try:
                    if isinstance(expires_at, str):
                        # Handle different date formats
                        if expires_at.count('-') == 2:  # YYYY-MM-DD format
                            # Add time component to make it a full datetime
                            expires_at = datetime.strptime(expires_at + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                            expires_at = expires_at.replace(tzinfo=timezone.utc)
                        else:
                            # Try ISO format
                            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        
                        if expires_at.tzinfo is None:
                            expires_at = expires_at.replace(tzinfo=timezone.utc)
                    
                    if datetime.now(timezone.utc) > expires_at:
                        status = license_doc.get("status", "expired")
                        if status == "trial":
                            return {"error": "Trial license expired"}, "trial_expired"
                        else:
                            return {"error": "License expired"}, "expired"
                except Exception as e:
                    print(f"Error parsing expiration date '{expires_at}': {e}")
                    # If we can't parse the date, assume it's valid
                    pass
            
            # Get license status
            status = license_doc.get("status", "not_found")
            
            if status in ["active", "trial"]:
                # Create license payload
                license_data = {
                    "status": status,
                    "code": clean_code,
                    "features": license_doc.get("features", ["basic"]),
                    "issuedAt": license_doc.get("created", datetime.now(timezone.utc).isoformat()),
                    "expiresAt": license_doc.get("expiry", ""),
                    "machineHash": machine_hash,
                    "signature": self._create_mock_signature(clean_code, machine_hash, status),
                    "user": license_doc.get("user", "Unknown User"),
                    "email": license_doc.get("email", "No Email"),
                    "company": license_doc.get("company", "No Company"),
                    "metadata": {
                        "type": "mongodb",
                        "version": "1.0.0",
                        "licenseId": str(license_doc.get("_id", ""))
                    }
                }
                return license_data, status
            else:
                error_msg = f"License status: {status}"
                return {"error": error_msg}, status
                
        except Exception as e:
            print(f"MongoDB validation error: {e}")
            return {"error": f"Database error: {str(e)}"}, "not_found"
    
    def _validate_against_api(self, code: str, machine_hash: str) -> Tuple[Dict, str]:
        """Validate license code against external API."""
        try:
            # Prepare request payload
            payload = {
                "code": code.strip().upper(),
                "machineHash": machine_hash,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Add API key if available
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Make request to license validation endpoint
            response = requests.post(
                f"{self.api_base_url}/license/activate",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "not_found")
                
                if status in ["active", "trial"]:
                    # Return the full license payload for valid licenses
                    return data, status
                else:
                    # Return error information for invalid licenses
                    error_msg = data.get("message", "License validation failed")
                    return {"error": error_msg}, status
            else:
                # Handle HTTP errors
                error_msg = f"Server error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    pass
                
                return {"error": error_msg}, "not_found"
                
        except requests.exceptions.RequestException as e:
            # Handle network/connection errors
            error_msg = f"Connection error: {str(e)}"
            return {"error": error_msg}, "not_found"
        except Exception as e:
            # Handle other errors
            error_msg = f"Validation error: {str(e)}"
            return {"error": error_msg}, "not_found"
    
    def _create_mock_signature(self, code: str, machine_hash: str, status: str) -> str:
        """Create a mock signature for development purposes."""
        signature_data = f"{code}:{machine_hash}:{status}:{datetime.now(timezone.utc).isoformat()}"
        return hmac.new(
            b"mock-secret-key", 
            signature_data.encode(), 
            hashlib.sha256
        ).hexdigest()
    
    def create_mock_license(self, code: str, machine_hash: str, status: str = "trial") -> Dict:
        """
        Create a mock license for development/testing purposes.
        In production, this would be replaced by server-side validation.
        """
        now = datetime.now(timezone.utc)
        
        if status == "trial":
            expires_at = now + timedelta(days=30)  # 30-day trial
        elif status == "active":
            expires_at = now + timedelta(days=365)  # 1-year license
        else:
            expires_at = now
        
        # Create a mock signature (in production, this would be server-signed)
        signature_data = f"{code}:{machine_hash}:{status}:{expires_at.isoformat()}"
        mock_signature = hmac.new(
            b"mock-secret-key", 
            signature_data.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        license_data = {
            "status": status,
            "code": code,
            "features": ["basic", "advanced", "premium"],
            "issuedAt": now.isoformat(),
            "expiresAt": expires_at.isoformat(),
            "machineHash": machine_hash,
            "signature": mock_signature,
            "user": "Demo User",
            "email": "demo@example.com",
            "company": "Demo Company",
            "metadata": {
                "type": "development",
                "version": "1.0.0"
            }
        }
        
        return license_data
    
    def validate_mock_license(self, code: str, machine_hash: str) -> Tuple[Dict, str]:
        """
        Mock license validation for development/testing.
        In production, this would call the real server.
        """
        # Simple mock validation logic
        if not code or len(code) < 8:
            return {"error": "Invalid license code format"}, "not_found"
        
        # Mock different license types based on code
        if code.startswith("TRIAL"):
            status = "trial"
        elif code.startswith("ACTIVE"):
            status = "active"
        elif code.startswith("EXPIRED"):
            status = "expired"
        elif code.startswith("BLOCKED"):
            status = "blocked"
        else:
            status = "not_found"
        
        if status in ["active", "trial"]:
            license_data = self.create_mock_license(code, machine_hash, status)
            return license_data, status
        else:
            error_msg = f"License {status.replace('_', ' ')}"
            return {"error": error_msg}, status
