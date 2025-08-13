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
from src.core.models import LicenseRecord, LicenseStatus, LicenseType
from src.utils.online_time_provider import get_current_utc_time, get_time_source_info

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
        """Validate license code against MongoDB collection using robust data models."""
        try:
            print("=== MONGODB LICENSE VALIDATION ===")
            
            # Clean the code
            clean_code = code.strip().upper()
            print(f"🔍 Validating code: {clean_code}")
            
            # Query the licenses collection using the actual field name from your schema
            license_doc = collection.find_one({"license_key": clean_code})
            
            if not license_doc:
                print("❌ License not found in MongoDB")
                return {"error": "License not found"}, "not_found"
            
            print(f"📋 MongoDB license document: {license_doc}")
            
            # Check if license is blocked (assuming blocked status is in the status field)
            if license_doc.get("status") == "blocked":
                print("❌ License is blocked")
                # Don't return early, continue to create license data with blocked status
            
            # Check expiration using the actual field name from your schema
            expires_at = license_doc.get("expires_at")
            print(f"🔍 Raw expires_at value: {expires_at}")
            print(f"🔍 expires_at type: {type(expires_at)}")
            
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
                    
                    print(f"🔍 Parsed expires_at datetime: {expires_at}")
                    
                    # Use online time provider with fallback to local time
                    current_time = get_current_utc_time()
                    time_source, is_online = get_time_source_info()
                    print(f"🕐 MongoDB license validation using: {time_source}")
                    
                    # Ensure both times are timezone-aware for comparison
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    
                    if current_time > expires_at:
                        current_status = license_doc.get("status", "expired")
                        if current_status == "trial":
                            # Update database status to trial_expired
                            new_status = "trial_expired"
                            print(f"❌ Trial license expired on {expires_at} (checked with {time_source})")
                            print(f"🔄 Updating database status from '{current_status}' to '{new_status}'")
                            
                            # Update the database
                            try:
                                collection.update_one(
                                    {"license_key": clean_code},
                                    {
                                        "$set": {
                                            "status": new_status,
                                            "last_updated": datetime.now(timezone.utc)
                                        }
                                    }
                                )
                                print(f"✅ Database updated: status changed to '{new_status}'")
                            except Exception as db_error:
                                print(f"⚠️ Failed to update database status: {db_error}")
                            
                            return {"error": "Trial license expired"}, new_status
                        else:
                            # Update database status to expired
                            new_status = "expired"
                            print(f"❌ License expired on {expires_at} (checked with {time_source})")
                            print(f"🔄 Updating database status from '{current_status}' to '{new_status}'")
                            
                            # Update the database
                            try:
                                collection.update_one(
                                    {"license_key": clean_code},
                                    {
                                        "$set": {
                                            "status": new_status,
                                            "last_updated": datetime.now(timezone.utc)
                                        }
                                    }
                                )
                                print(f"✅ Database updated: status changed to '{new_status}'")
                            except Exception as db_error:
                                print(f"⚠️ Failed to update database status: {db_error}")
                            
                            return {"error": "License expired"}, new_status
                    else:
                        print(f"✅ License not expired, expires on {expires_at} (checked with {time_source})")
                        # If license is not expired but database shows expired status, update it
                        current_status = license_doc.get("status", "active")
                        if current_status in ["expired", "trial_expired"]:
                            print(f"🔄 License not expired but database shows '{current_status}', updating to 'active'")
                            try:
                                collection.update_one(
                                    {"license_key": clean_code},
                                    {
                                        "$set": {
                                            "status": "active",
                                            "last_updated": datetime.now(timezone.utc)
                                        }
                                    }
                                )
                                print(f"✅ Database updated: status corrected to 'active'")
                            except Exception as db_error:
                                print(f"⚠️ Failed to update database status: {db_error}")
                        
                except Exception as e:
                    print(f"❌ Error parsing expiration date '{expires_at}': {e}")
                    # If we can't parse the date, assume it's valid
                    pass
            else:
                print("⚠️ No expires_at field found in MongoDB document")
            
            # Re-fetch the license document in case status was updated during expiration check
            updated_license_doc = collection.find_one({"license_key": clean_code})
            if updated_license_doc:
                license_doc = updated_license_doc
            
            # Get license status
            status = license_doc.get("status", "not_found")
            print(f"🔍 License status: {status}")
            
            # Create a proper LicenseRecord object for validation (for all statuses)
            license_record = self._create_license_record_from_mongodb(license_doc, clean_code)
            if not license_record:
                print("❌ Failed to create valid LicenseRecord from MongoDB data")
                return {"error": "Invalid license data structure"}, "not_found"
            
            # Create license payload using the validated LicenseRecord
            license_data = {
                "status": license_record.status.value,
                "code": clean_code,
                "features": license_doc.get("features", ["basic"]),
                "issuedAt": license_record.created_at.isoformat(),
                "expiresAt": license_record.expires_at.isoformat() if license_record.expires_at else "",
                "machineHash": machine_hash,
                "signature": self._create_mock_signature(clean_code, machine_hash, status),
                "user": license_record.user or "Unknown User",
                "email": license_record.email or "No Email",
                "company": license_record.company or "No Company",
                "max_devices": license_record.max_devices,
                "metadata": {
                    "type": "mongodb",
                    "version": "1.0.0",
                    "licenseId": str(license_doc.get("_id", "")),
                    "licenseRecord": {
                        "is_trial": license_record.is_trial,
                        "license_type": license_record.license_type.value if license_record.license_type else None,
                        "product": license_record.product,
                        "devices_count": len(license_record.devices) if license_record.devices else 0
                    }
                }
            }
            
            # Debug: Show field mapping using the validated LicenseRecord
            print(f"🔍 Field mapping (using validated LicenseRecord):")
            print(f"  created_at -> issuedAt: {license_record.created_at}")
            print(f"  expires_at -> expiresAt: {license_record.expires_at or 'NO EXPIRATION'}")
            print(f"  max_devices -> max_devices: {license_record.max_devices}")
            print(f"  user -> user: {license_record.user or 'NO USER'}")
            print(f"  company -> company: {license_record.company or 'NO COMPANY'}")
            print(f"  is_trial: {license_record.is_trial}")
            print(f"  devices_count: {len(license_record.devices) if license_record.devices else 0}")
            
            # Return the license data for all statuses, let the caller handle validation
            return license_data, status
                
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
                "timestamp": get_current_utc_time().isoformat()
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
            # Treat trial_expired as expired
            if status == "trial_expired":
                status = "expired"
            error_msg = f"License {status.replace('_', ' ')}"
            return {"error": error_msg}, status

    def _create_license_record_from_mongodb(self, license_doc: Dict, clean_code: str) -> Optional[LicenseRecord]:
        """
        Create a LicenseRecord object from MongoDB document data.
        This ensures type safety and validates the data structure.
        """
        try:
            # Extract and validate required fields
            status_str = license_doc.get("status", "").lower()
            
            # Map status string to LicenseStatus enum
            try:
                status = LicenseStatus(status_str)
            except ValueError:
                print(f"❌ Invalid status value: {status_str}")
                return None
            
            # Parse dates
            created_at = self._parse_mongodb_date(license_doc.get("created_at"))
            expires_at = self._parse_mongodb_date(license_doc.get("expires_at"))
            
            if not created_at:
                print("❌ Missing or invalid created_at field")
                return None
            
            # Create LicenseRecord with proper validation
            license_record = LicenseRecord(
                license_key=clean_code,
                status=status,
                created_at=created_at,
                max_devices=int(license_doc.get("max_devices", 1)),
                user=license_doc.get("user", ""),
                company=license_doc.get("company", ""),
                email=license_doc.get("email", ""),
                license_type=self._parse_license_type(license_doc.get("license_type")),
                product=license_doc.get("product", ""),
                sales_representative=license_doc.get("sales_representative", ""),
                expires_at=expires_at,
                devices=license_doc.get("devices", []),
                notes=license_doc.get("notes", ""),
                is_trial=(status == LicenseStatus.TRIAL),
                license_id=license_doc.get("license_id"),
                generated_by=license_doc.get("generated_by", ""),
                last_updated=self._parse_mongodb_date(license_doc.get("last_updated")),
                metadata=license_doc.get("metadata", {})
            )
            
            print(f"✅ Created LicenseRecord: {license_record}")
            return license_record
            
        except Exception as e:
            print(f"❌ Error creating LicenseRecord: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_mongodb_date(self, date_value) -> Optional[datetime]:
        """Parse date values from MongoDB document."""
        if not date_value:
            return None
            
        try:
            if isinstance(date_value, datetime):
                return date_value.replace(tzinfo=timezone.utc) if date_value.tzinfo is None else date_value
            elif isinstance(date_value, str):
                # Handle different date formats
                if date_value.count('-') == 2:  # YYYY-MM-DD format
                    parsed_date = datetime.strptime(date_value + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                else:
                    parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                
                return parsed_date.replace(tzinfo=timezone.utc) if parsed_date.tzinfo is None else parsed_date
            else:
                print(f"⚠️ Unsupported date type: {type(date_value)}")
                return None
                
        except Exception as e:
            print(f"❌ Error parsing date '{date_value}': {e}")
            return None
    
    def _parse_license_type(self, type_value) -> Optional[LicenseType]:
        """Parse license type from MongoDB document."""
        if not type_value:
            return None
            
        try:
            return LicenseType(type_value)
        except ValueError:
            print(f"⚠️ Invalid license type: {type_value}")
            return None

    def test_mongodb_connection(self) -> None:
        """Test MongoDB connection and inspect license collection structure."""
        print("\n" + "="*60)
        print("MONGODB CONNECTION TEST")
        print("="*60)
        
        try:
            collection = self._get_mongo_connection()
            if collection is None:
                print("❌ MongoDB connection failed")
                return
            
            print("✅ MongoDB connection successful")
            print(f"📊 Database: {self.mongo_db_name}")
            print(f"📊 Collection: {self.mongo_collection_name}")
            
            # Count total documents
            total_docs = collection.count_documents({})
            print(f"📊 Total documents in collection: {total_docs}")
            
            if total_docs > 0:
                # Get a sample document to see the structure
                sample_doc = collection.find_one({})
                if sample_doc:
                    print(f"\n📋 Sample document structure:")
                    for key, value in sample_doc.items():
                        print(f"  {key}: {value} (type: {type(value)})")
                
                # Check for specific fields we need (using your exact field names)
                print(f"\n🔍 Checking for required fields (using your schema):")
                required_fields = ["license_key", "status", "expires_at", "max_devices", "created_at"]
                for field in required_fields:
                    count = collection.count_documents({field: {"$exists": True}})
                    print(f"  {field}: {count} documents have this field")
                
                # Check for alternative field names that might exist
                print(f"\n🔍 Checking for alternative field names:")
                alt_fields = ["expiry", "expiration", "maxDevices", "device_limit", "created", "createdAt"]
                for field in alt_fields:
                    count = collection.count_documents({field: {"$exists": True}})
                    if count > 0:
                        print(f"  {field}: {count} documents have this field")
                
                # Show all unique field names in the collection
                print(f"\n🔍 All unique field names in collection:")
                pipeline = [
                    {"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}},
                    {"$unwind": "$arrayofkeyvalue"},
                    {"$group": {"_id": None, "allkeys": {"$addToSet": "$arrayofkeyvalue.k"}}}
                ]
                try:
                    result = list(collection.aggregate(pipeline))
                    if result:
                        all_fields = sorted(result[0]["allkeys"])
                        for field in all_fields:
                            print(f"  {field}")
                except Exception as e:
                    print(f"  Could not get field list: {e}")
            
        except Exception as e:
            print(f"❌ Error testing MongoDB connection: {e}")
            import traceback
            traceback.print_exc()
        
        print("="*60 + "\n")
