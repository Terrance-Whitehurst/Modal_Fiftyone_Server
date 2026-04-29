# FiftyOne on Modal

Minimal Modal app that boots the FiftyOne UI with the built-in `quickstart` dataset (200 COCO images with predictions, ~23 MB).

## One-time setup

```bash
uv sync                    # creates .venv and installs modal
uv run modal setup         # interactive — auths your Modal account in the browser
```

## Run it

```bash
uv run modal serve apps/modal_fiftyone_app.py
```

Modal prints a public `https://...modal.run` URL. First boot takes ~30–60s (image build + dataset download); subsequent requests are warm.

For a persistent deployment:

```bash
uv run modal deploy apps/modal_fiftyone_app.py
```
