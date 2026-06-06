# Task Decomposition

Tasks ordered roughly by dependency. Each is sized to be 1–4 hours so an Agent can pick one up and run it without further breakdown.

## Phase 3 — Implementation (Days 5–11)

### Backend

- [ ] **T1. Pydantic models** — Define `GenerationRequest`, `StoryPage`, `CharacterSheet`, `StoryDocument`, `JobStatus` in `backend/models.py`.
- [ ] **T2. LLM client wrapper** — `backend/story_agent.py`: thin wrapper over the OpenAI SDK pointed at Ollama. Function `generate_story(request) -> StoryDocument`. Use a system prompt that enforces JSON output; validate with Pydantic; retry once on parse failure.
- [ ] **T3. SDXL pipeline init** — `backend/character_agent.py`: load `StableDiffusionXLPipeline` once at module import, function `generate_reference(character_sheet) -> PIL.Image`.
- [ ] **T4. IP-Adapter integration** — `backend/illustration_agent.py`: load SDXL with IP-Adapter, function `generate_page(reference_image, scene_prompt, seed) -> PIL.Image`.
- [ ] **T5. Pipeline orchestrator** — `backend/pipeline.py`: `run_generation(request, run_id, status_callback)` that calls T2 → T3 → T4 (loop) → T6, writing each output to `outputs/{run_id}/` and updating an in-memory status dict.
- [ ] **T6. PDF compiler** — `backend/pdf_compiler.py`: given `StoryDocument` and page image paths, produce `storybook.pdf` with image + caption per page.
- [ ] **T7. FastAPI routes** — `backend/api.py`: implement the four endpoints from ARCHITECTURE.md §3. Use `asyncio.create_task` to run T5 in background.

### Frontend

- [ ] **T8. Gradio form** — `frontend/app.py`: input form with the four fields from PRD F1.
- [ ] **T9. Status polling** — Hit `/api/status` every 2s, display progress bar and which stage is running.
- [ ] **T10. Result gallery** — When complete, show a `gr.Gallery` of pages with the narration as caption, and a download button for the PDF.

### Wiring

- [ ] **T11. End-to-end smoke test** — Run a full 4-page generation, fix any integration bugs.
- [ ] **T12. requirements.txt freeze** — Lock versions after smoke test passes.

## Phase 4 — Polish & docs (Days 12–17)

- [ ] **T13. README local-execution steps** — Verify by following them in a fresh venv.
- [ ] **T14. WORKFLOW.md** — Add the key prompts used in T2 (story JSON schema enforcement), the IP-Adapter debugging journey from T4, and the orchestrator design from T5.
- [ ] **T15. Demo recording** — Record a screen capture of generating a 4-page book end to end. Save as `314832015_HW7.mp4`.
- [ ] **T16. Submission TXT** — Write `314832015_HW7.txt` with the public GitHub URL.

## Open questions (resolve before T4)

- What `ip_adapter_scale` works best for children's-book art? Tune during T11. Starting guess: 0.6.
- Same seed across all pages, or per-page seed? Probably same seed for max consistency — confirm visually.
