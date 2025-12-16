# PersonA Implementation

Agent pipeline for interpreting user requests and generating PC builds.

## Components

### Interpreter (`app/agent/interpreter.py`)
Converts user input into structured constraints using LLM.

### Planner (`app/agent/planner.py`)
Generates PC builds from constraints. Supports revision mode.

### Critic (`app/agent/critic.py`)
Analyzes validation failures and generates revision feedback.

### Orchestrator (`app/agent/orchestrator.py`)
Coordinates the plan-validate-critique-revise loop. Max 5 iterations.

### Formatter (`app/explain/formatter.py`)
Formats builds into readable output with specs and pricing.

## LLM Configuration

Configure in `.env`:

**OpenAI:**
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**Ollama:**
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

## Testing

```bash
python test_quick_pipeline.py     # OpenAI (fast)
python test_complete_pipeline.py  # Ollama (slower)
```

## Pipeline Flow

```
Input → Interpreter → Planner → Validator → (if invalid) → Critic → Planner → ... → Formatter → Output
```

## Key Files

**LLM:**
- `app/llm/client.py` - OpenAI/Ollama client
- `app/llm/prompts/` - System prompts

**Agents:**
- `app/agent/interpreter.py`
- `app/agent/planner.py`
- `app/agent/critic.py`
- `app/agent/orchestrator.py`
- `app/explain/formatter.py`

## Integration

Uses PersonB's models and validation system. Planner generates builds matching the full schema required by PersonB's validator.
