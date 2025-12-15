"""
Validation result models.

Person B's validator produces these.
Person A's critic consumes them to revise builds.
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ErrorType(str, Enum):
    """Validation error categories"""
    # Compatibility errors
    SOCKET_MISMATCH = "socket_mismatch"
    RAM_TYPE_MISMATCH = "ram_type_mismatch"
    FORM_FACTOR_INCOMPATIBLE = "form_factor_incompatible"
    GPU_TOO_LONG = "gpu_too_long"
    COOLER_TOO_TALL = "cooler_too_tall"
    RADIATOR_NOT_SUPPORTED = "radiator_not_supported"
    
    # Power errors
    INSUFFICIENT_PSU = "insufficient_psu"
    MISSING_POWER_CONNECTORS = "missing_power_connectors"
    
    # Thermal errors
    COOLING_INSUFFICIENT = "cooling_insufficient"
    
    # Capacity errors
    INSUFFICIENT_RAM_SLOTS = "insufficient_ram_slots"
    INSUFFICIENT_M2_SLOTS = "insufficient_m2_slots"
    INSUFFICIENT_SATA_PORTS = "insufficient_sata_ports"
    INSUFFICIENT_PCIE_SLOTS = "insufficient_pcie_slots"
    
    # Budget errors
    OVER_BUDGET = "over_budget"
    
    # Missing components
    MISSING_GPU = "missing_gpu"
    MISSING_COMPONENT = "missing_component"


class WarningType(str, Enum):
    """Validation warning categories"""
    # Power warnings
    LOW_PSU_HEADROOM = "low_psu_headroom"
    EFFICIENCY_SUBOPTIMAL = "efficiency_suboptimal"
    
    # Thermal warnings
    THERMAL_RISK = "thermal_risk"
    AIRFLOW_CONCERN = "airflow_concern"
    
    # Performance warnings
    BOTTLENECK_RISK = "bottleneck_risk"
    RAM_SPEED_MISMATCH = "ram_speed_mismatch"
    
    # Compatibility warnings
    TIGHT_FIT = "tight_fit"
    CLEARANCE_MINIMAL = "clearance_minimal"
    
    # Budget warnings
    NEAR_BUDGET_LIMIT = "near_budget_limit"
    UNBALANCED_ALLOCATION = "unbalanced_allocation"
    
    # Future-proofing
    LIMITED_UPGRADE_PATH = "limited_upgrade_path"
    NO_SPARE_SLOTS = "no_spare_slots"


class ValidationIssue(BaseModel):
    """Base class for validation errors and warnings"""
    type: str = Field(description="Error or warning type code")
    component: Optional[str] = Field(
        default=None,
        description="Component(s) involved, e.g., 'cpu', 'psu', 'cpu+motherboard'"
    )
    message: str = Field(description="Human-readable explanation")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (e.g., expected vs actual values)"
    )
    severity: Optional[str] = Field(
        default=None,
        description="For warnings: 'low', 'medium', 'high'"
    )


class ValidationError(ValidationIssue):
    """Hard constraint violation - build is invalid"""
    pass


class ValidationWarning(ValidationIssue):
    """Soft constraint or potential risk - build is valid but suboptimal"""
    pass


class ValidationResult(BaseModel):
    """
    Output of build validation.
    
    Person B's validator returns this.
    Person A's critic uses it to guide revisions.
    """
    is_valid: bool = Field(description="True if build passes all hard constraints")
    
    errors: List[ValidationError] = Field(
        default_factory=list,
        description="Hard constraint violations (causes is_valid=False)"
    )
    
    warnings: List[ValidationWarning] = Field(
        default_factory=list,
        description="Soft constraints, risks, or suboptimal choices"
    )
    
    # Validation metadata
    validation_timestamp: Optional[str] = Field(default=None)
    validation_version: Optional[str] = Field(default="1.0")
    
    # Computed metrics
    computed_metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="e.g., actual PSU headroom %, thermal margin, cost breakdown"
    )
    
    def add_error(
        self,
        error_type: ErrorType,
        message: str,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Helper to add an error"""
        self.errors.append(ValidationError(
            type=error_type.value,
            component=component,
            message=message,
            details=details
        ))
        self.is_valid = False
    
    def add_warning(
        self,
        warning_type: WarningType,
        message: str,
        severity: str = "medium",
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Helper to add a warning"""
        self.warnings.append(ValidationWarning(
            type=warning_type.value,
            component=component,
            message=message,
            details=details,
            severity=severity
        ))
    
    def has_errors(self) -> bool:
        """Check if any errors exist"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if any warnings exist"""
        return len(self.warnings) > 0
    
    def get_errors_by_component(self, component: str) -> List[ValidationError]:
        """Get all errors for a specific component"""
        return [
            error for error in self.errors
            if error.component and component in error.component
        ]
    
    def get_high_severity_warnings(self) -> List[ValidationWarning]:
        """Get warnings marked as high severity"""
        return [
            warning for warning in self.warnings
            if warning.severity == "high"
        ]
    
    def summary(self) -> str:
        """Human-readable validation summary"""
        if self.is_valid and not self.has_warnings():
            return "✓ Build is valid with no issues"
        elif self.is_valid:
            return f"✓ Build is valid with {len(self.warnings)} warning(s)"
        else:
            return f"✗ Build is invalid: {len(self.errors)} error(s), {len(self.warnings)} warning(s)"
