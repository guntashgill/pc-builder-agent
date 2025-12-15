"""
Hardware compatibility validation logic.

Validates socket compatibility, RAM type, form factors, physical clearances, etc.
"""
from typing import Optional, List
from app.models.build import PCBuild
from app.models.validation import ValidationResult, ErrorType, WarningType


def validate_cpu_motherboard_socket(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate CPU socket matches motherboard socket.
    
    This is a hard constraint - mismatched sockets are incompatible.
    """
    cpu_socket = build.cpu.socket.upper()
    mb_socket = build.motherboard.socket.upper()
    
    if cpu_socket != mb_socket:
        result.add_error(
            ErrorType.SOCKET_MISMATCH,
            f"CPU socket '{build.cpu.socket}' does not match "
            f"motherboard socket '{build.motherboard.socket}'",
            component="cpu+motherboard",
            details={
                "cpu_socket": build.cpu.socket,
                "cpu_model": build.cpu.model,
                "motherboard_socket": build.motherboard.socket,
                "motherboard_model": build.motherboard.model,
            }
        )
    
    return result


def validate_ram_compatibility(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate RAM type matches motherboard and capacity is within limits.
    """
    ram_type = build.ram.type.upper()
    mb_ram_type = build.motherboard.ram_type.upper()
    
    # Check RAM type compatibility
    if ram_type != mb_ram_type:
        result.add_error(
            ErrorType.RAM_TYPE_MISMATCH,
            f"RAM type '{build.ram.type}' incompatible with "
            f"motherboard RAM type '{build.motherboard.ram_type}'",
            component="ram+motherboard",
            details={
                "ram_type": build.ram.type,
                "ram_capacity_gb": build.ram.capacity_gb,
                "motherboard_ram_type": build.motherboard.ram_type,
                "motherboard_model": build.motherboard.model,
            }
        )
    
    # Check RAM capacity doesn't exceed motherboard max
    if build.ram.capacity_gb > build.motherboard.max_ram_gb:
        result.add_error(
            ErrorType.INSUFFICIENT_RAM_SLOTS,
            f"RAM capacity {build.ram.capacity_gb}GB exceeds "
            f"motherboard maximum {build.motherboard.max_ram_gb}GB",
            component="ram+motherboard",
            details={
                "ram_capacity_gb": build.ram.capacity_gb,
                "motherboard_max_gb": build.motherboard.max_ram_gb,
            }
        )
    
    # Check number of modules fits in slots
    if build.ram.modules > build.motherboard.ram_slots:
        result.add_error(
            ErrorType.INSUFFICIENT_RAM_SLOTS,
            f"RAM configuration requires {build.ram.modules} slots but "
            f"motherboard only has {build.motherboard.ram_slots}",
            component="ram+motherboard",
            details={
                "ram_modules": build.ram.modules,
                "motherboard_slots": build.motherboard.ram_slots,
            }
        )
    
    # Warning: not using all slots (upgrade path consideration)
    if build.ram.modules == build.motherboard.ram_slots:
        result.add_warning(
            WarningType.NO_SPARE_SLOTS,
            f"All {build.motherboard.ram_slots} RAM slots used - no upgrade path without replacement",
            severity="low",
            component="ram+motherboard",
            details={
                "ram_modules": build.ram.modules,
                "motherboard_slots": build.motherboard.ram_slots,
            }
        )
    
    # Warning: RAM speed might be limited by CPU/motherboard
    if build.ram.speed_mhz > 4000 and mb_ram_type == "DDR4":
        result.add_warning(
            WarningType.RAM_SPEED_MISMATCH,
            f"RAM speed {build.ram.speed_mhz}MHz is quite high for DDR4. "
            f"Verify motherboard/CPU officially supports this speed.",
            severity="low",
            component="ram",
            details={"ram_speed_mhz": build.ram.speed_mhz}
        )
    
    return result


def validate_motherboard_form_factor(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate motherboard fits in the chassis.
    """
    mb_form_factor = build.motherboard.form_factor.upper()
    
    # Normalize chassis motherboard support list
    case_supports = [ff.upper() for ff in build.chassis.motherboard_support]
    
    # Check if motherboard form factor is supported
    if mb_form_factor not in case_supports:
        result.add_error(
            ErrorType.FORM_FACTOR_INCOMPATIBLE,
            f"Motherboard form factor '{build.motherboard.form_factor}' not supported by chassis. "
            f"Chassis supports: {', '.join(build.chassis.motherboard_support)}",
            component="motherboard+chassis",
            details={
                "motherboard_form_factor": build.motherboard.form_factor,
                "chassis_supports": build.chassis.motherboard_support,
                "chassis_model": build.chassis.model,
            }
        )
    
    return result


def validate_gpu_clearance(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate GPU fits in chassis.
    """
    if not build.gpu:
        return result  # No GPU to validate
    
    # Check GPU length
    if build.gpu.length_mm and build.chassis.max_gpu_length_mm:
        clearance_mm = build.chassis.max_gpu_length_mm - build.gpu.length_mm
        
        if clearance_mm < 0:
            result.add_error(
                ErrorType.GPU_TOO_LONG,
                f"GPU length {build.gpu.length_mm}mm exceeds chassis maximum "
                f"{build.chassis.max_gpu_length_mm}mm",
                component="gpu+chassis",
                details={
                    "gpu_length_mm": build.gpu.length_mm,
                    "chassis_max_mm": build.chassis.max_gpu_length_mm,
                    "overhang_mm": abs(clearance_mm),
                }
            )
        elif clearance_mm < 10:
            result.add_warning(
                WarningType.TIGHT_FIT,
                f"GPU clearance very tight: only {clearance_mm}mm available",
                severity="medium",
                component="gpu+chassis",
                details={
                    "gpu_length_mm": build.gpu.length_mm,
                    "chassis_max_mm": build.chassis.max_gpu_length_mm,
                    "clearance_mm": clearance_mm,
                }
            )
    
    # Check PCIe slots
    required_slots = build.gpu.pcie_slots
    # Note: We'd need motherboard PCIe slot info to validate this properly
    # For now, just warn if GPU uses 3+ slots
    if required_slots >= 3:
        result.add_warning(
            WarningType.NO_SPARE_SLOTS,
            f"GPU occupies {required_slots} PCIe slots - may limit expansion options",
            severity="low",
            component="gpu",
            details={"gpu_pcie_slots": required_slots}
        )
    
    return result


def validate_cpu_cooler_clearance(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate CPU cooler fits in chassis and can handle CPU TDP.
    """
    # Check cooler height clearance (for air coolers)
    if build.cooling.type == "air" and build.cooling.height_mm and build.chassis.max_cpu_cooler_height_mm:
        clearance_mm = build.chassis.max_cpu_cooler_height_mm - build.cooling.height_mm
        
        if clearance_mm < 0:
            result.add_error(
                ErrorType.COOLER_TOO_TALL,
                f"CPU cooler height {build.cooling.height_mm}mm exceeds chassis maximum "
                f"{build.chassis.max_cpu_cooler_height_mm}mm",
                component="cooling+chassis",
                details={
                    "cooler_height_mm": build.cooling.height_mm,
                    "chassis_max_mm": build.chassis.max_cpu_cooler_height_mm,
                    "overhang_mm": abs(clearance_mm),
                }
            )
        elif clearance_mm < 5:
            result.add_warning(
                WarningType.TIGHT_FIT,
                f"CPU cooler clearance very tight: only {clearance_mm}mm available",
                severity="medium",
                component="cooling+chassis",
                details={
                    "cooler_height_mm": build.cooling.height_mm,
                    "chassis_max_mm": build.chassis.max_cpu_cooler_height_mm,
                    "clearance_mm": clearance_mm,
                }
            )
    
    # Check radiator support (for AIOs)
    if build.cooling.type == "aio" and build.cooling.radiator_size_mm:
        if build.chassis.radiator_support:
            if build.cooling.radiator_size_mm not in build.chassis.radiator_support:
                result.add_error(
                    ErrorType.RADIATOR_NOT_SUPPORTED,
                    f"Chassis does not support {build.cooling.radiator_size_mm}mm radiator. "
                    f"Supported sizes: {build.chassis.radiator_support}",
                    component="cooling+chassis",
                    details={
                        "radiator_size_mm": build.cooling.radiator_size_mm,
                        "chassis_supports": build.chassis.radiator_support,
                    }
                )
        else:
            # Chassis doesn't specify radiator support - add warning
            result.add_warning(
                WarningType.CLEARANCE_MINIMAL,
                f"Chassis radiator support not specified. Verify {build.cooling.radiator_size_mm}mm "
                f"radiator fitment manually.",
                severity="high",
                component="cooling+chassis",
                details={"radiator_size_mm": build.cooling.radiator_size_mm}
            )
    
    return result


def validate_cooling_capacity(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate CPU cooler can handle CPU TDP.
    """
    cpu_tdp = build.cpu.tdp_w
    cooler_rating = build.cooling.tdp_rating_w
    
    # Check if cooler is rated for CPU TDP
    if cooler_rating < cpu_tdp:
        result.add_error(
            ErrorType.COOLING_INSUFFICIENT,
            f"CPU cooler TDP rating {cooler_rating}W insufficient for "
            f"CPU TDP {cpu_tdp}W",
            component="cooling+cpu",
            details={
                "cpu_tdp_w": cpu_tdp,
                "cooler_rating_w": cooler_rating,
                "shortfall_w": cpu_tdp - cooler_rating,
            }
        )
    elif cooler_rating < cpu_tdp * 1.2:
        # Less than 20% headroom
        result.add_warning(
            WarningType.THERMAL_RISK,
            f"CPU cooler TDP rating {cooler_rating}W provides minimal headroom for "
            f"CPU TDP {cpu_tdp}W. May run hot under sustained load.",
            severity="high",
            component="cooling+cpu",
            details={
                "cpu_tdp_w": cpu_tdp,
                "cooler_rating_w": cooler_rating,
                "headroom_pct": round(((cooler_rating - cpu_tdp) / cpu_tdp) * 100, 1),
            }
        )
    
    return result


def validate_storage_connectivity(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate motherboard has sufficient M.2 and SATA ports for storage.
    """
    # Count required M.2 slots
    m2_count = sum(1 for s in build.storage if s.type == "nvme")
    if build.additional_storage:
        m2_count += sum(1 for s in build.additional_storage if s.type == "nvme")
    
    # Count required SATA ports
    sata_count = sum(1 for s in build.storage if s.type in ["ssd", "hdd"])
    if build.additional_storage:
        sata_count += sum(1 for s in build.additional_storage if s.type in ["ssd", "hdd"])
    
    # Validate M.2 slots
    if m2_count > build.motherboard.m2_slots:
        result.add_error(
            ErrorType.INSUFFICIENT_M2_SLOTS,
            f"Storage requires {m2_count} M.2 slots but motherboard only has "
            f"{build.motherboard.m2_slots}",
            component="storage+motherboard",
            details={
                "m2_required": m2_count,
                "m2_available": build.motherboard.m2_slots,
            }
        )
    elif m2_count == build.motherboard.m2_slots and m2_count > 0:
        result.add_warning(
            WarningType.NO_SPARE_SLOTS,
            f"All {build.motherboard.m2_slots} M.2 slots used - no room for expansion",
            severity="low",
            component="storage+motherboard",
            details={
                "m2_required": m2_count,
                "m2_available": build.motherboard.m2_slots,
            }
        )
    
    # Validate SATA ports
    if sata_count > build.motherboard.sata_ports:
        result.add_error(
            ErrorType.INSUFFICIENT_SATA_PORTS,
            f"Storage requires {sata_count} SATA ports but motherboard only has "
            f"{build.motherboard.sata_ports}",
            component="storage+motherboard",
            details={
                "sata_required": sata_count,
                "sata_available": build.motherboard.sata_ports,
            }
        )
    
    return result


def validate_integrated_graphics(
    build: PCBuild,
    result: ValidationResult
) -> ValidationResult:
    """
    Validate that if there's no discrete GPU, CPU has integrated graphics.
    """
    if not build.gpu and not build.cpu.integrated_graphics:
        result.add_error(
            ErrorType.MISSING_GPU,
            f"No discrete GPU specified and CPU '{build.cpu.model}' lacks integrated graphics. "
            f"System will have no video output.",
            component="cpu+gpu",
            details={
                "cpu_model": build.cpu.model,
                "cpu_has_igpu": build.cpu.integrated_graphics,
            }
        )
    
    return result
