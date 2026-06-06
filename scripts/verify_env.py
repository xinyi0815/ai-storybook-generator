"""Quick environment check for the workstation. Run after following SETUP_WORKSTATION.md."""

from __future__ import annotations

import shutil
import sys
import urllib.request
import json


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}[ OK ]{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"{RED}[FAIL]{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}[WARN]{RESET} {msg}")


def check_python() -> bool:
    major, minor = sys.version_info[:2]
    if (major, minor) in {(3, 10), (3, 11)}:
        ok(f"Python {major}.{minor}")
        return True
    fail(f"Python {major}.{minor} — need 3.10 or 3.11 (some diffusion deps lag on 3.12+)")
    return False


def check_torch_cuda() -> bool:
    try:
        import torch
    except ImportError:
        fail("torch not installed — see step 3 of SETUP_WORKSTATION.md")
        return False

    print(f"       torch {torch.__version__}")
    if not torch.cuda.is_available():
        fail("torch.cuda.is_available() is False — wrong CUDA wheel installed")
        return False

    device_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
    ok(f"CUDA available on {device_name} ({vram_gb:.1f} GB VRAM)")

    if vram_gb < 10:
        warn(f"  VRAM {vram_gb:.1f} GB is tight for SDXL — plan to enable model_cpu_offload")
    return True


def check_ollama() -> bool:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
    except Exception as e:
        fail(f"Ollama not reachable at http://localhost:11434 ({e})")
        return False

    models = [m["name"] for m in data.get("models", [])]
    if not models:
        fail("Ollama is up but no models are pulled. Run: ollama pull qwen2.5:7b")
        return False

    ok(f"Ollama reachable, models: {', '.join(models)}")
    return True


def check_diffusers() -> bool:
    try:
        import diffusers
        import transformers
        import accelerate
    except ImportError as e:
        fail(f"diffusion stack not installed: {e.name}")
        return False
    ok(f"diffusers {diffusers.__version__}, transformers {transformers.__version__}")
    return True


def check_disk() -> bool:
    free_gb = shutil.disk_usage(".").free / 1024**3
    if free_gb < 20:
        warn(f"only {free_gb:.1f} GB free in current dir — SDXL + IP-Adapter weights need ~10 GB")
    else:
        ok(f"{free_gb:.1f} GB free disk in current dir")
    return True


def main() -> int:
    print("=" * 60)
    print("AI Storybook Generator — environment check")
    print("=" * 60)
    results = [
        check_python(),
        check_torch_cuda(),
        check_ollama(),
        check_diffusers(),
        check_disk(),
    ]
    print("=" * 60)
    if all(results):
        print(f"{GREEN}All checks passed. You're ready for Phase 3.{RESET}")
        return 0
    print(f"{RED}Some checks failed — see messages above and SETUP_WORKSTATION.md.{RESET}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
