"""
Data models and types for the license system.
Provides consistent typing across different database systems and better IDE support.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class LicenseStatus(str, Enum):
    """Valid license status values."""
    ACTIVE = "active"
    TRIAL = "trial"
    EXPIRED = "expired"
    TRIAL_EXPIRED = "trial_expired"
    BLOCKED = "blocked"
    NOT_FOUND = "not_found"


class LicenseType(str, Enum):
    """Valid license type values."""
    STANDARD = "Standard"
    PREMIUM = "Premium"
    ENTERPRISE = "Enterprise"
    TRIAL = "Trial"


@dataclass
class LicenseRecord:
    """
    Complete license record structure for database operations.
    
    Attributes:
        license_key: Unique license identifier.
        status: Current status of the license (from LicenseStatus enum).
        created_at: Timestamp when the license was created.
        max_devices: Maximum number of devices allowed.
        user: Associated user or account (optional).
        company: Optional company/organization name.
        email: Optional email address.
        license_type: Optional license type (from LicenseType enum).
        product: Optional product/software name.
        sales_representative: Optional sales representative.
        expires_at: Optional timestamp when the license expires.
        devices: List of registered device HWIDs.
        notes: Optional notes about the license.
        is_trial: True if status == 'trial', else False.
        license_id: Optional unique identifier.
        generated_by: Optional generator identifier.
        last_updated: Optional timestamp of last modification.
        metadata: Optional additional metadata.
    """
    license_key: str
    status: LicenseStatus
    created_at: datetime
    max_devices: int
    user: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    license_type: Optional[LicenseType] = None
    product: Optional[str] = None
    sales_representative: Optional[str] = None
    expires_at: Optional[datetime] = None
    devices: Optional[List[str]] = None
    notes: Optional[str] = None
    is_trial: Optional[bool] = None
    license_id: Optional[str] = None
    generated_by: Optional[str] = None
    last_updated: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        """Set default values after initialization."""
        if self.user is None:
            object.__setattr__(self, 'user', "")
        if self.company is None:
            object.__setattr__(self, 'company', "")
        if self.email is None:
            object.__setattr__(self, 'email', "")
        if self.product is None:
            object.__setattr__(self, 'product', "")
        if self.sales_representative is None:
            object.__setattr__(self, 'sales_representative', "")
        if self.devices is None:
            object.__setattr__(self, 'devices', [])
        if self.notes is None:
            object.__setattr__(self, 'notes', "")
        if self.is_trial is None:
            object.__setattr__(self, 'is_trial', False)
        if self.generated_by is None:
            object.__setattr__(self, 'generated_by', "")
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


# TypedDict classes for database operations
class LicenseInsertData(Dict[str, Any]):
    """Data structure for inserting new licenses."""
    license_key: str
    user: Optional[str]
    status: LicenseStatus
    created_at: Optional[datetime]
    expires_at: Optional[datetime]
    devices: Optional[List[str]]
    max_devices: int
    notes: Optional[str]
    company: Optional[str]
    email: Optional[str]
    license_type: Optional[LicenseType]
    product: Optional[str]
    sales_representative: Optional[str]
    is_trial: Optional[bool]
    license_id: Optional[str]
    generated_by: Optional[str]
    metadata: Optional[Dict[str, Any]]


class LicenseUpdateData(Dict[str, Any]):
    """Data structure for updating existing licenses."""
    user: Optional[str]
    status: Optional[LicenseStatus]
    expires_at: Optional[datetime]
    devices: Optional[List[str]]
    max_devices: Optional[int]
    notes: Optional[str]
    company: Optional[str]
    email: Optional[str]
    license_type: Optional[LicenseType]
    product: Optional[str]
    sales_representative: Optional[str]
    is_trial: Optional[bool]
    metadata: Optional[Dict[str, Any]]


class LicenseSearchFilters(Dict[str, Any]):
    """Filters for license search operations."""
    status_filter: Optional[LicenseStatus]
    user_filter: Optional[str]
    license_type_filter: Optional[LicenseType]
    company_filter: Optional[str]
    product_filter: Optional[str]
    created_after: Optional[datetime]
    created_before: Optional[datetime]
    expires_after: Optional[datetime]
    expires_before: Optional[datetime]
    limit: Optional[int]


class LicenseSearchResult(Dict[str, Any]):
    """Result structure for license search operations."""
    licenses: List[LicenseRecord]
    total_count: int
    has_more: bool


class DatabaseConnectionConfig(Dict[str, Any]):
    """Database connection configuration."""
    mongo_uri: str
    database_name: str
    collection_name: str
    max_pool_size: int
    retry_writes: bool
    server_selection_timeout_ms: int
    connect_timeout_ms: int
    socket_timeout_ms: int


class DeviceRegistrationData(Dict[str, Any]):
    """Data for device registration operations."""
    license_key: str
    device_hwid: str


class LicenseValidationResult(Dict[str, Any]):
    """Result of license validation operations."""
    is_valid: bool
    license_record: Optional[LicenseRecord]
    error_message: Optional[str]
    validation_details: Dict[str, Any]


# Type aliases for common operations
LicenseKey = str
DeviceHWID = str
UserID = str
CompanyName = str
ProductName = str
EmailAddress = str
Notes = str
GeneratedBy = str

# Union types for flexible field values
OptionalString = Optional[str]
OptionalInt = Optional[int]
OptionalBool = Optional[bool]
OptionalDateTime = Optional[datetime]
OptionalList = Optional[List[str]]
OptionalDict = Optional[Dict[str, Any]]

# Database operation result types
DatabaseResult = bool
DatabaseOperationResult = Union[bool, LicenseRecord, List[LicenseRecord], LicenseValidationResult]
