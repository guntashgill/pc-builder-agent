from pydantic import BaseModel, Field
from typing import List, Literal


class PeripheralRequirements(BaseModel):
    monitor: bool = False
    audio: bool = False


class Constraints(BaseModel):
    """Normalized user requirements extracted from natural language input"""
    
    budget_usd: int = Field(..., description="Maximum budget in USD")
    primary_workloads: List[str] = Field(
        ..., 
        description="List of primary use cases (e.g., gaming, ml, video_editing, office)"
    )
    
    # Priority levels: low, medium, high
    gpu_priority: Literal["low", "medium", "high"] = "medium"
    cpu_priority: Literal["low", "medium", "high"] = "medium"
    
    ram_min_gb: int = Field(16, description="Minimum RAM in GB")
    storage_min_tb: float = Field(1.0, description="Minimum storage in TB")
    
    form_factor: Literal["mini-itx", "micro-atx", "mid-tower", "full-tower"] = "mid-tower"
    noise_tolerance: Literal["low", "medium", "high"] = "medium"
    upgrade_horizon_years: int = Field(3, description="Expected time before next upgrade")
    
    peripherals: PeripheralRequirements = Field(default_factory=PeripheralRequirements)