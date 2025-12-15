"""
PC build specification models.

Person A's planner generates this structure.
Person B's validator consumes and validates it.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CPUSpec(BaseModel):
    """CPU component specification"""
    model: str = Field(description="e.g., 'Ryzen 5 7600', 'Intel Core i5-13600K'")
    brand: str = Field(description="'amd' or 'intel'")
    socket: str = Field(description="e.g., 'AM5', 'LGA1700'")
    cores: int = Field(ge=2, description="Number of cores")
    threads: int = Field(ge=2, description="Number of threads")
    base_clock_ghz: float = Field(gt=0, description="Base clock speed in GHz")
    boost_clock_ghz: Optional[float] = Field(default=None, description="Boost clock in GHz")
    tdp_w: int = Field(gt=0, description="Thermal design power in watts")
    integrated_graphics: bool = Field(default=False, description="Has iGPU")
    price_usd: float = Field(ge=0)


class GPUSpec(BaseModel):
    """GPU component specification"""
    model: str = Field(description="e.g., 'RTX 4060 Ti', 'RX 7800 XT'")
    brand: str = Field(description="'nvidia' or 'amd'")
    chipset: str = Field(description="e.g., 'AD106', 'Navi 32'")
    vram_gb: int = Field(gt=0, description="Video memory in GB")
    vram_type: str = Field(description="e.g., 'GDDR6', 'GDDR6X'")
    tdp_w: int = Field(gt=0, description="Power consumption in watts")
    length_mm: Optional[int] = Field(default=None, description="Card length for case clearance")
    pcie_slots: int = Field(ge=1, le=4, default=2, description="Number of PCIe slots occupied")
    power_connectors: Optional[str] = Field(
        default=None, 
        description="e.g., '1x 8-pin', '2x 8-pin', '1x 12VHPWR'"
    )
    price_usd: float = Field(ge=0)


class RAMSpec(BaseModel):
    """Memory specification"""
    capacity_gb: int = Field(gt=0, description="Total RAM capacity in GB")
    type: str = Field(description="'DDR4' or 'DDR5'")
    speed_mhz: int = Field(gt=0, description="RAM speed in MHz")
    modules: int = Field(ge=1, le=4, default=2, description="Number of modules (e.g., 2x16GB)")
    cas_latency: Optional[int] = Field(default=None, description="CAS latency")
    price_usd: float = Field(ge=0)


class StorageSpec(BaseModel):
    """Storage specification"""
    type: str = Field(description="'nvme', 'ssd', or 'hdd'")
    capacity_tb: float = Field(gt=0, description="Capacity in TB")
    interface: str = Field(description="e.g., 'M.2 NVMe', 'SATA', 'PCIe 4.0 x4'")
    read_speed_mbps: Optional[int] = Field(default=None, description="Sequential read MB/s")
    write_speed_mbps: Optional[int] = Field(default=None, description="Sequential write MB/s")
    form_factor: Optional[str] = Field(default=None, description="e.g., 'M.2 2280', '2.5\"'")
    price_usd: float = Field(ge=0)


class MotherboardSpec(BaseModel):
    """Motherboard specification"""
    model: str
    chipset: str = Field(description="e.g., 'B650', 'Z790'")
    socket: str = Field(description="Must match CPU socket")
    form_factor: str = Field(description="'Mini-ITX', 'Micro-ATX', 'ATX', 'E-ATX'")
    ram_type: str = Field(description="'DDR4' or 'DDR5'")
    ram_slots: int = Field(ge=2, le=8, description="Number of RAM slots")
    max_ram_gb: int = Field(gt=0, description="Maximum supported RAM")
    m2_slots: int = Field(ge=0, description="Number of M.2 slots")
    sata_ports: int = Field(ge=0, description="Number of SATA ports")
    pcie_slots: Dict[str, int] = Field(
        default_factory=dict,
        description="e.g., {'x16': 2, 'x4': 1, 'x1': 2}"
    )
    price_usd: float = Field(ge=0)


class PSUSpec(BaseModel):
    """Power supply specification"""
    model: str
    wattage: int = Field(gt=0, description="Power rating in watts")
    efficiency: str = Field(description="'80+ Bronze', '80+ Gold', '80+ Platinum', etc.")
    modular: str = Field(description="'full', 'semi', 'non'")
    form_factor: str = Field(default="ATX", description="e.g., 'ATX', 'SFX'")
    pcie_connectors: Optional[Dict[str, int]] = Field(
        default=None,
        description="e.g., {'8-pin': 2, '6-pin': 2}"
    )
    price_usd: float = Field(ge=0)


class CoolingSpec(BaseModel):
    """CPU cooling specification"""
    type: str = Field(description="'air', 'aio', or 'custom'")
    model: str
    tdp_rating_w: int = Field(gt=0, description="Max TDP it can handle")
    height_mm: Optional[int] = Field(default=None, description="Cooler height for case clearance")
    radiator_size_mm: Optional[int] = Field(
        default=None, 
        description="For AIOs: 120, 240, 280, 360, etc."
    )
    fan_count: int = Field(ge=1, default=1)
    noise_level_db: Optional[float] = Field(default=None, description="Noise at max RPM")
    price_usd: float = Field(ge=0)


class ChassisSpec(BaseModel):
    """Case specification"""
    model: str
    form_factor: str = Field(description="'Mini-ITX', 'Micro-ATX', 'Mid-Tower', 'Full-Tower'")
    motherboard_support: list[str] = Field(
        description="e.g., ['Mini-ITX', 'Micro-ATX', 'ATX']"
    )
    max_gpu_length_mm: Optional[int] = Field(default=None)
    max_cpu_cooler_height_mm: Optional[int] = Field(default=None)
    radiator_support: Optional[list[int]] = Field(
        default=None,
        description="Supported radiator sizes, e.g., [240, 280, 360]"
    )
    included_fans: int = Field(ge=0, default=0)
    color: Optional[str] = Field(default=None)
    price_usd: float = Field(ge=0)


class PeripheralSpec(BaseModel):
    """Optional peripheral"""
    type: str = Field(description="'monitor', 'keyboard', 'mouse', 'headphones', 'speakers'")
    model: str
    price_usd: float = Field(ge=0)
    specs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Type-specific specs (resolution, refresh rate, etc.)"
    )


class PCBuild(BaseModel):
    """
    Complete PC build specification.
    
    Generated by Person A's planner.
    Validated by Person B's validator.
    """
    cpu: CPUSpec
    gpu: Optional[GPUSpec] = Field(
        default=None, 
        description="Optional if CPU has integrated graphics"
    )
    motherboard: MotherboardSpec
    ram: RAMSpec
    storage: list[StorageSpec] = Field(min_length=1, description="At least one storage device")
    psu: PSUSpec
    cooling: CoolingSpec
    chassis: ChassisSpec
    
    # Optional components
    additional_storage: Optional[list[StorageSpec]] = Field(
        default=None,
        description="Secondary storage drives"
    )
    case_fans: Optional[int] = Field(
        default=None,
        description="Additional case fans beyond included"
    )
    peripherals: Optional[list[PeripheralSpec]] = Field(default=None)
    
    # Metadata
    estimated_cost_usd: float = Field(ge=0, description="Total estimated cost")
    estimated_tdp_w: Optional[int] = Field(
        default=None,
        description="Total estimated power draw"
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Key reasoning for component choices"
    )
    
    def calculate_total_cost(self) -> float:
        """Calculate total build cost from all components"""
        total = (
            self.cpu.price_usd +
            self.motherboard.price_usd +
            self.ram.price_usd +
            self.psu.price_usd +
            self.cooling.price_usd +
            self.chassis.price_usd +
            sum(s.price_usd for s in self.storage)
        )
        
        if self.gpu:
            total += self.gpu.price_usd
        
        if self.additional_storage:
            total += sum(s.price_usd for s in self.additional_storage)
        
        if self.peripherals:
            total += sum(p.price_usd for p in self.peripherals)
        
        return total
    
    def calculate_total_tdp(self) -> int:
        """Calculate estimated total power draw"""
        tdp = self.cpu.tdp_w
        
        if self.gpu:
            tdp += self.gpu.tdp_w
        
        # Add estimates for other components
        tdp += 10  # RAM (~10W)
        tdp += 10 * len(self.storage)  # ~10W per drive
        tdp += 5 * (self.case_fans or 0)  # ~5W per fan
        
        return tdp
