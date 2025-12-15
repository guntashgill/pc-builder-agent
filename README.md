# pc-builder-agent

An **agentic PC build recommendation system** that generates, validates, and explains custom PC configurations based on user-defined constraints.

---

## What This Does

Recommends a complete PC configuration—including:

- **CPU**
- **GPU**
- **RAM**
- **Storage**
- **Chassis**
- **Cooling System**
- **PSU**
- **Optional peripherals** (monitor, audio, etc.)

Based on user-input constraints such as:

- Budget
- Target workloads (gaming, ML, productivity, etc.)
- Performance priorities
- Form factor
- Noise tolerance
- Upgrade horizon and future-proofing preferences

---

## How It Works

The system is structured as a **multi-step agent pipeline** with clear boundaries between generative reasoning and deterministic validation.

---

### 1. Constraint Extraction (Requirement Interpretation)

Unstructured natural language input is converted into a **structured constraint representation**.

- A large language model interprets ambiguous or qualitative inputs  
  (e.g. *“future-proof,” “quiet,” “mostly for ML”*)
- These are normalized into explicit, machine-readable parameters:
  - Budget limits
  - Workload weights
  - Performance priorities
  - Form factor
  - Noise tolerance

**Output:** a validated constraint object representing user intent  
This object becomes the agent’s internal state.

---

### 2. Candidate Build Generation (Planning)

Using the structured constraints, the planner generates an initial PC build.

- Uses **generative reasoning**, not fixed rules
- Balances competing objectives:
  - GPU vs. budget
  - Thermals vs. acoustics
  - Immediate performance vs. upgrade path

**Output:** a complete candidate build with:
- Component selections
- Estimated cost
- Rationale for key choices

---

### 3. Deterministic Compatibility Validation

The candidate build is checked using deterministic logic to enforce **hard constraints**:

- CPU ↔ motherboard socket compatibility
- RAM type compatibility
- PSU wattage and headroom
- Chassis form factor constraints
- Cooling capacity vs. thermal load

This step ensures correctness that generative models alone cannot guarantee.

---

### 4. Tradeoff Analysis & Self-Critique (Agent Loop)

If validation fails or reveals risky tradeoffs:

- The agent analyzes *why* the failure occurred
- Produces structured feedback (errors + warnings)
- Revises **only the affected components**

This **plan → evaluate → revise loop** is what gives the system its **agentic behavior**.

---

### 5. Explanation & Recommendation Output

Once a valid build is produced, the system generates a human-readable explanation covering:

- Why each major component was chosen
- Tradeoffs that were made
- Potential bottlenecks
- Upgrade paths over time

The result is actionable for both beginners and advanced users.

---

### 6. Optional Extensions

The architecture is designed to be extensible, with optional modules for:

- Price awareness
- Bottleneck scoring
- Cloud deployment via a lightweight API

---

## Transitions Between Steps

### Step 1 → Step 2  
**Constraint Extraction → Build Planning**

**Output of Step 1:** Normalized Constraint Object (JSON)

```json
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
## Why This Matters

- **Removes ambiguity from natural language**
- **Enables deterministic validation**
- **Decouples NLP from planning logic**

---

## Step 2 → Step 3  
### Build Planning → Compatibility Validation

**Output of Step 2:** Candidate PC Configuration

The planner consumes the normalized constraint object and produces a **complete, structured PC configuration** with component selections and metadata.

### Example Candidate Build

```json
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
### Contract Guarantees

- Every required component is present  
- All fields are typed and directly comparable  
- No natural language is required downstream  

---

## Step 3 → Step 4  
### Compatibility Validation → Tradeoff Analysis

**Output of Step 3:** Validation Results (Pass / Fail + Failure Metadata)

The validator produces a structured result indicating whether the build is valid and, if not, why.

### Example (Failure Case)

```json
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
### Why Structured Feedback Matters

- Enables targeted revision  
- Prevents random re-planning  
- Makes failures explicit and explainable  

---

## Step 4 → Step 2 (Revision Loop)  
### Input to Step 2 (Revised Planning)

If validation fails or warnings exceed defined thresholds, the planner is re-invoked with:

- Original constraints  
- Previous build  
- Structured validation feedback  

### Example Revision Input

```json
{
  "original_constraints": { "...": "..." },
  "previous_build": { "...": "..." },
  "feedback": {
    "errors": ["insufficient_psu"],
    "warnings": ["thermal_risk"]
  }
}
The planner is instructed to **modify only the affected components**, preserving all valid decisions.

---

## Step 4 → Step 5  
### Final Build → Explanation Output

**Output of Step 4:** Final Approved Build

Once a valid configuration is reached, the final structured build is passed to the explanation layer.

### Explanation Stage Inputs

The explanation layer consumes:

- Final build specification  
- Original constraints  
- Tradeoff metadata  

and produces a **human-readable recommendation** explaining component choices, tradeoffs, and upgrade paths.

---

## Architectural Overview

This architecture demonstrates:

- Clear separation of concerns  
- Deterministic system boundaries  
- Agentic control over generative components  
- Production-style AI system design  

---

## Code File Structure

```text
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
│   │   ├── orchestrator.py  # Plan–validate–revise loop controller
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
│   │   ├── price_data.json  # Optional static prices
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
