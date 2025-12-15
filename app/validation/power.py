"""
Power estimation and PSU validation logic.

Validates that PSU wattage is sufficient for the build with appropriate headroom.
"""
from typing import Optional
from app.models.build import PCBuild
from app.models.validation import ValidationResult, ErrorType, WarningType


# PSU efficiency losses (approximate)
EFFICIENCY_MULTIPLIERS = {
    "80+ Titanium": 0.96,
    "80+ Platinum": 0.94,
    "80+ Gold": 0.90,
    "80+ Silver": 0.88,
    "80+ Bronze": 0.85,
    "80+": 0.82,
}

# Recommended PSU headroom percentages
MINIMUM_PSU_HEADROOM = 0.20  # 20% minimum
RECOMMENDED_PSU_HEADROOM = 0.30  # 30% recommended
CRITICAL_PSU_HEADROOM = 0.15  # 15% triggers error


def estimate_total_power_draw(build: PCBuild) -> int:
    """
    Calculate estimated total system power draw in watts.
    
    Includes all components with realistic load estimates.
    """
    total_tdp = 0
    
    # CPU - use TDP rating
    total_tdp += build.cpu.tdp_w
    
    # GPU - use TDP rating if present
    if build.gpu:
        total_tdp += build.gpu.tdp_w
    
    # RAM - approximately 3-5W per 8GB
    ram_power = (build.ram.capacity_gb / 8) * 4
    total_tdp += int(ram_power)
    
    # Storage
    for storage in build.storage:
        if storage.type == "nvme":
            total_tdp += 8  # NVMe drives: 5-10W
        elif storage.type == "ssd":
            total_tdp += 3  # SATA SSD: 2-4W
        else:  # HDD
            total_tdp += 8  # HDD: 6-10W
    
    # Additional storage
    if build.additional_storage:
        for storage in build.additional_storage:
            if storage.type == "nvme":
                total_tdp += 8
            elif storage.type == "ssd":
                total_tdp += 3
            else:
                total_tdp += 8
    
    # Motherboard - approximately 50-80W
    total_tdp += 60
    
    # Cooling fans
    cooling_fans = build.cooling.fan_count
    if build.case_fans:
        cooling_fans += build.case_fans
    total_tdp += cooling_fans * 5  # ~5W per fan
    
    # AIO pump if applicable
    if build.cooling.type == "aio":
        total_tdp += 10  # AIO pump: ~10W
    
    # Chassis included fans
    total_tdp += build.chassis.included_fans * 5
    
    return total_tdp


def calculate_psu_headroom(psu_wattage: int, estimated_draw: int) -> float:
    """
    Calculate PSU headroom as a percentage.
    
    Returns: (available_power / estimated_draw) as decimal
    Example: 0.30 = 30% headroom
    """
    if estimated_draw <= 0:
        return 1.0
    
    available_power = psu_wattage - estimated_draw
    headroom = available_power / estimated_draw
    return headroom


