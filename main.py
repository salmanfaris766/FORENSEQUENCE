# =============================================================================
# main.py
# FORENSEQUENCE - Cyber Forensics & Threat Intelligence Workstation
# PyWebview Desktop Application Entry Point (Liquid Glassmorphism Architecture)
# =============================================================================

from __future__ import annotations

import os
import sys
from pathlib import Path
import webview

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gui.web_bridge import ApiBridge


def main() -> None:
    """
    Initialize and run the FORENSEQUENCE PyWebview Workstation.
    Binds the Python ApiBridge to the HTML5/CSS3/JS Glassmorphism interface.
    """
    html_file = PROJECT_ROOT / "web" / "index.html"
    if not html_file.exists():
        raise FileNotFoundError(f"Frontend bundle missing at: {html_file}")

    # Instantiate Python API Bridge
    api = ApiBridge()

    # Create native desktop window
    window = webview.create_window(
        title="FORENSEQUENCE — Cyber Forensics & Threat Intelligence Workstation",
        url=str(html_file),
        js_api=api,
        width=1440,
        height=900,
        min_size=(1024, 640),
        background_color="#020505",
    )

    # Bind window instance to bridge for native OS file pickers
    api.set_window(window)

    # Start PyWebview event loop
    webview.start(debug=False)


if __name__ == "__main__":
    main()

