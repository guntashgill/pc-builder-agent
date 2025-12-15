"""
Unit tests for PC build validation logic.

Tests all validation rules for compatibility and power estimation.
"""
import pytest
from app.models.build import (
    PCBuild, CPUSpec, GPUSpec, RAMSpec, StorageSpec,
    MotherboardSpec, PSUSpec, CoolingSpec, ChassisSpec
)
from app.models.validation import ErrorType, WarningType
from app.validation import validate_build


def create_valid_build() -> PCBuild:
    """Create a valid baseline build for testing"""
    return PCBuild(
        cpu=CPUSpec(
            model="Ryzen 5 7600",
            brand="amd",
            socket="AM5",
            cores=6,
            threads=12,
            base_clock_ghz=3.8,
            boost_clock_ghz=5.1,
            tdp_w=65,
            integrated_graphics=True,
            price_usd=229.99
        ),
        motherboard=MotherboardSpec(
            model="MSI B650 TOMAHAWK",
            chipset="B650",
            socket="AM5",
            form_factor="ATX",
            ram_type="DDR5",
            ram_slots=4,
            max_ram_gb=128,
            m2_slots=2,
            sata_ports=4,
            pcie_slots={"x16": 2, "x4": 1, "x1": 2},
            price_usd=199.99
        ),
        ram=RAMSpec(
            capacity_gb=32,
            type="DDR5",
            speed_mhz=6000,
            modules=2,
            cas_latency=30,
            price_usd=99.99
        ),
        storage=[
            StorageSpec(
                type="nvme",
                capacity_tb=1.0,
                interface="PCIe 4.0 x4",
                read_speed_mbps=7000,
                write_speed_mbps=5000,
                form_factor="M.2 2280",
                price_usd=89.99
            )
        ],
        psu=PSUSpec(
            model="Corsair RM750e",
            wattage=750,
            efficiency="80+ Gold",
            modular="full",
            form_factor="ATX",
            pcie_connectors={"8-pin": 4, "6-pin": 2},
            price_usd=109.99
        ),
        cooling=CoolingSpec(
            type="air",
            model="Thermalright Peerless Assassin 120",
            tdp_rating_w=220,
            height_mm=155,
            fan_count=2,
            noise_level_db=25.0,
            price_usd=39.99
        ),
        chassis=ChassisSpec(
            model="Fractal Design Meshify 2",
            form_factor="Mid-Tower",
            motherboard_support=["Mini-ITX", "Micro-ATX", "ATX"],
            max_gpu_length_mm=315,
            max_cpu_cooler_height_mm=185,
            radiator_support=[240, 280, 360],
            included_fans=3,
            color="Black",
            price_usd=139.99
        ),
        estimated_cost_usd=909.93
    )


class TestValidBuild:
    """Test that valid builds pass validation"""
    
    def test_valid_build_passes(self):
        """A properly configured build should pass all validation"""
        build = create_valid_build()
        result = validate_build(build)
        
        assert result.is_valid
        assert len(result.errors) == 0
        print(f"\n✓ Valid build: {result.summary()}")
        if result.warnings:
            print(f"  Warnings: {len(result.warnings)}")
            for warning in result.warnings:
                print(f"    - {warning.message}")


class TestSocketCompatibility:
    """Test CPU/motherboard socket validation"""
    
    def test_socket_mismatch_error(self):
        """Mismatched CPU and motherboard sockets should error"""
        build = create_valid_build()
        
        # Change CPU to Intel with LGA1700 socket
        build.cpu.socket = "LGA1700"
        build.cpu.model = "Intel Core i5-13600K"
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any(e.type == ErrorType.SOCKET_MISMATCH.value for e in result.errors)
        print(f"\n✓ Detected socket mismatch: {result.errors[0].message}")
    
    def test_matching_sockets_pass(self):
        """Matching sockets should pass"""
        build = create_valid_build()
        
        # Ensure sockets match
        build.cpu.socket = "AM5"
        build.motherboard.socket = "AM5"
        
        result = validate_build(build)
        
        # Should not have socket mismatch error
        assert not any(e.type == ErrorType.SOCKET_MISMATCH.value for e in result.errors)
        print(f"\n✓ Matching sockets validated")


