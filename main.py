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

from gui.web_bridge import ApiBridge, ForenSequenceAPI


def on_window_closed(api: ApiBridge) -> None:
    """Handle graceful shutdown on window close to prevent WebView2 ObjectDisposedException."""
    api.shutdown()


def main() -> None:
    """
    Initialize and run the FORENSEQUENCE PyWebview Workstation.
    Binds the Python ApiBridge to the HTML5/CSS3/JS Glassmorphism interface.
    """
    html_file = PROJECT_ROOT / "web" / "index.html"
    if not html_file.exists():
        html_file = PROJECT_ROOT / "ui" / "index.html"
    if not html_file.exists():
        raise FileNotFoundError(f"Frontend bundle missing at: {html_file}")

    # Instantiate Python API Bridge
    api = ForenSequenceAPI()

    # Create native desktop window
    window = webview.create_window(
        title="FORENSEQUENCE - Digital Forensic Assistant",
        url=str(html_file),
        js_api=api,
        width=1366,
        height=820,
        min_size=(1200, 720),
        background_color="#020505",
    )

    # Bind window instance to bridge for native OS file pickers and safe_eval
    api.attach_window(window)

    # Register graceful shutdown event handler
    window.events.closed += lambda: on_window_closed(api)

    # Start PyWebview event loop
    webview.start(debug=False)


if __name__ == "__main__":
    main()


