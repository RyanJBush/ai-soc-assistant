"""Manual helper: prints expected NSL-KDD file targets.

Phase 4 keeps dataset acquisition explicit to avoid brittle URL dependencies.
"""

from pathlib import Path

RAW_DIR = Path("backend/data/raw")

if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("Place files in backend/data/raw:")
    print("- KDDTrain+.txt")
    print("- KDDTest+.txt")
