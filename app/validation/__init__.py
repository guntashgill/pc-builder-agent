"""
Validation module initialization.

Provides main validate_build() function that orchestrates all validation checks.
"""
from app.models.build import PCBuild
from app.models.validation import ValidationResult
from app.validation.compatibility import (
    validate_cpu_motherboard_socket,
    validate_ram_compatibility,
    validate_motherboard_form_factor,
    validate_gpu_clearance,
    validate_cpu_cooler_clearance,
    validate_cooling_capacity,
    validate_storage_connectivity,
    validate_integrated_graphics,
)
from app.validation.power import (
    validate_psu_wattage,
    validate_power_connectors,
)


def validate_build(build: PCBuild) -> ValidationResult:
    """
    Main validation entry point.
    
    Runs all compatibility and power validation checks on a PC build.
    
    Args:
        build: PCBuild specification to validate
        
    Returns:
        ValidationResult with errors and warnings
        
    Example:
        >>> from app.models.build import PCBuild
        >>> build = PCBuild(...)
        >>> result = validate_build(build)
        >>> if result.is_valid:
        ...     print("Build is valid!")
        >>> else:
        ...     for error in result.errors:
        ...         print(f"Error: {error.message}")
    """
    result = ValidationResult(is_valid=True)
    
    # Run all compatibility checks
    validate_cpu_motherboard_socket(build, result)
    validate_ram_compatibility(build, result)
    validate_motherboard_form_factor(build, result)
    validate_gpu_clearance(build, result)
    validate_cpu_cooler_clearance(build, result)
    validate_cooling_capacity(build, result)
    validate_storage_connectivity(build, result)
    validate_integrated_graphics(build, result)
    
    # Run all power checks
    validate_psu_wattage(build, result)
    validate_power_connectors(build, result)
    
    return result


__all__ = [
    'validate_build',
    'ValidationResult',
]
