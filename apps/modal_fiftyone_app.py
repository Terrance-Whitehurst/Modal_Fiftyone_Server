"""Serve the FiftyOne App on Modal with the built-in 'quickstart' dataset.

Run:
    modal serve apps/modal_fiftyone_app.py     # ephemeral preview, hot reloads
    modal deploy apps/modal_fiftyone_app.py    # persistent deployment

Modal prints a public https URL — open it to see the FiftyOne UI.
"""

import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0", "libcurl4")
    .pip_install("fiftyone")
    .env(
        {
            "FIFTYONE_DEFAULT_APP_ADDRESS": "0.0.0.0",
            "FIFTYONE_DEFAULT_APP_PORT": "5151",
        }
    )
)

app = modal.App("fiftyone-quickstart", image=image)


FIFTYONE_BOOT = """
import fiftyone as fo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset("quickstart")
session = fo.launch_app(dataset, address="0.0.0.0", port=5151, auto=False)
session.wait(-1)
"""


@app.function(
    timeout=60 * 60,
    scaledown_window=300,
    cpu=2,
    memory=4096,
    max_containers=1,
)
@modal.concurrent(max_inputs=100)
@modal.web_server(port=5151, startup_timeout=300)
def serve():
    import socket
    import subprocess
    import sys
    import time

    subprocess.Popen([sys.executable, "-u", "-c", FIFTYONE_BOOT])

    for _ in range(120):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect(("127.0.0.1", 5151))
                print("[diag] 127.0.0.1:5151 reachable — handing off to Modal proxy")
                return
            except OSError:
                pass
        time.sleep(1)

    raise RuntimeError("FiftyOne failed to bind 127.0.0.1:5151 within ~180s")