class TestRAMCompatibility:
    """Test RAM validation"""
    
    def test_ram_type_mismatch_error(self):
        """DDR4 RAM with DDR5 motherboard should error"""
        build = create_valid_build()
        
        build.ram.type = "DDR4"
        # Motherboard expects DDR5
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.RAM_TYPE_MISMATCH.value for e in result.errors)
        print(f"\n✓ Detected RAM type mismatch")
    
    def test_ram_exceeds_max_capacity(self):
        """RAM exceeding motherboard max should error"""
        build = create_valid_build()
        
        build.ram.capacity_gb = 256  # Exceeds 128GB max
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.INSUFFICIENT_RAM_SLOTS.value for e in result.errors)
        print(f"\n✓ Detected RAM capacity exceeded")
    
    def test_too_many_ram_modules(self):
        """More modules than slots should error"""
        build = create_valid_build()
        
        build.ram.modules = 8  # Motherboard has only 4 slots
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.INSUFFICIENT_RAM_SLOTS.value for e in result.errors)
        print(f"\n✓ Detected insufficient RAM slots")


class TestPowerValidation:
    """Test PSU wattage and power validation"""
    
    def test_insufficient_psu_wattage(self):
        """PSU too small for system load should error"""
        build = create_valid_build()
        
        # Add high-power GPU
        build.gpu = GPUSpec(
            model="RTX 4090",
            brand="nvidia",
            chipset="AD102",
            vram_gb=24,
            vram_type="GDDR6X",
            tdp_w=450,
            length_mm=304,
            pcie_slots=3,
            power_connectors="1x 12VHPWR",
            price_usd=1599.99
        )
        
        # Use tiny PSU
        build.psu.wattage = 450
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.INSUFFICIENT_PSU.value for e in result.errors)
        print(f"\n✓ Detected insufficient PSU wattage")
        print(f"  {result.errors[0].message}")
    
    def test_adequate_psu_wattage(self):
        """Properly sized PSU should pass"""
        build = create_valid_build()
        
        # Add moderate GPU
        build.gpu = GPUSpec(
            model="RTX 4060 Ti",
            brand="nvidia",
            chipset="AD106",
            vram_gb=16,
            vram_type="GDDR6",
            tdp_w=160,
            length_mm=244,
            pcie_slots=2,
            power_connectors="1x 8-pin",
            price_usd=499.99
        )
        
        # 750W PSU is plenty
        build.psu.wattage = 750
        
        result = validate_build(build)
        
        # Should not have PSU errors
        assert not any(e.type == ErrorType.INSUFFICIENT_PSU.value for e in result.errors)
        
        # Check computed metrics
        assert result.computed_metrics is not None
        assert "estimated_power_draw_w" in result.computed_metrics
        assert "psu_headroom_pct" in result.computed_metrics
        
        print(f"\n✓ PSU adequate for build")
        print(f"  Power draw: {result.computed_metrics['estimated_power_draw_w']}W")
        print(f"  Headroom: {result.computed_metrics['psu_headroom_pct']}%")


class TestFormFactorCompatibility:
    """Test chassis and component form factor compatibility"""
    
    def test_motherboard_too_large_for_case(self):
        """E-ATX motherboard in Mini-ITX case should error"""
        build = create_valid_build()
        
        build.motherboard.form_factor = "E-ATX"
        build.chassis.motherboard_support = ["Mini-ITX"]
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.FORM_FACTOR_INCOMPATIBLE.value for e in result.errors)
        print(f"\n✓ Detected form factor incompatibility")
    
    def test_gpu_too_long_for_case(self):
        """GPU longer than case clearance should error"""
        build = create_valid_build()
        
        build.gpu = GPUSpec(
            model="RTX 4090",
            brand="nvidia",
            chipset="AD102",
            vram_gb=24,
            vram_type="GDDR6X",
            tdp_w=450,
            length_mm=360,  # Very long
            pcie_slots=3,
            price_usd=1599.99
        )
        
        build.chassis.max_gpu_length_mm = 315  # Too short
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.GPU_TOO_LONG.value for e in result.errors)
        print(f"\n✓ Detected GPU too long for case")
    
    def test_cpu_cooler_too_tall(self):
        """CPU cooler taller than case clearance should error"""
        build = create_valid_build()
        
        build.cooling.height_mm = 190
        build.chassis.max_cpu_cooler_height_mm = 165
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.COOLER_TOO_TALL.value for e in result.errors)
        print(f"\n✓ Detected cooler too tall for case")


class TestCoolingValidation:
    """Test cooling capacity validation"""
    
    def test_insufficient_cooling_for_cpu(self):
        """Cooler rated below CPU TDP should error"""
        build = create_valid_build()
        
        # High-power CPU
        build.cpu.tdp_w = 170
        
        # Weak cooler
        build.cooling.tdp_rating_w = 120
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.COOLING_INSUFFICIENT.value for e in result.errors)
        print(f"\n✓ Detected insufficient cooling")
    
    def test_adequate_cooling(self):
        """Properly rated cooler should pass"""
        build = create_valid_build()
        
        build.cpu.tdp_w = 65
        build.cooling.tdp_rating_w = 220  # Plenty of headroom
        
        result = validate_build(build)
        
        assert not any(e.type == ErrorType.COOLING_INSUFFICIENT.value for e in result.errors)
        print(f"\n✓ Cooling adequate")


