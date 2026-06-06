# Product Requirements Document — AI Storybook Generator

**Status:** Phase 1 (Ideation & Planning) output
**Author:** 314832015, with Claude Code as Agent collaborator
**Date:** 2026-06-06

---

## 1. Problem

Creating an illustrated children's storybook traditionally requires both writing and illustration skills. Parents, teachers, and hobbyists who want a personalized story (e.g., featuring their child as the protagonist, or addressing a specific lesson) have no easy way to produce one.

## 2. Goal

Build a single-page web app that turns a short user prompt into a fully illustrated, downloadable PDF storybook in under 5 minutes, with a visually consistent main character across all pages.

## 3. Target user

- Parent who wants a custom bedtime story for their child
- Teacher who wants a quick illustrated handout for a lesson theme
- (Implicit) Course grader evaluating an end-to-end LLM + Diffusion integration

## 4. Core features (MVP, must-have)

| ID | Feature | Acceptance criteria |
|---|---|---|
| F1 | Theme input form | User can enter: theme, main character description, age group, page count (4–6) |
| F2 | Story generation | LLM produces a coherent N-page story with per-page scene descriptions and a character sheet |
| F3 | Character reference image | Diffusion generates a single reference image of the protagonist based on the character sheet |
| F4 | Per-page illustration | Diffusion + IP-Adapter generates one illustration per page, conditioned on the reference to maintain visual consistency |
| F5 | Interactive preview | User can flip through pages in the Gradio UI before downloading |
| F6 | PDF download | One-click export of the full storybook as a PDF |

## 5. Nice-to-have (post-MVP, only if time allows)

- N1: User can regenerate a single page without redoing the whole book
- N2: Style picker (watercolor / pixel / 3D render)
- N3: TTS narration for each page
- N4: Multi-language (English / Traditional Chinese) output

## 6. Out of scope

- User accounts, persistent storage of past books
- Model fine-tuning or LoRA training (using pre-trained models only)
- Mobile app
- Editing the generated text after the fact

## 7. Tech stack rationale

| Choice | Why |
|---|---|
| Ollama for LLM | No API key required, runs on workstation, OpenAI-compatible — easy to swap for hosted later |
| SDXL for Diffusion | Best open-weights quality-per-VRAM today, well-supported in `diffusers` |
| IP-Adapter for character consistency | Pragmatic alternative to training a character LoRA; works zero-shot from a reference image |
| Gradio (not Streamlit) | Better support for image galleries and async backends |
| FastAPI backend (not bundling into Gradio) | Forces a clean API boundary, makes Workflow Log easier to write |

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| IP-Adapter quality on stylized art is uneven | Fallback: seed-locked generation with detailed character description re-injected per page |
| SDXL generation is slow (~10s/image on consumer GPU) | Cap page count at 6; surface a progress bar; consider SDXL-Turbo as fallback |
| Python 3.14 dependency conflicts on local dev box | Run everything on workstation; local machine is for editing and Gradio only |
| Workstation access intermittent | Containerize backend (Dockerfile in Phase 3) so it can be brought up anywhere |

## 9. Success metric

Grader can:
1. Clone the repo, follow README, and launch the app in <10 minutes
2. Generate a 4-page storybook end-to-end without crashes
3. See clearly which Agent did what by reading WORKFLOW.md
