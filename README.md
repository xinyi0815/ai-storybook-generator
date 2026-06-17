# AI Storybook Generator

> NYCU 1142.639002 Deep Generative Models — HW7 Final Project
> Student ID: **314832015**
> Public repo: https://github.com/xinyi0815/ai-storybook-generator

An agent-driven generative AI application that turns a user's idea into a fully illustrated children's storybook. Built end-to-end with LLM + Diffusion technologies, scaffolded and implemented through an Agentic Workflow with Claude Code (Opus 4.7).

## Demo

The user types a theme, a description of the main character, an age group, and a page count. The system produces:

1. A coherent multi-page story with paginated scene descriptions (LLM)
2. A character reference sheet (SDXL)
3. Per-page illustrations with a visually consistent main character (SDXL + IP-Adapter)
4. A downloadable A5 PDF storybook

Single screenshot of the running Gradio UI is in [docs/demo.png](docs/demo.png). Full development journey, including every debugging step and the actual prompts I gave the agent, is in [WORKFLOW.md](WORKFLOW.md).

## System Architecture

```
+-------------+      +------------------+
|  Gradio UI  +----->+  FastAPI Backend |        (in-process pipeline call also supported)
+-------------+      +---------+--------+
                               |
       +-----------------------+-----------------------+
       |                       |                       |
       v                       v                       v
+--------------+    +-------------------+    +---------------------+
|  Story Agent |    |  Character Agent  |    | Illustration Agent  |
|   (LLM)      |    |    (SDXL)         |    | (SDXL + IP-Adapter) |
|              |    |  reference image  |    | one image per page  |
+--------------+    +-------------------+    +---------------------+
       |                       |                       |
       +-----------------------+-----------------------+
                               |
                               v
                      +-----------------+
                      |  PDF Compiler   |   (ReportLab A5)
                      +-----------------+
```

- Full architecture rationale and component contracts: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Product spec / MVP feature list: [docs/PRD.md](docs/PRD.md)
- 16-task breakdown that drove implementation: [docs/TASKS.md](docs/TASKS.md)
- Agent collaboration log (prompts, bottlenecks, fixes): [WORKFLOW.md](WORKFLOW.md)

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| LLM | Ollama `qwen2.5:7b` (Q4_K_M, 32k ctx) | Local inference on workstation, OpenAI-compatible REST API |
| LLM (backup) | Big Pickle (`opencode/big-pickle`) | Free hosted, 200k context |
| Diffusion | Stable Diffusion XL base 1.0 | 30 inference steps, ~2 s/image on H100 |
| Character consistency | IP-Adapter (`h94/IP-Adapter`, `ip-adapter_sdxl.bin`) | Zero-shot, lazy-loaded after the reference image is rendered |
| Backend | FastAPI + Uvicorn | Clean API surface; pipeline can also be called in-process |
| Frontend | Gradio Blocks (port 7860) | Live progress, gallery, PDF download |
| PDF | ReportLab A5 | Cover + image-per-page with narration captions |

## Local Setup

### Prerequisites

- **GPU workstation** with NVIDIA card (≥12 GB VRAM recommended for SDXL; tested on H100 NVL with 95 GB VRAM)
- **Python 3.10 or 3.11** (3.12+ may have issues with some diffusion deps)
- [Ollama](https://ollama.com/) installed with a model pulled
- ~30 GB free disk for model weights + cache

If you don't have `sudo` on the workstation, see [docs/SETUP_WORKSTATION.md §1](docs/SETUP_WORKSTATION.md) for a userspace Ollama install path (download tarball to `~/.local`).

### Install

```bash
git clone https://github.com/xinyi0815/ai-storybook-generator.git
cd ai-storybook-generator

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip

# PyTorch with the right CUDA wheel (check nvidia-smi first; cu124 works for CUDA 12+ drivers)
pip install torch --index-url https://download.pytorch.org/whl/cu124

# Everything else
pip install -r requirements.txt

# Ollama model
ollama pull qwen2.5:7b

# Config
cp configs/settings.example.toml configs/settings.toml
# Edit if you need to point at a remote Ollama / Big Pickle endpoint.

# Pre-download SDXL + IP-Adapter weights (~10 GB; saves a 5-min wait on first run)
python scripts/prefetch_weights.py

# Verify the full environment
python scripts/verify_env.py
```

Expected `verify_env.py` output: green check for Python version, CUDA, Ollama reachable, diffusers + transformers loaded, disk free.

### Run (the simple way)

Make sure Ollama is running, then:

```bash
# Ollama (only if not already running as a service)
nohup ollama serve > ~/ollama.log 2>&1 &

# Gradio UI — calls the backend pipeline in-process
python frontend/app.py
```

Open `http://localhost:7860`.

### Run (with the FastAPI backend separately)

```bash
# Terminal 1
uvicorn backend.api:app --host 0.0.0.0 --port 8000

# Terminal 2
python frontend/app.py    # currently uses in-process; see docstring to switch
```

API routes: `POST /api/generate`, `GET /api/status/{run_id}`, `GET /api/result/{run_id}`, `GET /api/file/{run_id}/{filename}`. See [backend/api.py](backend/api.py).

### Remote demo via SSH port forward

If you're running the workstation remotely (as I do), forward the Gradio port:

```powershell
# from your local machine
ssh -L 7860:localhost:7860 -p <workstation_port> <user>@<workstation_host>
```

Then open `http://localhost:7860` in your local browser.

## Outputs

Each generation lands in `outputs/<run_id>/`:

```
outputs/<run_id>/
├── story.json          # the LLM-generated story document
├── reference.png       # IP-Adapter character reference (SDXL only)
├── page_01.png ...     # per-page illustrations (SDXL + IP-Adapter)
└── storybook.pdf       # compiled A5 PDF
```

## Smoke tests

Run these in order if you're verifying a fresh setup:

```bash
python scripts/test_story_agent.py          # T2 — LLM story generation
python scripts/test_character_agent.py      # T3 — SDXL reference image
python scripts/test_illustration_agent.py   # T4 — IP-Adapter per-page render
python scripts/test_pipeline_e2e.py         # T5..T6 — full pipeline + PDF
```

Each script saves its output under `outputs/` so you can sanity-check visually.

## Known limitations

- **Small wearable accessories** (e.g. "a yellow scarf around the turtle's neck") are often dropped by SDXL even when they're in every prompt. The character's main shape, color, and species stay consistent across pages thanks to IP-Adapter, but tiny accessory details require either prompt weighting (Compel) or a small fine-tuned LoRA. Discussed in [WORKFLOW.md §3.5 Bug 3](WORKFLOW.md).
- **Page 4 sometimes drifts from the narration**, e.g. the story says "back on the beach" but the image keeps the character underwater. This is a known IP-Adapter behavior: at scale 0.6, the model anchors too strongly to the reference's environment context. Lowering to 0.4 helps but slightly weakens character identity. Tradeoff lives in `configs/settings.toml`.
- **English-only narration.** The LLM prompt currently asks for English output. Switching to Traditional Chinese is a one-line change in `backend/story_agent.py` but isn't validated.
- **No persistence.** Job state is in-memory; restarting the backend loses run IDs. Outputs on disk survive.
- **Single concurrent generation.** SDXL + IP-Adapter fully occupies the GPU; `concurrency_limit=1` in `frontend/app.py` enforces serial processing.

## License

Coursework. Not for redistribution.
