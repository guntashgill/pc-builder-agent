# pc-builder-agent
PC build recommendation agent.

What this does
Recommends a PC configuration(CPU model, GPU model, RAM, Storage, Chassis, Cooling System, PSU, Other Peripherals like monitors, speakers, headphones) given user inputted constraints including budget, workloads, performance priorities, form factor, noise tolerance, and upgrade preferences

How it does it
1. Constraint extraction (Requirement interpretation)

The system first converts unstructured user input into a structured set of constraints.
A large language model is used to interpret ambiguous or qualitative requirements (e.g., “future-proof,” “quiet,” “mostly for ML”) and normalize them into explicit parameters such as budget limits, workload weights, form factor, and performance priorities.

This step produces a validated, machine-readable representation of user intent that serves as the agent’s internal state.

2. Candidate build generation (Planning)

Using the extracted constraints, the agent generates an initial PC configuration.
Rather than selecting parts through fixed rules, the system uses generative reasoning to balance competing objectives such as GPU performance vs. budget, thermals vs. acoustics, and present performance vs. upgrade path.

The output at this stage is a complete candidate build with estimated cost and rationale for key choices

3. Deterministic compatibility validation

The candidate build is then checked using deterministic validation logic to ensure correctness and feasibility.
This includes verifying component compatibility (e.g., CPU socket and motherboard, RAM type, PSU wattage headroom, chassis form factor, and cooling capacity).

This step enforces hard constraints that cannot be reliably guaranteed by generative models alone.

4. Tradeoff analysis and self-critique

If the build violates constraints or exhibits suboptimal tradeoffs, the agent evaluates the failure mode (e.g., power insufficiency, thermal risk, budget overrun).
The system generates structured feedback describing what went wrong and why, then revises the configuration accordingly.

This iterative plan-evaluate-revise loop is what gives the system its agentic behavior

5. Explanation and recommendation output

Once a valid configuration is produced, the system generates a human-readable explanation describing:

Why each major component was chosen

What tradeoffs were made

Where performance bottlenecks may exist

How the system can be upgraded in the future

This allows the recommendation to be understandable and actionable for users with varying levels of technical expertise.

6. Optional extensions

The system is designed to be extensible, with optional modules for price awareness, bottleneck scoring, or cloud-hosted deployment via a lightweight API.

Transitions between Steps
Step 1 → Step 2
Constraint Extraction → Build Planning
Output of Step 1: Normalized Constraint Object

After interpreting user input, the system produces a validated JSON object representing the user’s requirements.
This object serves as the agent’s internal state and is the only input to the planning stage.

Example
{
  "budget_usd": 1500,
  "primary_workloads": ["gaming", "ml"],
  "gpu_priority": "high",
  "cpu_priority": "medium",
  "ram_min_gb": 32,
  "storage_min_tb": 1,
  "form_factor": "mid-tower",
  "noise_tolerance": "low",
  "upgrade_horizon_years": 3,
  "peripherals": {
    "monitor": true,
    "audio": false
  }
}

Why this matters
Removes ambiguity from natural language
Allows deterministic validation
Decouples NLP from planning logic

Step 2 → Step 3
Build Planning → Compatibility Validation
Output of Step 2: Candidate PC Configuration

The planner consumes the constraint object and produces a complete candidate configuration with structured component selections and metadata.

Example
{
  "cpu": {
    "model": "Ryzen 5 7600",
    "socket": "AM5",
    "tdp_w": 65
  },
  "gpu": {
    "model": "RTX 4060 Ti",
    "vram_gb": 16,
    "tdp_w": 160
  },
  "ram": {
    "capacity_gb": 32,
    "type": "DDR5"
  },
  "storage": {
    "type": "NVMe SSD",
    "capacity_tb": 2
  },
  "chassis": {
    "form_factor": "mid-tower"
  },
  "psu": {
    "wattage": 750,
    "efficiency": "Gold"
  },
  "cooling": {
    "type": "Air"
  },
  "estimated_cost_usd": 1475
}

Contract guarantees

Every required component is present

All fields are typed and comparable

No natural language is required downstream


Step 3 → Step 4
Compatibility Validation → Tradeoff Analysis
 Output of Step 3: Validation Results (Pass / Fail + Failure Metadata)

The validator produces a structured result indicating whether the build is valid and, if not, why.

Example (failure case)
{
  "is_valid": false,
  "errors": [
    {
      "type": "power",
      "message": "Estimated load exceeds PSU headroom by 12%"
    }
  ],
  "warnings": [
    {
      "type": "thermals",
      "message": "Air cooling may be insufficient under sustained GPU load"
    }
  ]
}

Why structured feedback matters
Enables targeted revision
Prevents random re-planning
Makes failures explainable

Step 4 → Step 2(Revision Loop)
Input to Step 2 (Revised Planning)

If validation fails or warnings exceed thresholds, the planner is re-invoked with:

Original constraints

Previous build

Structured validation feedback

Example revision input
{
  "original_constraints": { ... },
  "previous_build": { ... },
  "feedback": {
    "errors": ["insufficient_psu"],
    "warnings": ["thermal_risk"]
  }
}


The planner is instructed to modify only the affected components, preserving valid decisions.
Step 4 → Step 5
Final Build → Explanation Output
Output of Step 4: Final Approved Build

Once a valid configuration is reached, the final structured build is passed to the explanation layer.

The explanation stage consumes:
Final build spec
Original constraints
Tradeoff metadata
and produces a human-readable recommendation.

This architecture demonstrates:
Clear separation of concerns
Deterministic system boundaries
Agentic control over generative components
Production-style AI system design
Code File Structure
pc-build-agent/
├── README.md
├── requirements.txt
├── .env.example
│
├── app/
│   ├── main.py              # Entry point (CLI or API)
│   ├── config.py            # Global config (budgets, thresholds)
│
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── orchestrator.py  # Controls agent loop
│   │   ├── interpreter.py   # Step 1: constraint extraction
│   │   ├── planner.py       # Step 2: build generation
│   │   ├── critic.py        # Step 4: evaluation & revision
│
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── compatibility.py # Socket, PSU, form factor checks
│   │   ├── power.py         # Power estimation logic
│
│   ├── data/
│   │   ├── parts_db.json    # Component metadata
│   │   ├── price_data.json  # (Optional) static prices
│
│   ├── models/
│   │   ├── constraints.py   # Dataclasses / schemas
│   │   ├── build.py         # Build specification model
│   │   ├── validation.py    # Validation result model
│
│   ├── llm/
│   │   ├── client.py        # LLM wrapper (OpenAI, etc.)
│   │   ├── prompts/
│   │   │   ├── interpret.txt
│   │   │   ├── plan.txt
│   │   │   └── critique.txt
│
│   ├── explain/
│   │   └── formatter.py     # Human-readable explanation
│
│   └── utils/
│       ├── logging.py
│       └── errors.py
│
└── tests/
    ├── test_validation.py
    └── test_planner.py


