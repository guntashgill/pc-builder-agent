from pydantic import BaseModel, Field
from typing import Optional


class CPU(BaseModel):
    model: str = Field(..., description="CPU model name")
    socket: str = Field(..., description="Socket type")
    tdp_w: int = Field(..., description="Thermal Design Power in watts")


class GPU(BaseModel):
    model: str = Field(..., description="GPU model name")
    vram_gb: int = Field(..., description="VRAM capacity in GB")
    tdp_w: int = Field(..., description="Power consumption in watts")


class RAM(BaseModel):
    capacity_gb: int = Field(..., description="Total RAM capacity in GB")
    type: str = Field(..., description="RAM type (DDR4/DDR5)")
    speed_mhz: Optional[int] = Field(None, description="RAM speed in MHz")


class Storage(BaseModel):
    type: str = Field(..., description="Storage type (NVMe SSD, SATA SSD)")
    capacity_tb: float = Field(..., description="Storage capacity in TB")


class Motherboard(BaseModel):
    model: str = Field(..., description="Motherboard model name")
    socket: str = Field(..., description="CPU socket type")
    ram_type: str = Field(..., description="Supported RAM type (DDR4/DDR5)")
    form_factor: str = Field(..., description="Form factor (ATX, Micro-ATX, Mini-ITX)")


class Chassis(BaseModel):
    model: str = Field(..., description="Case model name")
    form_factor: str = Field(..., description="Form factor (mid-tower, full-tower, etc.)")


class PSU(BaseModel):
    wattage: int = Field(..., description="PSU wattage")
    efficiency: str = Field(..., description="Efficiency rating (Bronze, Gold, Platinum, etc.)")


class Cooling(BaseModel):
    type: str = Field(..., description="Cooling type (Air, AIO, Custom Loop)")
    model: Optional[str] = Field(None, description="Specific cooler model if applicable")


class Build(BaseModel):
    cpu: CPU
    gpu: GPU
    motherboard: Motherboard
    ram: RAM
    storage: Storage
    chassis: Chassis
    psu: PSU
    cooling: Cooling
    estimated_cost_usd: int = Field(..., description="Estimated total cost in USD")
    rationale: Optional[str] = Field(None, description="Brief explanation of key component choices")
