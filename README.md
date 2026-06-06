# AI Storybook Generator

> NYCU 1142.639002 Deep Generative Models — HW7 Final Project
> Student ID: 314832015

An agent-driven generative AI application that turns a user's idea into a fully illustrated children's storybook. Built end-to-end with LLM + Diffusion technologies, scaffolded and implemented through an Agentic Workflow.

## Demo

Input a theme, main character traits, age group, and page count. The app produces:

1. A coherent story with paginated scene descriptions (LLM)
2. A character reference sheet (Diffusion)
3. Per-page illustrations with a consistent main character (Diffusion + IP-Adapter)
4. A downloadable PDF storybook

## System Architecture

```
+-------------+      +------------------+
|  Gradio UI  +----->+  FastAPI Backend |
+-------------+      +---------+--------+
                               |
       +-----------------------+-----------------------+
       |                       |                       |
       v                       v                       v
+--------------+    +-------------------+    +------------------+
|  Story Agent |    |  Character Agent  |    | Illustration     |
|   (LLM)      |    |    (SDXL)         |    | Agent            |
|              |    |                   |    | (SDXL + IPAdapter)|
+--------------+    +-------------------+    +------------------+
       |                       |                       |
       +-----------------------+-----------------------+
                               |
                               v
                      +-----------------+
                      |  PDF Compiler   |
                      +-----------------+
```

Full architecture details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
Product spec: [docs/PRD.md](docs/PRD.md)
Task breakdown: [docs/TASKS.md](docs/TASKS.md)
Agent collaboration log: [WORKFLOW.md](WORKFLOW.md)

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| LLM | Ollama (`qwen2.5:7b` or `llama3.1:8b`) | Local inference on workstation, OpenAI-compatible REST |
| LLM (backup) | Big Pickle (`opencode/big-pickle`) | Free hosted, 200k context |
| Diffusion | Stable Diffusion XL | Workstation GPU |
| Character consistency | IP-Adapter (via `diffusers`) | Locks main character across pages |
| Backend | FastAPI + Uvicorn | |
| Frontend | Gradio Blocks | |
| PDF | ReportLab | |

## Local Setup

### Prerequisites

- Workstation with NVIDIA GPU (>= 12 GB VRAM recommended for SDXL)
- Python 3.10 or 3.11 (3.12+ may have issues with some diffusion deps)
- [Ollama](https://ollama.com/) installed and a model pulled:
  ```bash
  ollama pull qwen2.5:7b
  ```

### Install

```bash
git clone https://github.com/xinyi0815/ai-storybook-generator.git
cd ai-storybook-generator
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp configs/settings.example.toml configs/settings.toml
# Edit configs/settings.toml if you need to point at a remote Ollama / Big Pickle
```

### Run

```bash
# 1. Start backend (in one terminal)
uvicorn backend.api:app --host 0.0.0.0 --port 8000

# 2. Start frontend (in another terminal)
python frontend/app.py
```

Open the Gradio URL printed in the terminal.

## Outputs

Generated storybooks land in `outputs/<run_id>/` as both individual PNG pages and a compiled `storybook.pdf`.

## License

Coursework — not for redistribution.