def validate_psu_wattage(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate PSU wattage against estimated system power draw.
    
    Adds errors if PSU is insufficient.
    Adds warnings if headroom is low.
    """
    estimated_draw = estimate_total_power_draw(build)
    psu_wattage = build.psu.wattage
    headroom = calculate_psu_headroom(psu_wattage, estimated_draw)
    
    # Calculate actual usable wattage considering efficiency
    efficiency_multiplier = EFFICIENCY_MULTIPLIERS.get(
        build.psu.efficiency,
        0.85  # Default to 80+ Bronze if unknown
    )
    effective_wattage = int(psu_wattage * efficiency_multiplier)
    effective_headroom = calculate_psu_headroom(effective_wattage, estimated_draw)
    
    # Store computed metrics
    if not result.computed_metrics:
        result.computed_metrics = {}
    
    result.computed_metrics.update({
        "estimated_power_draw_w": estimated_draw,
        "psu_wattage": psu_wattage,
        "psu_headroom_pct": round(headroom * 100, 1),
        "effective_wattage": effective_wattage,
        "effective_headroom_pct": round(effective_headroom * 100, 1),
        "psu_efficiency": build.psu.efficiency,
    })
    
    # Check for critical errors
    if effective_wattage < estimated_draw:
        result.add_error(
            ErrorType.INSUFFICIENT_PSU,
            f"PSU wattage insufficient: {estimated_draw}W draw exceeds "
            f"{effective_wattage}W effective capacity (accounting for {build.psu.efficiency} efficiency)",
            component="psu",
            details={
                "estimated_draw_w": estimated_draw,
                "psu_rated_wattage": psu_wattage,
                "psu_effective_wattage": effective_wattage,
                "shortfall_w": estimated_draw - effective_wattage,
            }
        )
        return result
    
    # Check for insufficient headroom (error)
    if effective_headroom < CRITICAL_PSU_HEADROOM:
        result.add_error(
            ErrorType.INSUFFICIENT_PSU,
            f"PSU headroom critically low: {effective_headroom*100:.1f}% "
            f"(minimum {CRITICAL_PSU_HEADROOM*100:.0f}% required)",
            component="psu",
            details={
                "estimated_draw_w": estimated_draw,
                "effective_wattage": effective_wattage,
                "headroom_pct": round(effective_headroom * 100, 1),
                "minimum_required_pct": CRITICAL_PSU_HEADROOM * 100,
            }
        )
        return result
    
    # Check for low headroom (warning)
    if effective_headroom < MINIMUM_PSU_HEADROOM:
        result.add_warning(
            WarningType.LOW_PSU_HEADROOM,
            f"PSU headroom low: {effective_headroom*100:.1f}% "
            f"(recommended {RECOMMENDED_PSU_HEADROOM*100:.0f}%)",
            severity="high",
            component="psu",
            details={
                "estimated_draw_w": estimated_draw,
                "effective_wattage": effective_wattage,
                "headroom_pct": round(effective_headroom * 100, 1),
                "recommended_pct": RECOMMENDED_PSU_HEADROOM * 100,
            }
        )
    elif effective_headroom < RECOMMENDED_PSU_HEADROOM:
        result.add_warning(
            WarningType.LOW_PSU_HEADROOM,
            f"PSU headroom below recommended: {effective_headroom*100:.1f}% "
            f"(recommended {RECOMMENDED_PSU_HEADROOM*100:.0f}%)",
            severity="medium",
            component="psu",
            details={
                "estimated_draw_w": estimated_draw,
                "effective_wattage": effective_wattage,
                "headroom_pct": round(effective_headroom * 100, 1),
                "recommended_pct": RECOMMENDED_PSU_HEADROOM * 100,
            }
        )
    
    # Check efficiency rating
    if build.psu.efficiency in ["80+", "80+ Bronze"] and estimated_draw > 400:
        result.add_warning(
            WarningType.EFFICIENCY_SUBOPTIMAL,
            f"PSU efficiency ({build.psu.efficiency}) is suboptimal for {estimated_draw}W system. "
            f"Consider 80+ Gold or higher for better efficiency and lower heat/noise.",
            severity="low",
            component="psu",
            details={
                "current_efficiency": build.psu.efficiency,
                "estimated_draw_w": estimated_draw,
            }
        )
    
    return result


def validate_power_connectors(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate that PSU has required power connectors for GPU.
    
    Adds errors if connectors are missing or insufficient.
    """
    if not build.gpu or not build.gpu.power_connectors:
        return result  # No GPU or no connector requirements
    
    # Parse GPU power connector requirements
    # Example formats: "1x 8-pin", "2x 8-pin", "1x 12VHPWR", "8-pin + 6-pin"
    gpu_connectors = build.gpu.power_connectors.lower()
    
    # PSU connector inventory
    if not build.psu.pcie_connectors:
        # If PSU doesn't specify connectors, add a warning for high-power GPUs
        if build.gpu.tdp_w > 150:
            result.add_warning(
                WarningType.CLEARANCE_MINIMAL,
                f"PSU power connectors not specified. GPU requires: {build.gpu.power_connectors}",
                severity="medium",
                component="psu+gpu",
                details={
                    "gpu_tdp_w": build.gpu.tdp_w,
                    "gpu_connectors_required": build.gpu.power_connectors,
                }
            )
        return result
    
    # Simple validation: check for 12VHPWR specifically (newer GPUs)
    if "12vhpwr" in gpu_connectors or "12v-2x6" in gpu_connectors:
        if "12VHPWR" not in build.psu.pcie_connectors and "12V-2x6" not in build.psu.pcie_connectors:
            result.add_error(
                ErrorType.MISSING_POWER_CONNECTORS,
                f"GPU requires 12VHPWR connector but PSU does not provide it",
                component="psu+gpu",
                details={
                    "gpu_connectors_required": build.gpu.power_connectors,
                    "psu_connectors_available": build.psu.pcie_connectors,
                }
            )
    
    return result
