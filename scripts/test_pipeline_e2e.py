"""End-to-end smoke test: run the orchestrator without the API.

Generates a full storybook (story + reference + pages + PDF) and prints the
output directory. Use this to verify T1..T6 work together before bringing up
the FastAPI server.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.models import AgeGroup, GenerationRequest
from backend.pipeline import get_status, register_job, run_generation


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> int:
    req = GenerationRequest(
        theme="a brave little turtle who learns to swim in the deep sea",
        main_character="a small green sea turtle named Momo with a bright yellow scarf",
        age_group=AgeGroup.EARLY,
        num_pages=4,
    )
    run_id = register_job(req)
    print(f"run_id: {run_id}")
    t0 = time.time()
    run_generation(req, run_id)
    dt = time.time() - t0

    status = get_status(run_id)
    print(f"final status: {status.status.value if status else 'unknown'}")
    if status and status.error:
        print(f"error: {status.error}")
        return 1
    print(f"total: {dt:.1f}s")
    print(f"outputs: outputs/{run_id}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
