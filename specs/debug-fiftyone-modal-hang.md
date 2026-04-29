# Debug Prompt: FiftyOne-on-Modal URL hangs

**Task:** Diagnose why a FiftyOne-on-Modal app hangs when its public URL is opened in a browser.

## Context

I'm trying to serve the FiftyOne UI on Modal using `@modal.web_server`. The repo is at `/Users/twhitehurst3/Documents/twhitehurst3/Studying/Projects/Fiftyone_Modal_Server/`. The Modal app is `apps/modal_fiftyone_app.py`. Modal version is 1.4.2, FiftyOne 1.14.2, Python 3.11.

Current state:

- `modal serve apps/modal_fiftyone_app.py` is running in the background (output at `/private/tmp/claude-501/-Users-twhitehurst3-Documents-twhitehurst3-Studying-Projects-Fiftyone-Modal-Server/18e4c6ee-56e4-4000-97f1-37781b3d0e84/tasks/bxtk18izg.output`).
- Public URL: `https://terrance-8862--fiftyone-quickstart-serve-dev.modal.run`
- Inside the container, my diagnostic confirms `127.0.0.1:5151` is reachable and the FiftyOne `Session` is alive (`session=Dataset: quickstart`).
- I configured `max_containers=1` + `@modal.concurrent(max_inputs=100)` so there's a single pinned container.
- Env vars set: `FIFTYONE_DEFAULT_APP_ADDRESS=0.0.0.0`, `FIFTYONE_DEFAULT_APP_PORT=5151`.
- Function blocks on `threading.Event().wait()` so it can't return early.

## Symptom

Browser sits at "loading" indefinitely on the modal.run URL. No response, no FiftyOne UI. Container is up and FiftyOne port is internally reachable.

## What I've already ruled out

- It's not a function-early-return issue (we tried `session.wait(-1)` first; switched to `threading.Event().wait()` after seeing the Welcome banner reprint on every request).
- It's not multi-container thrash (`max_containers=1` plus `@modal.concurrent` made the diag print only once).
- The FiftyOne server IS bound on `127.0.0.1:5151` inside the container (TCP connect from Python succeeds).

## Hypotheses worth testing

1. **WebSocket/HTTP protocol mismatch:** FiftyOne's UI uses websockets. Modal's `@modal.web_server` proxy may not pass WS upgrades cleanly to the inner port, OR the FiftyOne backend on `127.0.0.1:5151` is HTTP-only while the frontend assets are served from a different port. Check what FiftyOne v1.14.2 actually serves on 5151 — is it the React UI bundle + API, or just the API server?
2. **CORS / Origin check:** FiftyOne may reject requests with a `Host:` header that isn't `localhost:5151`. The Modal proxy passes the public hostname through.
3. **`remote=True` semantics:** When `remote=True` is passed to `fo.launch_app`, FiftyOne assumes SSH tunneling and may not actually serve the static UI on the bound port — only the data API. Confirm by `curl http://127.0.0.1:5151/` from inside the container and check what it returns (HTML? JSON? 404?).
4. **Modal `web_server` requires the inner server to bind on `0.0.0.0` (not `127.0.0.1`):** despite my assumption that Modal's proxy connects via loopback, it may actually need `0.0.0.0` binding. Verify against current Modal docs.

## What I want you to do

1. Read `apps/modal_fiftyone_app.py` and the tail of the `modal serve` log file.
2. Open Modal's `@modal.web_server` docs and confirm whether it requires `0.0.0.0` binding and whether it transparently forwards WebSocket upgrades.
3. Open the FiftyOne `launch_app(remote=True)` docs/source and confirm what gets served on the bound port — UI assets, API only, or both.
4. Add a `subprocess.run(["curl", "-sv", "http://127.0.0.1:5151/"], capture_output=True)` step into the `serve()` function (after the existing diag) so we can see the raw HTTP response from inside the container on the next hot-reload.
5. From the curl response, diagnose: is FiftyOne not serving the UI at `/`, is it returning a redirect Modal can't follow, or is it a WS-only endpoint?
6. Propose and implement the minimal fix.

Report findings concisely (under 300 words) and show the diff you applied.
