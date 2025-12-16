import logging
from typing import Optional

from app.llm.client import LLMClient
from app.models import PCBuild, Constraints

logger = logging.getLogger(__name__)


class BuildFormatter:
    """Formats PC builds into human-readable explanations"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def format_build(
        self,
        build: PCBuild,
        constraints: Constraints,
        include_technical_details: bool = True
    ) -> str:
        """Generate human-readable build explanation"""
        logger.info("Formatting build explanation")

        output = []
        output.append("="*70)
        output.append("PC BUILD RECOMMENDATION")
        output.append("="*70)
        output.append("")

        # Budget summary
        output.append(f"Total Cost: ${build.estimated_cost_usd:,.2f}")
        if build.estimated_cost_usd <= constraints.budget_usd:
            under_budget = constraints.budget_usd - build.estimated_cost_usd
            output.append(f"Under Budget: ${under_budget:,.2f} ({under_budget/constraints.budget_usd*100:.1f}%)")
        output.append("")

        # Component breakdown
        output.append("COMPONENTS")
        output.append("-"*70)
        output.append("")

        output.append(f"CPU: {build.cpu.model}")
        if include_technical_details:
            output.append(f"  • {build.cpu.cores} cores / {build.cpu.threads} threads")
            output.append(f"  • {build.cpu.base_clock_ghz} GHz base")
            if build.cpu.boost_clock_ghz:
                output.append(f"  • Up to {build.cpu.boost_clock_ghz} GHz boost")
            output.append(f"  • {build.cpu.tdp_w}W TDP")
            output.append(f"  • ${build.cpu.price_usd:.2f}")
        output.append("")

        if build.gpu:
            output.append(f"GPU: {build.gpu.model}")
            if include_technical_details:
                output.append(f"  • {build.gpu.vram_gb}GB {build.gpu.vram_type}")
                output.append(f"  • {build.gpu.tdp_w}W TDP")
                output.append(f"  • ${build.gpu.price_usd:.2f}")
            output.append("")
        else:
            output.append("GPU: Integrated Graphics")
            output.append("")

        output.append(f"Motherboard: {build.motherboard.model}")
        if include_technical_details:
            output.append(f"  • Chipset: {build.motherboard.chipset}")
            output.append(f"  • Socket: {build.motherboard.socket}")
            output.append(f"  • {build.motherboard.ram_type}, up to {build.motherboard.max_ram_gb}GB")
            output.append(f"  • ${build.motherboard.price_usd:.2f}")
        output.append("")

        output.append(f"RAM: {build.ram.capacity_gb}GB {build.ram.type}")
        if include_technical_details:
            output.append(f"  • {build.ram.speed_mhz} MHz")
            output.append(f"  • {build.ram.modules} modules")
            output.append(f"  • ${build.ram.price_usd:.2f}")
        output.append("")

        storage_total = sum(s.capacity_tb for s in build.storage)
        if build.additional_storage:
            storage_total += sum(s.capacity_tb for s in build.additional_storage)
        
        output.append(f"Storage: {storage_total:.1f}TB Total")
        for i, storage in enumerate(build.storage, 1):
            output.append(f"  Drive {i}: {storage.capacity_tb}TB {storage.type}")
            if include_technical_details:
                output.append(f"    • Interface: {storage.interface}")
                if storage.read_speed_mbps:
                    output.append(f"    • {storage.read_speed_mbps} MB/s read")
                output.append(f"    • ${storage.price_usd:.2f}")
        output.append("")

        output.append(f"PSU: {build.psu.wattage}W {build.psu.efficiency}")
        if include_technical_details:
            output.append(f"  • {build.psu.modular.capitalize()} modular")
            output.append(f"  • ${build.psu.price_usd:.2f}")
        output.append("")

        output.append(f"Cooling: {build.cooling.type.capitalize()} - {build.cooling.model}")
        if include_technical_details:
            output.append(f"  • Rated for {build.cooling.tdp_rating_w}W TDP")
            output.append(f"  • ${build.cooling.price_usd:.2f}")
        output.append("")

        output.append(f"Case: {build.chassis.model}")
        if include_technical_details:
            output.append(f"  • Form factor: {build.chassis.form_factor}")
            output.append(f"  • ${build.chassis.price_usd:.2f}")
        output.append("")

        # Power summary
        if build.estimated_tdp_w or (build.cpu and build.gpu):
            tdp = build.estimated_tdp_w or build.calculate_total_tdp()
            output.append(f"Estimated Power Draw: {tdp}W")
            headroom = ((build.psu.wattage - tdp) / build.psu.wattage) * 100
            output.append(f"PSU Headroom: {headroom:.1f}%")
            output.append("")

        # Rationale / Explanation
        if build.rationale:
            output.append("="*70)
            output.append("RATIONALE")
            output.append("="*70)
            output.append("")
            output.append(build.rationale)
            output.append("")

        explanation = self._generate_explanation(build, constraints)
        if explanation:
            output.append("="*70)
            output.append("ANALYSIS")
            output.append("="*70)
            output.append("")
            output.append(explanation)
            output.append("")

        output.append("="*70)

        return "\n".join(output)

    def _generate_explanation(self, build: PCBuild, constraints: Constraints) -> Optional[str]:
        prompt = f"""Analyze this PC build and provide:
1. Key tradeoffs made (what was prioritized vs sacrificed)
2. Potential bottlenecks for the target workload
3. Upgrade path recommendations over the next {constraints.upgrade_horizon_years} years

Build:
- CPU: {build.cpu.model} ({build.cpu.cores}C/{build.cpu.threads}T, {build.cpu.tdp_w}W)
- GPU: {build.gpu.model if build.gpu else 'Integrated Graphics'}
- RAM: {build.ram.capacity_gb}GB {build.ram.type}
- Storage: {sum(s.capacity_tb for s in build.storage)}TB {build.storage[0].type}
- Budget: ${build.estimated_cost_usd} of ${constraints.budget_usd}

User Workload: {', '.join(constraints.primary_workloads)}
Priorities: GPU={constraints.gpu_priority}, CPU={constraints.cpu_priority}

Keep it concise (3-5 bullet points total). Be specific and actionable."""

        try:
            response = self.llm.call(
                system_prompt="You are a PC hardware expert providing build analysis.",
                user_prompt=prompt,
                temperature=0.5
            )
            return response.strip()
        except Exception as e:
            logger.warning(f"Failed to generate LLM explanation: {e}")
            return None

    def quick_summary(self, build: PCBuild) -> str:
        """One-line build summary"""
        gpu_str = build.gpu.model if build.gpu else "iGPU"
        return (
            f"{build.cpu.model} + {gpu_str} | "
            f"{build.ram.capacity_gb}GB {build.ram.type} | "
            f"{sum(s.capacity_tb for s in build.storage)}TB | "
            f"${build.estimated_cost_usd:,.0f}"
        )
