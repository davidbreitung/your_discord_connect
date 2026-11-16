"""Resolve manifest requirements with Home Assistant's installer constraints."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import homeassistant

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "custom_components/your_discord_connect/manifest.json").read_text())
constraints = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path(homeassistant.__file__).parent / "package_constraints.txt"
)
with tempfile.TemporaryDirectory() as directory:
    requirements = Path(directory) / "requirements.txt"
    requirements.write_text("\n".join(manifest["requirements"]) + "\n")
    subprocess.run(
        [
            "uv",
            "pip",
            "compile",
            str(requirements),
            "--constraint",
            str(constraints),
            "--python",
            sys.executable,
        ],
        check=True,
    )
