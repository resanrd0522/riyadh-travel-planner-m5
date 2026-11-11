"""Execute the notebook's default code cells locally with live construction forbidden."""

import ast
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
notebook = json.loads((ROOT / "notebooks/M5_Colab_Run.ipynb").read_text())
controls = ast.parse("".join(notebook["cells"][1]["source"]))
flags = {node.targets[0].id: ast.literal_eval(node.value) for node in controls.body if isinstance(node, ast.Assign)}
for flag in ("APPROVE_LIVE_PILOT", "APPROVE_FULL_EXPERIMENT", "UPLOAD_REPOSITORY_ZIP", "INSTALL_DEPENDENCIES", "DOWNLOAD_RUNS"):
    if flags.get(flag) is not False:
        raise ValueError(f"Unsafe notebook default: {flag}")
os.chdir(ROOT)
namespace = {"__name__": "colab_default_smoke"}
with patch("m5eval.generation.GeminiBackend", side_effect=AssertionError("Default notebook must never construct a live client")):
    for number, cell in enumerate(notebook["cells"], 1):
        if cell["cell_type"] == "code":
            exec(compile("".join(cell["source"]), f"notebook-cell-{number}", "exec"), namespace)
print("PASS: all default notebook code cells executed locally; no live backend was constructed.")
