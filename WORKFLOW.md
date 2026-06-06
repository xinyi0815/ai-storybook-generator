# Agent Collaboration Workflow Log

This file documents the human + Agent development process for HW7. Entries are appended as the project progresses.

---

## Phase 1 — Ideation & Planning (2026-06-06)

### Setup

- **Agent used:** Claude Code (Opus 4.7, 1M context) running in VS Code
- **Working directory:** `c:/Users/xinyi/Desktop/雜項misc/模組課/`

### Key prompt 1 — Project ideation

> "可以看一下模組課嗎?"

Agent read the assignment PDF, summarized the requirements, then asked whether to brainstorm topics or go straight to a plan. After confirming "直接幫我規劃", it proposed three project shapes and recommended **AI Interactive Storybook Generator** because:

- Hits both required tech families (LLM + Diffusion) in one project
- Character consistency across pages is a real technical challenge → produces meaningful Workflow Log content
- Visually demoable → good for the required demo recording

### Key prompt 2 — Constraint refinement

> "我有GITHUB...沒有 OpenRouter / Replicate API key...我不打算用本機訓練，我有工作站可以讓我用"

Agent revised the plan:
- LLM → Ollama (workstation, no API key)
- Diffusion → SDXL + IP-Adapter on workstation (no API key, no Replicate)
- Backup LLM → Big Pickle (free, mentioned in assignment spec)

### Phase 1 deliverables

- [docs/PRD.md](docs/PRD.md) — Product Requirements
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design
- [docs/TASKS.md](docs/TASKS.md) — Decomposed task list

---

## Phase 2 — Architecture Design (2026-06-06)

### Design decisions made with Agent

1. **Separate Character Agent from Illustration Agent.** Initial instinct was to use the first page's image as the IP-Adapter reference. Agent pushed back: generating a dedicated reference image with `T-pose / neutral background` gives IP-Adapter a cleaner signal than a busy scene. Adopted.

2. **One LLM call, not two.** Considered splitting "story writing" and "scene-prompt writing" into two LLM calls. Agent argued one call is better because the same model has full context of tone/style, ensuring scene prompts match the narration's mood. Adopted.

3. **In-process async, no Celery.** For an MVP demo, `asyncio.create_task` is enough. Adding Redis/Celery would burn a day for zero demo benefit. Adopted.

4. **Rejected:** LoRA fine-tuning of a character. Time-box: 17 days. Training + dataset curation alone could eat a week. IP-Adapter is the pragmatic choice.

---

## Phase 3 — Implementation (to be filled in as work proceeds)

_Append entries below as each task in TASKS.md completes. Each entry should answer: what prompt did I give? what did the Agent generate? what didn't work and how did we fix it?_

### T2 — LLM client wrapper (TBD)

### T4 — IP-Adapter integration (TBD)

…

---

## Phase 4 — Polish (to be filled in)
