"""Add scripts/ to sys.path so vector_drift_scheduler can import vector_drift_check."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / "scripts"))
