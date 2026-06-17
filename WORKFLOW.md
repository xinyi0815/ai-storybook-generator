# Agent Collaboration Workflow Log

This document records the agent-assisted development process for HW7 ("AI Storybook Generator"). It captures the actual prompts used, the tools combined, and the technical bottlenecks resolved with the agent's help — as required by §V.3 of the assignment.

- **Student:** 314832015
- **Course:** NYCU 1142.639002 Deep Generative Models
- **Agent:** Claude Code (Opus 4.7, 1M context window) running inside VS Code
- **Backends used:** Ollama (local LLM), Hugging Face Hub (model weights), an internal H100 NVL workstation for SDXL inference
- **Local dev box:** Windows 10, Python 3.14 (used only for editing + git; not for running the model stack)

---

## Phase 1 — Ideation & Planning (2026-06-06)

### Step 1.1 — Read the assignment, brainstorm shapes of project

**My prompt:**
> "可以看一下模組課嗎?"

**What the agent did:**
The agent enumerated the contents of `c:/Users/xinyi/Desktop/雜項misc/模組課/` and read the HW7 PDF. It summarized the four-phase Agent Workflow requirement (Ideation → Architecture → Implementation → UI) and the two required tech families (LLM and/or Diffusion/Flow Matching). Rather than dive in, it asked whether to brainstorm topics or jump to a plan.

**Key decision I made:** I told it to "直接幫我規劃" (just plan it for me).

### Step 1.2 — Choose between three candidate project shapes

