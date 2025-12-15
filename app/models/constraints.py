"""
User constraint models for PC build requirements.

This schema represents normalized user intent after natural language processing.
Person A's interpreter converts unstructured input into this format.
Person B's validator and Person A's planner both consume this.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


class PeripheralPreferences(BaseModel):
    """Optional peripheral requirements"""
    monitor: bool = False
    keyboard: bool = False
    mouse: bool = False
    audio: bool = False
    headphones: bool = False


class Constraints(BaseModel):
    """
    Normalized user constraints for PC build generation.
    
    All ambiguous/qualitative inputs should be resolved to concrete values.
    """
    # Budget
    budget_usd: float = Field(gt=0, description="Total budget in USD")
    budget_flexibility_pct: Optional[float] = Field(
        default=5.0, 
        ge=0, 
        le=20,
        description="Allowable budget overage percentage"
    )
    
    # Workloads (normalized weights)
    primary_workloads: List[str] = Field(
        description="e.g., ['gaming', 'ml', 'productivity', 'content_creation']"
    )
    workload_weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional explicit weights for each workload"
    )
    
    # Component priorities
    gpu_priority: str = Field(
        default="medium",
        description="Importance level: 'low', 'medium', 'high', 'critical'"
    )
    cpu_priority: str = Field(
        default="medium",
        description="Importance level: 'low', 'medium', 'high', 'critical'"
    )
    
    # Component requirements
    ram_min_gb: int = Field(ge=8, default=16, description="Minimum RAM in GB")
    storage_min_tb: float = Field(ge=0.25, default=1.0, description="Minimum storage in TB")
    storage_type_preference: Optional[str] = Field(
        default="nvme",
        description="'nvme', 'ssd', 'hdd', or None for planner choice"
    )
    
    # Form factor & physical
    form_factor: str = Field(
        default="mid-tower",
        description="'mini-itx', 'micro-atx', 'mid-tower', 'full-tower'"
    )
    color_preference: Optional[str] = Field(
        default=None,
        description="Case/component color preference if specified"
    )
    
    # Thermals & acoustics
    noise_tolerance: str = Field(
        default="medium",
        description="'low' (quiet), 'medium', 'high' (performance priority)"
    )
    cooling_preference: Optional[str] = Field(
        default=None,
        description="'air', 'aio', 'custom', or None for planner choice"
    )
    
    # Future-proofing
    upgrade_horizon_years: int = Field(
        ge=1, 
        le=5, 
        default=3,
        description="How long until next upgrade cycle"
    )
    
    # Peripherals
    peripherals: PeripheralPreferences = Field(
        default_factory=PeripheralPreferences,
        description="Peripheral inclusion preferences"
    )
    
    # Additional constraints
    brand_preferences: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="e.g., {'gpu': ['nvidia', 'amd'], 'cpu': ['amd']}"
    )
    exclude_brands: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Brands to avoid per component type"
    )
    
    @field_validator('gpu_priority', 'cpu_priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Ensure priority is valid"""
        valid = ['low', 'medium', 'high', 'critical']
        if v.lower() not in valid:
            raise ValueError(f"Priority must be one of {valid}")
        return v.lower()
    
    @field_validator('noise_tolerance')
    @classmethod
    def validate_noise(cls, v: str) -> str:
        """Ensure noise tolerance is valid"""
        valid = ['low', 'medium', 'high']
        if v.lower() not in valid:
            raise ValueError(f"Noise tolerance must be one of {valid}")
        return v.lower()
    
    @field_validator('form_factor')
    @classmethod
    def validate_form_factor(cls, v: str) -> str:
        """Ensure form factor is valid"""
        valid = ['mini-itx', 'micro-atx', 'mid-tower', 'full-tower']
        if v.lower() not in valid:
            raise ValueError(f"Form factor must be one of {valid}")
        return v.lower()
