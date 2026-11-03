"""Model libraries stay out of the backend at start: child processes import them, and
the token count imports Qwen's tokenizer at its first call (spoil-maker D46).

Qwen and OmniVoice themselves are checked by hand (spoil-maker seam 3)."""

import subprocess
import sys
from pathlib import Path


def test_importing_the_app_loads_no_model_library():
    # The backend must start in under a second; mlx-vlm alone loads mlx and transformers.
    code = (
        "import sys, backend.app; "
        "loaded = {'mlx', 'mlx_vlm', 'PIL', 'transformers', 'torch', 'omnivoice', 'pythainlp', 'numpy'} & set(sys.modules); "
        "sys.exit(f'loaded {loaded}' if loaded else 0)"
    )
    root = Path(__file__).resolve().parents[2]
    assert subprocess.run([sys.executable, "-c", code], cwd=root).returncode == 0
