# Workstation Setup Guide

Step-by-step environment setup for the GPU workstation where SDXL + IP-Adapter inference will run. Tested for Linux workstations; Windows notes inline.

---

## 0. Pre-flight checks

SSH in and run:

```bash
nvidia-smi                  # confirm GPU is visible, note CUDA version
python3 --version           # need 3.10 or 3.11 (NOT 3.12+)
df -h ~                     # need ~30 GB free for model weights
free -h                     # need ~16 GB RAM for SDXL load
```

**If `python3 --version` shows 3.12 or 3.14**, install 3.11 via `pyenv` or `conda`:

```bash
# Option A: conda (recommended on shared workstations)
conda create -n storybook python=3.11 -y
conda activate storybook

# Option B: pyenv
pyenv install 3.11.9
pyenv local 3.11.9
```

---

## 1. Clone the repo

```bash
git clone https://github.com/xinyi0815/ai-storybook-generator.git
cd ai-storybook-generator
```

---

## 2. Python environment

```bash
# If you didn't use conda above:
python3.11 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

pip install --upgrade pip
```

---

## 3. Install PyTorch (with the right CUDA wheel)

Check the CUDA driver version reported by `nvidia-smi`, then install the matching wheel. Don't rely on `requirements.txt` for this — pick the right index URL by hand:

```bash
# CUDA 12.1 (most common on recent workstations)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8 (older driver)
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

Verify:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Should print something like `2.4.0+cu121 True NVIDIA RTX A6000`. If `False`, stop here — the wrong wheel is installed.

---

## 4. Install the rest of the dependencies

```bash
pip install -r requirements.txt
```

This pulls `diffusers`, `transformers`, `accelerate`, `fastapi`, `gradio`, `reportlab`, etc.

---

## 5. Install Ollama and pull a model

Linux:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Windows: download installer from https://ollama.com/download

Start Ollama (Linux: usually starts as systemd service; if not, run `ollama serve` in a separate terminal), then pull a model:

```bash
ollama pull qwen2.5:7b           # ~4.7 GB, good balance
# or, if VRAM is tight:
ollama pull qwen2.5:3b           # ~2 GB
# or, if you have lots of VRAM and want better quality:
ollama pull llama3.1:8b          # ~4.7 GB
```

Verify Ollama is reachable:

```bash
curl http://localhost:11434/api/tags
```

Should return JSON listing the model(s) you pulled.

---

## 6. Pre-download SDXL + IP-Adapter weights

These will download on first run anyway, but doing it now avoids a 5-minute pause during the first end-to-end test:

```bash
python scripts/prefetch_weights.py
```

This downloads:
- `stabilityai/stable-diffusion-xl-base-1.0` (~7 GB)
- `h94/IP-Adapter` SDXL weights (~1 GB)

Models are cached in `~/.cache/huggingface/` by default.

---

## 7. Configure

```bash
cp configs/settings.example.toml configs/settings.toml
```

Open `configs/settings.toml` and confirm:
- `[llm].model` matches what you pulled in step 5
- `[diffusion].device = "cuda"`
- `[diffusion].ip_adapter_scale` — start at `0.6`, tune later

---

## 8. Verify the full environment

```bash
python scripts/verify_env.py
```

Expected output: a green checkmark for each of (Python version, CUDA, Ollama reachable, model present, diffusers loadable).

Once all green, you're ready for Phase 3 implementation.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `torch.cuda.is_available() == False` | Wrong CUDA wheel | Reinstall torch with the correct `--index-url` |
| Ollama `connection refused` | Service not running | `ollama serve &` or check `systemctl status ollama` |
| `diffusers` complains about `xformers` | Optional dep mismatch | Safe to ignore for now, or `pip install xformers` |
| OOM on SDXL load | <12 GB VRAM | Use `pipe.enable_model_cpu_offload()` in `character_agent.py` |
| `huggingface_hub` 401 on IP-Adapter | Token needed for some repos | `huggingface-cli login` |
