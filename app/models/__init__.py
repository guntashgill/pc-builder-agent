"""Data models for PC builder agent"""
from app.models.constraints import Constraints, PeripheralPreferences
from app.models.build import (
    PCBuild,
    CPUSpec,
    GPUSpec,
    RAMSpec,
    StorageSpec,
    MotherboardSpec,
    ChassisSpec,
    PSUSpec,
    CoolingSpec,
    PeripheralSpec,
)
from app.models.validation import ValidationResult, ValidationIssue

__all__ = [
    # Constraints
    "Constraints",
    "PeripheralPreferences",
    # Build components
    "PCBuild",
    "CPUSpec",
    "GPUSpec",
    "RAMSpec",
    "StorageSpec",
    "MotherboardSpec",
    "ChassisSpec",
    "PSUSpec",
    "CoolingSpec",
    "PeripheralSpec",
    # Validation
    "ValidationResult",
    "ValidationIssue",
]