class TestStorageValidation:
    """Test storage connectivity validation"""
    
    def test_insufficient_m2_slots(self):
        """More NVMe drives than M.2 slots should error"""
        build = create_valid_build()
        
        # Add 3 NVMe drives
        build.storage = [
            StorageSpec(type="nvme", capacity_tb=1.0, interface="M.2", price_usd=89.99),
            StorageSpec(type="nvme", capacity_tb=1.0, interface="M.2", price_usd=89.99),
            StorageSpec(type="nvme", capacity_tb=1.0, interface="M.2", price_usd=89.99),
        ]
        
        # Motherboard has only 2 M.2 slots
        build.motherboard.m2_slots = 2
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.INSUFFICIENT_M2_SLOTS.value for e in result.errors)
        print(f"\n✓ Detected insufficient M.2 slots")
    
    def test_insufficient_sata_ports(self):
        """More SATA drives than ports should error"""
        build = create_valid_build()
        
        # Add 6 SATA drives
        build.additional_storage = [
            StorageSpec(type="ssd", capacity_tb=1.0, interface="SATA", price_usd=59.99),
            StorageSpec(type="ssd", capacity_tb=1.0, interface="SATA", price_usd=59.99),
            StorageSpec(type="ssd", capacity_tb=1.0, interface="SATA", price_usd=59.99),
            StorageSpec(type="ssd", capacity_tb=1.0, interface="SATA", price_usd=59.99),
            StorageSpec(type="hdd", capacity_tb=4.0, interface="SATA", price_usd=89.99),
        ]
        
        # Motherboard has only 4 SATA ports
        build.motherboard.sata_ports = 4
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.INSUFFICIENT_SATA_PORTS.value for e in result.errors)
        print(f"\n✓ Detected insufficient SATA ports")


class TestIntegratedGraphics:
    """Test iGPU requirement validation"""
    
    def test_no_gpu_no_igpu_error(self):
        """No discrete GPU and no iGPU should error"""
        build = create_valid_build()
        
        build.gpu = None  # No discrete GPU
        build.cpu.integrated_graphics = False  # No iGPU
        
        result = validate_build(build)
        
        assert not result.is_valid
        assert any(e.type == ErrorType.MISSING_GPU.value for e in result.errors)
        print(f"\n✓ Detected missing GPU/iGPU")
    
    def test_igpu_only_passes(self):
        """CPU with iGPU and no discrete GPU should pass"""
        build = create_valid_build()
        
        build.gpu = None
        build.cpu.integrated_graphics = True
        
        result = validate_build(build)
        
        assert not any(e.type == ErrorType.MISSING_GPU.value for e in result.errors)
        print(f"\n✓ iGPU-only build validated")


class TestWarnings:
    """Test warning generation for suboptimal configs"""
    
    def test_low_psu_headroom_warning(self):
        """PSU with minimal headroom should warn"""
        build = create_valid_build()
        
        # Add high-power GPU
        build.gpu = GPUSpec(
            model="RTX 4080",
            brand="nvidia",
            chipset="AD103",
            vram_gb=16,
            vram_type="GDDR6X",
            tdp_w=320,
            length_mm=304,
            pcie_slots=3,
            price_usd=1199.99
        )
        
        # Use PSU that gives 20-25% headroom (below recommended 30%)
        build.psu.wattage = 650
        
        result = validate_build(build)
        
        # Should pass but with warning
        assert result.is_valid
        assert any(w.type == WarningType.LOW_PSU_HEADROOM.value for w in result.warnings)
        print(f"\n✓ Generated low PSU headroom warning")
        print(f"  Power: {result.computed_metrics['estimated_power_draw_w']}W, "
              f"Headroom: {result.computed_metrics['effective_headroom_pct']}%")
    
    def test_tight_gpu_clearance_warning(self):
        """GPU with minimal clearance should warn"""
        build = create_valid_build()
        
        build.gpu = GPUSpec(
            model="RTX 4060",
            brand="nvidia",
            chipset="AD107",
            vram_gb=8,
            vram_type="GDDR6",
            tdp_w=115,
            length_mm=312,  # Just barely fits
            pcie_slots=2,
            price_usd=299.99
        )
        
        build.chassis.max_gpu_length_mm = 315  # Only 3mm clearance
        
        result = validate_build(build)
        
        assert result.is_valid
        assert any(w.type == WarningType.TIGHT_FIT.value for w in result.warnings)
        print(f"\n✓ Generated tight fit warning")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
