---
name: cc-praxis-ui
description: >
  Use when user wants to open the cc-praxis skill manager — says "open the
  installer", "open cc-praxis", "manage skills", "show installed skills",
  or "what skills are installed". Opens a local web UI for browsing,
  installing, updating, and uninstalling skills.
---

# cc-praxis UI

Launch the cc-praxis skill manager — a local web app for browsing, installing,
updating, and uninstalling skills.

## Workflow

### Step 1 — Launch the server

Run in the background so the skill returns immediately:

```bash
cc-praxis --no-browser &
```

If `cc-praxis` is not on PATH (local clone without plugin install), fall back to:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/web_installer.py" --no-browser &
```

### Step 2 — Open the browser

```bash
open http://localhost:8765
```

(On Linux: `xdg-open http://localhost:8765`)

### Step 3 — Confirm

Tell the user:

> Skill manager running at **http://localhost:8765**
>
> - **About** — overview of all skills and what they do
> - **Browse** — explore skills by bundle, search by name or description
> - **Install** — manage what's installed on this machine
>
> The server keeps running in the background. Close it with `pkill -f web_installer.py` when done.

---

## If the port is already in use

```bash
cc-praxis --port 8766 --no-browser &
open http://localhost:8766
```

---

## Skill Chaining

**Invoked by:** User directly — "open cc-praxis", "manage my skills", "launch the installer"

**Invokes:** Nothing — launches a background process and returns

**Can be invoked independently:** Yes, this is a standalone launcher
