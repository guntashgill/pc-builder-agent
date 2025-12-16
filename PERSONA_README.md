# PersonA Implementation - PC Builder Agent Pipeline

This document explains the LLM/Agent pipeline implemented by PersonA.

## Components Implemented

PersonA owns the complete agentic loop (Steps 1, 2, 4, 5 from the main README):

### 1. **Interpreter** (`app/agent/interpreter.py`)
- Extracts structured constraints from natural language user input
- Uses LLM to parse free-form requests into `Constraints` model
- Prompt: `app/llm/prompts/interpret.txt`

### 2. **Planner** (`app/agent/planner.py`)
- Generates PC builds from constraints
- Supports revision mode (takes feedback from critic)
- Uses LLM to select compatible components
- Prompt: `app/llm/prompts/plan.txt`

### 3. **Critic** (`app/agent/critic.py`)
- Analyzes validation failures from PersonB's validator
- Identifies root causes and recommends specific fixes
- Generates feedback for planner to revise the build
- Prompt: `app/llm/prompts/critique.txt`

### 4. **Orchestrator** (`app/agent/orchestrator.py`)
- Main controller coordinating the agentic loop
- Pipeline: Interpret → Plan → Validate → Critique → Revise → Repeat
- Max 5 iterations to find a valid build
- Raises error if valid build cannot be generated

### 5. **Formatter** (`app/explain/formatter.py`)
- Generates human-readable explanations of builds
- Shows component specs, pricing, power calculations
- Uses LLM to generate tradeoff analysis and upgrade recommendations

## LLM Configuration

The system supports two LLM providers:

### OpenAI (Paid, Fast)
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### Ollama (Free, Local, Slower)
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

**Recommendation**: Use OpenAI for development/testing (faster), Ollama for production (free for users).

## Testing

### Quick Test (OpenAI)
```bash
python test_quick_pipeline.py
```

This test uses OpenAI temporarily for speed and validates the entire pipeline works.

### Full Test (Ollama)
```bash
python test_complete_pipeline.py
```

This test uses Ollama (slower but free). Expect 2-5 minutes for completion.

## How the Pipeline Works

```
User Input: "I need a gaming PC for $1500"
    ↓
[1] Interpreter
    ↓
Constraints: {budget: 1500, workloads: ["gaming"], gpu_priority: "high", ...}
    ↓
[2] Planner
    ↓
Build: {cpu: RTX 4070, gpu: Ryzen 5 7600, ...}
    ↓
[3] Validator (PersonB)
    ↓
ValidationResult: {is_valid: false, errors: ["Socket mismatch"]}
    ↓
[4] Critic
    ↓
Feedback: "CPU socket AM5 doesn't match motherboard LGA1700. Switch to compatible motherboard."
    ↓
[2] Planner (revision with feedback)
    ↓
Build: {cpu: RTX 4070, gpu: Ryzen 5 7600, motherboard: B650 (AM5), ...}
    ↓
[3] Validator
    ↓
ValidationResult: {is_valid: true}
    ↓
[5] Formatter
    ↓
Human-Readable Output with specs, pricing, analysis
```

## Integration with PersonB

PersonB provides:
- Detailed data models (`app/models/build.py`, `app/models/constraints.py`)
- Validation system (`app/validation/`)
- Parts database (234k+ lines)

PersonA's planner generates builds matching PersonB's detailed schema with ALL required fields:
- CPU: brand, socket, cores, threads, base_clock_ghz, boost_clock_ghz, tdp_w, price_usd, etc.
- GPU: brand, chipset, vram_gb, vram_type, tdp_w, length_mm, pcie_slots, power_connectors, price_usd, etc.
- And all other components with full specifications

## Key Files

### LLM Client
- `app/llm/client.py` - Unified client supporting OpenAI and Ollama

### Prompts
- `app/llm/prompts/interpret.txt` - Constraint extraction instructions
- `app/llm/prompts/plan.txt` - Build generation instructions (CRITICAL: matches PersonB's schema)
- `app/llm/prompts/critique.txt` - Failure analysis instructions

### Agent Modules
- `app/agent/interpreter.py` - Step 1: Extract constraints
- `app/agent/planner.py` - Step 2: Generate builds
- `app/agent/critic.py` - Step 4: Analyze failures
- `app/agent/orchestrator.py` - Main loop controller
- `app/explain/formatter.py` - Step 5: Format output

## Troubleshooting

### Issue: Ollama is very slow
**Solution**: This is expected for local LLMs. Use OpenAI for development, or be patient.

### Issue: Plan prompt generates incomplete JSON
**Solution**: Ensure `plan.txt` matches PersonB's models. ALL fields must be present.

### Issue: Validation always fails
**Solution**: Check that planner generates builds matching PersonB's schema exactly.

### Issue: LLM returns non-JSON
**Solution**: For Ollama, ensure model is llama3.1:8b or newer. May need to retry.

## Success Metrics

A successful pipeline run should:
1. Extract constraints correctly from user input
2. Generate a valid build within 1-3 iterations
3. Pass all of PersonB's validation rules
4. Format output with complete specs and analysis

Example successful run:
```
INFO - Constraints: budget=$1500, workloads=['gaming']
INFO - ITERATION 1/3
INFO - Build generated: AMD Ryzen 5 7600, NVIDIA GeForce RTX 4070
INFO - Cost: $1499.92
INFO - ✅ BUILD VALID! (completed in 1 iterations)
```

## Next Steps

1. Test with various user inputs (gaming, ML, office builds)
2. Test failure/revision scenarios
3. Optimize prompts for better first-attempt success rate
4. Create main.py CLI entry point (shared with PersonB)
5. Add more comprehensive tests
6. Push PersonA branch for review