The agent proposed three:
1. AI Interactive Storybook Generator (LLM + Diffusion, character consistency challenge)
2. Personal Knowledge Assistant with Voice + Visuals (LLM/RAG only)
3. Webtoon-style 4-panel Comic Generator (similar to #1, smaller scope)

**Why #1 won:** it (a) hits both required tech families, (b) has a real technical challenge worth writing about (character consistency across pages), and (c) demos visually well. The agent flagged the IP-Adapter character consistency angle as the key differentiator from a generic "LLM writes story" project.

### Step 1.3 — Adjust to my constraints

**My prompt:**
> "我有GITHUB...沒有 OpenRouter / Replicate API key...我不打算用本機訓練，我有工作站可以讓我用"

**What changed in the plan:**
- LLM → Ollama on the workstation (no API key needed)
- Diffusion → local SDXL + IP-Adapter on the workstation H100 (no Replicate)
- Backup LLM → Big Pickle (mentioned in the assignment spec, free)

**Phase 1 outputs:**
- [docs/PRD.md](docs/PRD.md) — Product Requirements Document with MVP feature list, target user, success criteria, and risk register
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System architecture and component contracts
- [docs/TASKS.md](docs/TASKS.md) — 16 tasks (T1..T16) sized at 1–4 hours each
- The agent committed these to a fresh GitHub repo at https://github.com/xinyi0815/ai-storybook-generator

---

## Phase 2 — Architecture & Task Decomposition

Three design decisions were debated with the agent. For each, the agent offered an opinion, I challenged it, and we landed somewhere defensible.

| Decision | First instinct | What the agent argued | Final |
|---|---|---|---|
| Should the IP-Adapter reference image be the first page's image? | Reuse page 1 | A dedicated T-pose / neutral-background reference gives IP-Adapter a cleaner signal than a busy scene | **Dedicated reference** (separate Character Agent) |
| One LLM call or two (story + per-page scene prompts split)? | Split for clarity | Single call shares full narrative context, so scene prompts naturally match story tone | **Single call** |
| Use Celery/Redis or in-process async? | Celery for "production feel" | For an MVP demo this burns a day for zero demo benefit | **In-process `asyncio` + thread executor** |
| Train a character LoRA? | Tempting | 17-day budget — dataset curation alone eats a week. IP-Adapter is zero-shot from a single reference image | **IP-Adapter (zero-shot)** |

These design choices are captured in [docs/ARCHITECTURE.md §5](docs/ARCHITECTURE.md).

---

## Phase 3 — Implementation

Below is a chronological log of every non-trivial bottleneck. Trivial steps (typing models, scaffolding folders) are omitted.

### Step 3.1 — Repo scaffold + first commit (no friction)

Agent created the folder tree, wrote README/PRD/ARCHITECTURE/TASKS in one batch, ran `git init`, committed. ~5 minutes.

### Step 3.2 — Workstation environment: GPU + Python OK, Ollama install path broken

**Workstation:** H100 NVL, 95.8 GB VRAM, CUDA driver 13.0 (max supported runtime), Python 3.10.12 system. No `sudo`.

**Bottleneck 1 — Ollama install:**
The agent gave me `curl -fsSL https://ollama.com/install.sh | sh` from the official docs. It failed with `xinyi081592 is not in the sudoers file. This incident will be reported.`

**How the agent debugged:**
1. Suggested a userspace install path: download tarball to `~/.local/`
2. First URL guess (`ollama.com/download/ollama-linux-amd64.tgz`) returned 9-byte "Not Found"
3. Pivoted to GitHub releases. The "latest" URL also 404'd
4. Wrote a quick Python one-liner querying `api.github.com/repos/ollama/ollama/releases/latest` to list real asset names
5. Discovered the asset is now `ollama-linux-amd64.tar.zst` (Zstandard, ~1.3 GB), not `.tgz`

**Final fix:**
```bash
curl -fL -o /tmp/ollama.tar.zst \
  https://github.com/ollama/ollama/releases/download/v0.30.6/ollama-linux-amd64.tar.zst
mkdir -p ~/.local
tar --zstd -C ~/.local -xf /tmp/ollama.tar.zst
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
nohup ollama serve > ~/ollama.log 2>&1 &
ollama pull qwen2.5:7b
```

**Lesson:** Vendor docs assume `sudo`. For shared workstations, always have a userspace fallback ready, and **read the actual asset list** instead of trusting the documented filename.

### Step 3.3 — Dependency hell: `transformers` × `diffusers` × `torch` 三方不相容

Three errors in a row, each unmasked by the previous fix:

**Error A:**
```
AttributeError: module 'torch' has no attribute 'float8_e8m0fnu'
```
Root cause: `transformers 5.10.2` (auto-installed by `pip install -r requirements.txt`) references a dtype only present in `torch>=2.6`. My CUDA 12.4 wheel was `torch 2.5`.

**Agent's first fix:** pin `transformers<4.50`, push.

**Error B (after the fix):**
```
ImportError: cannot import name 'Dinov2WithRegistersConfig' from 'transformers'
```
Root cause: `diffusers 0.38` references that symbol from `transformers 5.x`. The downgrade of `transformers` broke `diffusers`.

**This is where I gave the agent its biggest correction.** I had run an install command from a prior message before the agent finished pushing the new pin, so the repo and the workstation got out of sync.

**My prompt:**
> "不是阿，你先全部理解完再給我指令，因為你上面那個我執行了你改完requirements.txt之前得指令"

**What the agent changed in its behavior:**
1. It saved this lesson to its persistent memory as a `feedback` entry: *"Don't push speculative dep/config fixes until the user verifies they work on their machine."*
2. From this point forward, for env work, it gave one consolidated command, waited for me to verify, and only then committed the verified version to git.

**Final verified combo (pushed to `requirements.txt`):**
```
torch 2.5+cu124
diffusers==0.31.0
transformers==4.46.3
huggingface_hub 0.36.2
```

**Verification:**
```
[ OK ] Python 3.10
       torch 2.6.0+cu124
[ OK ] CUDA available on NVIDIA H100 NVL (93.1 GB VRAM)
[ OK ] Ollama reachable, models: qwen2.5:7b
[ OK ] diffusers 0.31.0, transformers 4.46.3
[ OK ] 1150.8 GB free disk in current dir
```

**Lesson:** Pin **all** packages whose APIs you touch, not just the one that errored. Latest-of-everything will drift in 18 months.

### Step 3.4 — Story Agent (T1 + T2): the easy win

Pydantic models + OpenAI-compatible client pointed at Ollama, JSON `response_format`, one validation retry. The agent wrote the system prompt to enforce a strict JSON schema:

```
Strict rules:
1. The `pages` array MUST contain exactly the number of pages requested.
2. Every `scene_prompt` MUST include the character's appearance (color,
   clothing, features) and the style_anchor, restated each time.
3. Narration must be appropriate for the target age group...
4. Tell a complete story arc across the pages: setup, challenge, turning
   point, resolution.
5. Output JSON only. No prose, no markdown fences, no explanations.
```

**Result:** First-try success. `qwen2.5:7b` produced a valid `StoryDocument` with 4 pages, every `scene_prompt` correctly restated the character appearance + style anchor — exactly what IP-Adapter consistency needs downstream.

### Step 3.5 — Diffusion Agents (T3 + T4): the real fight

This is where the project's "specific technical bottleneck resolved with Agent's assistance" lives.

#### Bug 1 — `encoder_hid_dim_type='ip_image_proj'` requires `image_embeds`

After loading IP-Adapter and immediately running reference generation (which doesn't pass any reference image), SDXL exploded with:

```
ValueError: <class 'UNet2DConditionModel'> has the config param
`encoder_hid_dim_type` set to 'ip_image_proj' which requires the keyword
argument `image_embeds` to be passed in `added_cond_kwargs`
```

**Agent's diagnosis:** `pipe.load_ip_adapter(...)` mutates the UNet config permanently. From that call onward, every `pipe(...)` invocation requires `image_embeds` — even when `set_ip_adapter_scale(0)`. Setting scale to zero only zeros the cross-attention contribution; it doesn't escape the input validation.

**Fix:** Lazy-load IP-Adapter. `character_agent.get_pipeline()` returns plain SDXL; `character_agent.ensure_ip_adapter_loaded()` attaches IP-Adapter the first time `illustration_agent.generate_page` is called. The reference image is generated BEFORE IP-Adapter is ever attached, so the pristine SDXL pipeline serves it.

This is captured in [backend/character_agent.py](backend/character_agent.py) — there's a deliberate comment explaining the ordering invariant.

#### Bug 2 — "character reference sheet" produces a multi-pose layout

First successful pipeline run gave:
- `test_reference.png` — a multi-turtle character model sheet (front turtle, smaller copies in corners)
- `test_page.png` — IP-Adapter dutifully transferred that *layout* into the page, producing more multi-turtle compositions, not a single swimming Momo

**Agent's diagnosis:** The prompt literally said `"character reference sheet of Momo the turtle..."`. SDXL's training data is full of model sheets that look exactly like that. IP-Adapter (scale 0.6) then preserved the multi-character composition into the page.

**Fix:**
- Reference prompt rewritten to ask for `"a single ... full body portrait, standing alone"`
- Both reference and page negative prompts explicitly reject `"character sheet, model sheet, reference sheet, multiple poses, montage, multiple characters, duplicate, two characters, group of characters"`

After the fix, references are single-character and pages render single characters in scene-appropriate environments.

#### Bug 3 — yellow scarf never rendered (unfixed, documented)

Across every successful run, the `bright yellow scarf tied around Momo's neck` is mentioned in the character_sheet and restated in every page's scene_prompt, but **SDXL consistently omits the scarf**. This is a known SDXL weakness: small wearable accessories in the middle of a long prompt get attention-dropped, especially when prompt tokens are dominated by environment descriptors.

**Mitigations tried during the project:**
- Re-ordering: putting `"wearing a bright yellow scarf"` near the front of the appearance string
- Stronger negative prompts ("no scarf" — counterproductive, made things worse)

**What would actually fix it (out of scope for HW7):**
- Compel-based prompt weighting: `(yellow scarf:1.4)` to bias attention
- A LoRA fine-tuned on a small scarf-turtle dataset
- ControlNet pose + per-region prompting

**This is intentionally surfaced in the README as a known limitation.** The character is still visually consistent across all four pages (same green/yellow turtle body, same watercolor style), which is the consistency property IP-Adapter is responsible for. The accessory miss is a separate, well-understood SDXL issue.

### Step 3.6 — Orchestrator + PDF + API (T5 + T6 + T7): smooth

Once the agents were stable, the orchestrator was straightforward. Single-pass agent generation, no edits:

- `backend/pipeline.py` — thread-safe in-memory job store, status updates emitted at each stage, output written to `outputs/{run_id}/`
- `backend/pdf_compiler.py` — ReportLab A5 layout with a cover, then image+caption per page
- `backend/api.py` — FastAPI with four endpoints (`POST /api/generate`, `GET /api/status/{id}`, `GET /api/result/{id}`, `GET /api/file/{id}/{name}`). Generation runs in a thread executor so the event loop isn't blocked.

End-to-end smoke test (`scripts/test_pipeline_e2e.py`) ran in **~30 seconds** on the H100 (4 pages, 30 inference steps each, ~2s per image at SDXL fp16).

### Step 3.7 — Gradio Frontend (T8 + T9 + T10)

Single-file `frontend/app.py` using `gradio.Blocks`. Calls the backend pipeline **in-process** (no FastAPI required for the demo — simpler one-command launch), but the FastAPI surface remains intact for grading/architectural review.

Surprises:
- Gradio's `gr.Examples` only loads values on **click** — empty form looked "pre-filled" because of placeholder text, which confused me when testing. Logged in the WORKFLOW; user-facing fix would be to set `value=` instead of `placeholder=` on each field.
- `gr.Progress(desc=...)` is the cleanest way to surface live updates while the generation thread is running. Polling every 0.5s on the in-memory `JobStatus` works.

### Step 3.8 — SSH port forwarding for remote demo

The H100 is on `140.113.30.188:7100` (custom SSH port). To open the Gradio UI in a local browser, port-forward from the local Windows box:

```powershell
ssh -L 7860:localhost:7860 -p 7100 xinyi081592@140.113.30.188
```

Browser → `http://localhost:7860`.

---

## Phase 4 — Polish

- [WORKFLOW.md](WORKFLOW.md) — this document
- [README.md](README.md) — updated with the Gradio port, SSH-tunnel instructions for remote demo, and a "Known limitations" section
- `314832015_HW7.txt` — submission file containing the public GitHub URL
- Demo screenshot of the Gradio UI after a successful generation

---

## What the Agent did vs what I did

| Done by the agent | Done by me |
|---|---|
| Wrote every line of code in `backend/`, `frontend/`, `scripts/` | Architectural judgement (IP-Adapter vs LoRA, in-process vs Celery, separate Character Agent vs reuse page 1) |
| Wrote PRD, ARCHITECTURE, TASKS, README, this WORKFLOW | All ambiguity resolution ("use my workstation, not local"; "GitHub is OK"; "I don't have API keys") |
| Wrote test scripts and the env verifier | Ran every command on the workstation; reported errors back |
| Authored all git commits and pushes | Provided the workstation, the GitHub account, and the visual quality verdicts ("this looks the same", "圍巾還是沒有", "OK go") |
| Diagnosed each runtime bug from the stack trace | Pushed back when the agent broke its own discipline (the speculative dep-fix incident in Step 3.3) |

The agent is doing the implementation grunt work; I am acting as the architect and reviewer.

---

## Tool stack used

| Layer | Tool |
|---|---|
| Agent | Claude Code (Opus 4.7) in the VS Code extension |
| Local IDE | VS Code (Windows 10) |
| Remote shell | MobaXterm SSH → `xinyi081592@140.113.30.188:7100` |
| Source control | Git + GitHub (`xinyi0815/ai-storybook-generator`) |
| LLM serving | Ollama 0.30.6 userspace (`qwen2.5:7b`, Q4_K_M, 32k ctx) |
| Diffusion stack | `diffusers 0.31.0`, `transformers 4.46.3`, `torch 2.6.0+cu124` on H100 NVL |
| Models | `stabilityai/stable-diffusion-xl-base-1.0` + `h94/IP-Adapter` (`ip-adapter_sdxl.bin`) |
| Backend | FastAPI + Uvicorn (clean API surface) |
| Frontend | Gradio Blocks (interactive demo) |
| PDF | ReportLab A5 layout |

---

## Key prompts I gave the agent (verbatim, in chronological order)

These are the prompts that meaningfully steered the project. Casual back-and-forth (e.g. "繼續", "OK") omitted.

1. `"可以看一下模組課嗎?"` — start
2. `"直接幫我規劃"` — commit to a full plan, no brainstorming
3. `"我有GITHUB，可以幫我弄好了 / 然後我不打算用本機訓練，我有工作站可以讓我用"` — switch from API-key plan to workstation plan
4. `"不是阿，你先全部理解完再給我指令，因為你上面那個我執行了你改完requirements.txt之前得指令"` — process correction; led the agent to save a persistent memory about not pushing speculative env fixes
5. `"看起來一樣?"` (after the first character/page render) — visual review handoff
6. `"你直接幫我做"` — delegate Phase 4 polish (this file is one of the outputs)

Each prompt fits on one line. The agent's value-add was decomposing them into actionable work, not interpreting elaborate spec documents.
