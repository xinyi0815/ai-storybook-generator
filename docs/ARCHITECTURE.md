# System Architecture

**Status:** Phase 2 (Architecture Design & Task Decomposition) output

## 1. High-level flow

```
User input  ─►  Gradio  ─►  FastAPI  ─►  Story Agent (LLM)
                                            │
                                            ├─ story.json {pages, character_sheet}
                                            ▼
                                       Character Agent (Diffusion)
                                            │
                                            ├─ reference.png
                                            ▼
                                       Illustration Agent
                                       (Diffusion + IP-Adapter)
                                            │
                                            ├─ page_1.png ... page_N.png
                                            ▼
                                       PDF Compiler
                                            │
                                            ▼
                                       storybook.pdf  ─►  Gradio  ─►  User
```

## 2. Component contracts

### 2.1 Story Agent

**Input:**
```json
{
  "theme": "a brave little turtle who learns to swim",
  "main_character": "a green turtle named Momo with a yellow scarf",
  "age_group": "4-6",
  "num_pages": 4
}
```

**Output (`story.json`):**
```json
{
  "title": "Momo the Brave",
  "character_sheet": {
    "name": "Momo",
    "species": "turtle",
    "appearance": "small green sea turtle, bright yellow scarf around neck, large round eyes, friendly smile",
    "style_anchor": "soft watercolor children's book illustration, warm colors"
  },
  "pages": [
    {
      "page_number": 1,
      "narration": "Momo lived in a quiet pond, afraid of the deep blue sea.",
      "scene_prompt": "A small green turtle named Momo with a yellow scarf sits on a lily pad in a calm pond at dawn, looking nervously toward the horizon, soft watercolor style"
    }
  ]
}
```

**Implementation:** Single LLM call with a structured-output prompt that returns the JSON schema above. Validate with Pydantic. Retry once on parse failure.

### 2.2 Character Agent

**Input:** `character_sheet` from Story Agent
**Output:** `reference.png` (1024x1024)
**Prompt template:** `"character portrait, {appearance}, {style_anchor}, full body, neutral background, T-pose"`
**Why a separate step:** IP-Adapter needs a single canonical reference. Generating it once and reusing it guarantees consistency.

### 2.3 Illustration Agent

**Input:** `reference.png` + each page's `scene_prompt`
**Output:** `page_N.png` (1024x1024) for each page
**Method:** `diffusers` SDXL pipeline with `IPAdapter` plugin, `ip_adapter_scale=0.6` (balance between consistency and scene compliance). Same `generator` seed across pages for extra consistency.

### 2.4 PDF Compiler

Takes `story.json` + page PNGs, lays out one page per PDF page with narration as caption underneath. Uses ReportLab. No fancy typography in MVP.

## 3. API surface (FastAPI)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/generate` | Submit a generation job, returns `run_id` |
| `GET` | `/api/status/{run_id}` | Poll job status (`queued` / `story_done` / `reference_done` / `illustrations_done` / `complete` / `failed`) |
| `GET` | `/api/result/{run_id}` | Returns paths to PNGs + PDF when complete |
| `GET` | `/api/file/{run_id}/{filename}` | Static-serve a result file |

Async job execution via `asyncio.create_task` — no Celery/Redis for MVP, keep it in-process.

## 4. Directory layout

```
ai-storybook-generator/
├── backend/
│   ├── api.py              # FastAPI app + routes
│   ├── story_agent.py      # LLM client + prompt + Pydantic models
│   ├── character_agent.py  # SDXL reference image generation
│   ├── illustration_agent.py  # SDXL + IP-Adapter per-page generation
│   ├── pdf_compiler.py     # ReportLab assembly
│   ├── pipeline.py         # Orchestrates the three agents
│   └── models.py           # Pydantic request/response schemas
├── frontend/
│   └── app.py              # Gradio Blocks UI
├── configs/
│   └── settings.example.toml
├── docs/
├── outputs/                # gitignored
└── WORKFLOW.md
```

## 5. Why this split (alternatives considered)

- **Monolithic Gradio app**: Rejected — bundling backend logic into Gradio callbacks makes it harder to demonstrate clean Agent decomposition in the Workflow Log.
- **Single LLM call that also does image prompts**: Kept — Story Agent outputs both narration AND scene prompts in one call. Saves a roundtrip and ensures the prompts match the narration tone.
- **LoRA fine-tuning for character**: Rejected for MVP — training time eats budget. IP-Adapter gives 80% of the benefit in 0% of the training time.
- **Streamlit vs Gradio**: Gradio chosen for built-in gallery and async support.

## 6. Configuration

`configs/settings.toml`:
```toml
[llm]
provider = "ollama"         # ollama | bigpickle
base_url = "http://localhost:11434/v1"
model = "qwen2.5:7b"
api_key = "ollama"          # placeholder; required by openai client

[diffusion]
sdxl_model = "stabilityai/stable-diffusion-xl-base-1.0"
ip_adapter_repo = "h94/IP-Adapter"
ip_adapter_weight = "ip-adapter_sdxl.bin"
device = "cuda"
ip_adapter_scale = 0.6
num_inference_steps = 30

[output]
dir = "outputs"
image_size = 1024
```
