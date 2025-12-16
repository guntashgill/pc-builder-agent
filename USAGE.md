# Usage Guide

## Quick Start

Run the PC Builder Agent interactively:

```bash
python run.py
```

## Usage Modes

### Interactive Mode (Default)
Chat with the agent to design multiple builds:

```bash
python run.py
```

Example session:
```
💬 Your requirements: I need a gaming PC for $1500
🔨 Building your PC...
[Your custom build appears here]
✅ Build complete! Want another?

💬 Your requirements: Build me a workstation for video editing under $2000
...
```

### Quick Mode
Generate a single build and exit:

```bash
python run.py --quick "gaming PC for $1500"
```

### Verbose Mode
See detailed logs and agent reasoning:

```bash
python run.py --verbose
```

## Example Requests

**Gaming:**
- "I need a gaming PC for $1500 that can handle 1440p"
- "Build me a high-end gaming rig for 4K under $3000"
- "I want a budget gaming PC for $800"

**Workstation:**
- "Build me a quiet workstation for video editing under $2000"
- "I need a PC for 3D rendering with 64GB RAM"
- "Workstation for programming and Docker, $1200 budget"

**Machine Learning:**
- "I want a compact PC for machine learning with RTX 4090"
- "ML workstation with 128GB RAM under $5000"
- "Deep learning PC with dual GPUs"

**Office/Home:**
- "I need a quiet office PC for $800"
- "Build me a small form factor PC for basic tasks"
- "Home office PC with good multitasking, $1000"

## Commands

While running interactively:
- Type your requirements and press Enter
- Type `quit`, `exit`, or `q` to stop
- Press `Ctrl+C` to interrupt

## Configuration

Edit `.env` to change LLM provider:

**Using OpenAI (recommended for speed):**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

**Using Ollama (free, slower):**
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

## Tips

1. **Be specific** about budget, workload, and priorities
2. **Mention constraints** like size, noise, or specific components
3. **Use verbose mode** (`-v`) if you want to see the agent's thinking process
4. **Quick mode** is great for scripting or automation
