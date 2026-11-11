"""Run the deterministic tests and rebuild derived evaluation reports."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
subprocess.run([sys.executable, "-m", "m5eval"], cwd=ROOT, check=True)
