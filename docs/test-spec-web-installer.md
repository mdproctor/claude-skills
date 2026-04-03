# Test Specification: Web Installer

**Purpose:** Defines all tests needed before and during `scripts/web_installer.py` implementation.
This is a specification document, not test code. Future Claude sessions should be able to read this
and write the actual test code without needing additional context.

**Test targets:**
- `docs/index.html` — JavaScript behaviour (chain graph, UX, context detection)
- `scripts/web_installer.py` — Python HTTP server (not yet built)

**Priority labels:**
- 🔴 MUST — required before implementation starts
- 🟡 SHOULD — write during implementation
- 🟢 NICE — after v1.0

**Test type labels:**
- `[unit]` — tests a single function in isolation
- `[integration]` — tests across function or module boundaries
- `[e2e]` — tests the full request/response cycle in a running server

---

## Section 1: Chain Graph Rendering Tests (JavaScript)

These tests cover the most fragile part of the UI. The chain graph logic lives in `docs/index.html`
inside `<script>` tags. Tests should use a DOM environment (jsdom via Vitest, or Playwright for
full browser). Each test must set up the `CHAIN` data object and a minimal DOM before calling
the function under test.

### 1.1 `getAncestors(name)` [unit]

`getAncestors` walks `CHAIN[cur].parents[0]` upward, collecting ancestors in order from
root to direct parent, protected by a `visited` Set seeded with `name`.

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1.1.1 | 🔴 Root skill returns empty array | `getAncestors('git-commit')` with `CHAIN['git-commit'].parents = []` | `[]` |
| 1.1.2 | 🔴 Single-level ancestry | `getAncestors('issue-workflow')` with `parents: ['git-commit']` and `git-commit.parents: []` | `['git-commit']` |
| 1.1.3 | 🔴 Two-level ancestry (grandparent) | `getAncestors('java-update-design')` — parents chain: `java-git-commit → git-commit → []` | `['git-commit', 'java-git-commit']` |
| 1.1.4 | 🔴 Cycle protection: A→B→A | `CHAIN = {A: {parents:['B']}, B: {parents:['A']}}`, `getAncestors('A')` | `['B']` (stops when `B` tries to revisit `A` which is in visited) |
| 1.1.5 | 🔴 Unknown skill name | `getAncestors('does-not-exist')` | `[]` (CHAIN lookup returns undefined, loop breaks immediately) |
| 1.1.6 | 🟡 Only parents[0] is followed | `CHAIN['java-code-review'].parents = ['java-dev', 'java-git-commit']` | Ancestor chain follows only `java-dev`, not `java-git-commit` |

**Implementation note:** `visited` is seeded with `name` (not just seen parents), so a direct
self-loop `A.parents = ['A']` also terminates in one step.

---

### 1.2 `buildChainRowHTML(name, data)` [unit]

Returns an HTML string. Tests should parse it via `DOMParser` or `innerHTML` and assert on
the resulting DOM structure.

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1.2.1 | 🔴 Root skill: no ⊙, no separator before current | `buildChainRowHTML('git-commit', {parents:[], children:['update-claude-md']})` | No element with class `root-sym`; first element is `.chain-name.current` containing `git-commit` |
| 1.2.2 | 🔴 Non-root skill: ⊙ present | `buildChainRowHTML('issue-workflow', ...)` with `parents:['git-commit']` | Contains `.chain-name.root-sym` with text `⊙` before any `.chain-name.clickable` |
| 1.2.3 | 🔴 Current node is bold/dark, not clickable | Any non-root skill | `.chain-name.current` has no `onclick`; has no class `clickable` |
| 1.2.4 | 🔴 Ancestor names are clickable | `buildChainRowHTML('java-update-design', ...)` — ancestors: `['git-commit','java-git-commit']` | Each ancestor is `.chain-name.clickable` with `onclick="navigateAndToggle('...')"` |
| 1.2.5 | 🔴 Ancestors ordered root→parent | Same input as 1.2.4 | `git-commit` appears before `java-git-commit` in the DOM |
| 1.2.6 | 🔴 Separator arrows between every segment | Non-root skill with children | `.chain-sep` elements containing `→` appear: after each ancestor, and after current if children exist |
| 1.2.7 | 🔴 No children: children column absent | `buildChainRowHTML('ts-security-audit', {parents:['ts-code-review'], children:[]})` | No `.chain-children-col` element |
| 1.2.8 | 🔴 Close button present | Any skill | Contains `.chain-row-close` button with `onclick="removeChainRow(event)"` |
| 1.2.9 | 🔴 rowId derived correctly | `buildChainRowHTML('ts-dev', ...)` | `rowId = 'ts-dev'`; grandchild IDs are `gc-ts-dev-0`, `gc-ts-dev-1`, etc. |
| 1.2.10 | 🟡 Non-alphanumeric chars replaced in rowId | `buildChainRowHTML('java-code-review', ...)` | `rowId = 'java-code-review'` (hyphens kept; no special chars to replace here — verify regex `/[^a-z0-9]/g` → `-`) |

---

### 1.3 Children column (`buildChildrenCol`) [unit]

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1.3.1 | 🔴 Child without grandchildren: no toggle button | `children: ['ts-security-audit']`, `CHAIN['ts-security-audit'].children = []` | One `.chain-child-line` with `.chain-name.clickable`; no `.chain-gc-toggle` |
| 1.3.2 | 🔴 Child with grandchildren: toggle button rendered | `children: ['java-code-review']`, `CHAIN['java-code-review'].children = ['java-security-audit', 'java-git-commit']` | `.chain-gc-toggle` button with text `▼` and title `Collapse`; `.chain-grandchildren` div visible |
| 1.3.3 | 🔴 Grandchildren rendered with `muted` class | Same as 1.3.2 | Each grandchild has class `chain-name muted clickable` |
| 1.3.4 | 🔴 Grandchildren expanded by default | Same as 1.3.2 | `.chain-grandchildren` has no `display:none` inline style |
| 1.3.5 | 🟡 Unknown child skill: CHAIN lookup defaults to `{children:[]}` | `children: ['nonexistent']` | No crash; child rendered as clickable but without a grandchild toggle |

**Note on cycle guard in grandchildren:** The prompt spec describes filtering grandchildren
that are in a `cycleGuard` Set (current + ancestors). The actual implementation in `index.html`
does NOT currently implement this filter — `buildChildrenCol` renders all grandchildren
unconditionally. The test at 1.3.5 covers the `|| {children:[]}` guard but not ancestor-cycle
filtering. If a cycle guard is added during implementation, add:

| 1.3.6 | 🟢 Grandchild that is also an ancestor: filtered out | `name='java-git-commit'`, ancestor `git-commit` is also a grandchild of one of its children | That grandchild name does NOT appear in `.chain-grandchildren` |

---

### 1.4 Insert position logic (above vs below) [unit]

`toggleChain` reads `skillEl.getBoundingClientRect().bottom` and inserts the `.chain-row`
above the skill element if `rect.bottom + 160 > window.innerHeight`, otherwise below.

| # | Test | Condition | Expected DOM insertion |
|---|------|-----------|------------------------|
| 1.4.1 | 🔴 Insert below when there is room | `rect.bottom = 400`, `window.innerHeight = 800` (400 + 160 = 560 ≤ 800) | `chain-row` is `skillEl.nextSibling` |
| 1.4.2 | 🔴 Insert above when near viewport bottom | `rect.bottom = 700`, `window.innerHeight = 800` (700 + 160 = 860 > 800) | `chain-row` is inserted before `skillEl` |
| 1.4.3 | 🔴 Exact threshold (== window.innerHeight): insert above | `rect.bottom + 160 = window.innerHeight + 1` | Inserts above |
| 1.4.4 | 🔴 Exact threshold (== window.innerHeight): insert below | `rect.bottom + 160 = window.innerHeight` | Inserts below |

**Test approach:** Create a minimal DOM with a parent containing the mock `skillEl`. Mock
`getBoundingClientRect` to return a controlled `bottom` value; mock `window.innerHeight`.

---

### 1.5 Toggle behaviour: open/close/one-at-a-time [unit + integration]

| # | Test | Action | Expected |
|---|------|--------|----------|
| 1.5.1 | 🔴 Open chain: `.chain-row` inserted | `toggleChain('git-commit', el)` | One `.chain-row` exists in DOM; `activeChainRow` and `activeSkillName` set |
| 1.5.2 | 🔴 Toggle same skill off: row removed | Call `toggleChain` twice on same skill | `.chain-row` removed; `activeChainRow = null`; `activeSkillName = null` |
| 1.5.3 | 🔴 Open second skill closes first | Open `git-commit`, then open `ts-dev` | Only one `.chain-row` in DOM; it belongs to `ts-dev` |
| 1.5.4 | 🔴 Close via × button | Call `removeChainRow()` | Row removed; `activeChainRow = null`; `activeSkillName = null` |
| 1.5.5 | 🔴 Unknown skill name: no row inserted | `toggleChain('nonexistent', el)` | `CHAIN['nonexistent']` is undefined; no `.chain-row` inserted |
| 1.5.6 | 🟡 Row scrolled into view after insertion | `toggleChain('git-commit', el)` | `row.scrollIntoView` called (can verify with a spy) after 30ms timeout |

---

### 1.6 Button active state management [unit]

The chain button (`#chain-btn-<name>`) gets class `active` (indigo) when chain is open,
loses it when chain is closed.

| # | Test | Action | Expected |
|---|------|--------|----------|
| 1.6.1 | 🔴 Button becomes active on open | `toggleChain('git-commit', el)` | `document.getElementById('chain-btn-git-commit')` has class `active` |
| 1.6.2 | 🔴 Button loses active on close (same skill) | Toggle open then toggle closed | `active` class removed |
| 1.6.3 | 🔴 Previous button deactivated when opening new skill | Open `git-commit`, then `ts-dev` | `chain-btn-git-commit` has no `active`; `chain-btn-ts-dev` has `active` |
| 1.6.4 | 🔴 Button deactivated on × close | Open then close via × | Button has no `active` class |
| 1.6.5 | 🟡 No crash when button element is absent | `toggleChain` called but `#chain-btn-X` not in DOM | No error thrown (`if (btn) btn.classList...` guard) |

---

### 1.7 Grandchild expand/collapse (`toggleGC`) [unit]

| # | Test | Action | Expected |
|---|------|--------|----------|
| 1.7.1 | 🔴 Initial state: grandchildren visible | Immediately after `buildChildrenCol` with grandchildren | `.chain-grandchildren` has no `display:none`; button text is `▼` |
| 1.7.2 | 🔴 Collapse: clicking ▼ hides grandchildren | `toggleGC('gc-ts-dev-0', btn)` when visible | `el.style.display = 'none'`; `btn.textContent = '▶'` |
| 1.7.3 | 🔴 Expand: clicking ▶ shows grandchildren | `toggleGC` again when hidden | `el.style.display = ''`; `btn.textContent = '▼'` |
| 1.7.4 | 🟡 Non-existent ID: no crash | `toggleGC('gc-missing', btn)` | Function returns early without error |

---

### 1.8 `navigateAndToggle(name)` [integration]

Closes the current chain row, calls `scrollToSkill(name)`, then after 400ms calls
`toggleChain(name, el)`.

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 1.8.1 | 🔴 Element exists: chain opens after delay | DOM has `#ov-ts-dev`; `navigateAndToggle('ts-dev')` called | After 400ms, `toggleChain('ts-dev', el)` is called; `.chain-row` appears |
| 1.8.2 | 🔴 Existing open chain closed first | Chain open for `git-commit`; `navigateAndToggle('ts-dev')` called | `git-commit` chain immediately removed; `ts-dev` chain opened after 400ms |
| 1.8.3 | 🔴 Missing element: no crash | No `#ov-nonexistent` in DOM; `navigateAndToggle('nonexistent')` | `el` is `null`; function exits silently |
| 1.8.4 | 🟡 `scrollToSkill` called with correct name | Spy on `scrollToSkill`; call `navigateAndToggle('ts-dev')` | `scrollToSkill` called with `'ts-dev'` |

---

### 1.9 `wireChainHovers()` injection [unit + integration]

Injects a `#chain-btn-<name>` button into every `.overview-skill-header`. Double-wire guard:
if `#chain-btn-<name>` already exists, skip.

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 1.9.1 | 🔴 Button injected once per skill | DOM with 3 `.overview-skill[id^="ov-"]` elements; call `wireChainHovers()` | 3 buttons created, one per skill header |
| 1.9.2 | 🔴 Button ID is `chain-btn-<name>` | Skill `id="ov-ts-dev"` | Button ID is `chain-btn-ts-dev` |
| 1.9.3 | 🔴 Double-wire guard works | Call `wireChainHovers()` twice | Still only 1 button per skill; second call skips existing |
| 1.9.4 | 🔴 Button click triggers `toggleChain` | Click the injected button | `toggleChain` called with correct `name` and `el`; chain row appears |
| 1.9.5 | 🔴 Button click does not bubble | Click the injected button | Parent `.overview-skill`'s own click handler not triggered |
| 1.9.6 | 🟡 Skill without `.overview-skill-header`: skipped gracefully | Element has `id="ov-x"` but no `.overview-skill-header` child | No crash; no button injected |

---

### 1.10 View-mode guard (chain only active in Browse) [integration]

The chain graph buttons are only injected into `.overview-skill` cards in the Browse view.
In About and Install views, the chain graph does not appear.

| # | Test | Action | Expected |
|---|------|--------|----------|
| 1.10.1 | 🔴 Chain buttons absent in About view | Page loads in `view-about`; inspect `.overview-skill-header` | No `.chain-btn` elements exist (Browse cards not rendered) |
| 1.10.2 | 🔴 Chain buttons present after switching to Browse | `setView('browse')`; inspect | All `#chain-btn-*` buttons injected |
| 1.10.3 | 🔴 Chain row not present in Install view | `setView('install')`; no `.chain-row` in DOM | `.chain-row` elements absent (overview list is hidden) |
| 1.10.4 | 🟡 Calling `toggleChain` while in About view | Manually call; Browse DOM not present | `CHAIN[name]` exists but `skillEl` from About view has no `.overview-skill-header` → no chain-btn, but `toggleChain` itself inserts if passed a valid element (no guard in function body) |

**Note:** The current implementation has no explicit view-mode guard inside `toggleChain`. The
protection is structural: overview skill elements only exist in the Browse DOM, and
`wireChainHovers` only runs on `.overview-skill[id^="ov-"]` elements. Test 1.10.4 documents
this implicit contract; a future explicit guard should be tested separately.

---

## Section 2: Web Installer Server Tests (Python)

`scripts/web_installer.py` does not exist yet. These tests define the contract it must satisfy.
Use Python's `unittest` or `pytest` with `TestClient`-style request simulation (e.g., via
`http.server` in a thread, or a framework like Flask/FastAPI with a test client).

### Setup conventions

```python
# Fixture: tmp_skills_dir
# Creates a temporary ~/.claude/skills/ equivalent.
# Fixture: marketplace_json
# Points to the real .claude-plugin/marketplace.json.
# Fixture: server
# Starts web_installer.py on a random port; tears down after test.
```

---

### 2.1 `GET /api/state` [unit + integration]

Returns JSON describing which skills are installed. Reads `~/.claude/skills/` (or configured path).
Each entry in `CHAIN` / marketplace is represented; installed = directory exists with a `SKILL.md`.

**Response schema:**
```json
{
  "installed": ["git-commit", "ts-dev"],
  "versions": {"git-commit": "1.0.0", "ts-dev": "1.0.0-SNAPSHOT"}
}
```
`versions` is read from each skill's `plugin.json` (or omitted if file absent).

| # | Test | Setup | Expected Response |
|---|------|-------|-------------------|
| 2.1.1 | 🔴 Empty skills dir: empty installed list | `~/.claude/skills/` exists but is empty | `{"installed": [], "versions": {}}` |
| 2.1.2 | 🔴 Skills dir does not exist | Dir absent | `{"installed": [], "versions": {}}` (no 500 error) |
| 2.1.3 | 🔴 One skill installed | `skills/git-commit/SKILL.md` exists | `"git-commit"` in `installed` |
| 2.1.4 | 🔴 Directory without SKILL.md not counted | `skills/random-dir/` but no `SKILL.md` | `"random-dir"` NOT in `installed` |
| 2.1.5 | 🔴 Version read from plugin.json | `skills/git-commit/plugin.json` contains `{"version": "1.0.0"}` | `versions["git-commit"] == "1.0.0"` |
| 2.1.6 | 🟡 Missing plugin.json: version absent or null | `skills/ts-dev/SKILL.md` exists, no `plugin.json` | `"ts-dev"` in `installed`; `versions.get("ts-dev")` is `null` or key absent |
| 2.1.7 | 🟡 Response Content-Type is `application/json` | Any valid request | `Content-Type: application/json` header present |
| 2.1.8 | 🟡 Multiple skills installed | 5 skill dirs with `SKILL.md` | All 5 names in `installed` |

---

### 2.2 `GET /api/marketplace` [unit]

Returns the parsed content of `.claude-plugin/marketplace.json`.

| # | Test | Setup | Expected Response |
|---|------|-------|-------------------|
| 2.2.1 | 🔴 Returns full marketplace JSON | File exists at known path | Body matches file content; `"name": "cc-praxis"` present |
| 2.2.2 | 🔴 File not found: 500 with error message | marketplace.json deleted | HTTP 500; body contains error description |
| 2.2.3 | 🟡 Malformed JSON: 500 | marketplace.json is not valid JSON | HTTP 500; no crash/traceback leaked to client |
| 2.2.4 | 🟡 Response Content-Type is `application/json` | Valid file | `Content-Type: application/json` |

---

### 2.3 `POST /api/install` [unit + integration]

Body: `{"skills": ["git-commit", "ts-dev"]}`. Runs:
`python3 scripts/claude-skill sync-local --skills git-commit ts-dev -y`

| # | Test | Input | Expected |
|---|------|-------|----------|
| 2.3.1 | 🔴 Valid skill names: correct command executed | `{"skills": ["git-commit"]}` | Subprocess called with `['python3', 'scripts/claude-skill', 'sync-local', '--skills', 'git-commit', '-y']` |
| 2.3.2 | 🔴 Multiple skills: all names in command | `{"skills": ["git-commit", "ts-dev"]}` | Both names appear in subprocess args in order |
| 2.3.3 | 🔴 Empty skills list: 400 Bad Request | `{"skills": []}` | HTTP 400; no subprocess spawned |
| 2.3.4 | 🔴 Missing `skills` key: 400 | `{}` | HTTP 400 |
| 2.3.5 | 🔴 Invalid skill name (path traversal): 400 | `{"skills": ["../etc/passwd"]}` | HTTP 400; no subprocess spawned |
| 2.3.6 | 🔴 Invalid skill name (shell metacharacters): 400 | `{"skills": ["git-commit; rm -rf /"]}` | HTTP 400 |
| 2.3.7 | 🔴 Subprocess success: 200 with output | Command exits 0 | HTTP 200; body contains `{"ok": true, "output": "..."}` |
| 2.3.8 | 🔴 Subprocess failure: 500 with error | Command exits non-zero | HTTP 500; body contains stderr or exit code |
| 2.3.9 | 🟡 Skill name validation: allow `[a-z0-9-]+` only | `{"skills": ["java-dev"]}` | Passes validation; command runs |
| 2.3.10 | 🟡 Non-JSON body: 400 | Plain text body | HTTP 400 |

---

### 2.4 `POST /api/uninstall` [unit + integration]

Body: `{"skills": ["ts-dev"]}`. Runs:
`python3 scripts/claude-skill uninstall ts-dev`

| # | Test | Input | Expected |
|---|------|-------|----------|
| 2.4.1 | 🔴 Valid skill name: correct command executed | `{"skills": ["ts-dev"]}` | Subprocess args include `['...claude-skill', 'uninstall', 'ts-dev']` |
| 2.4.2 | 🔴 Multiple skills: each name included | `{"skills": ["ts-dev", "ts-code-review"]}` | Both names in subprocess args |
| 2.4.3 | 🔴 Empty list: 400 | `{"skills": []}` | HTTP 400 |
| 2.4.4 | 🔴 Invalid name (path traversal): 400 | `{"skills": ["../../secrets"]}` | HTTP 400 |
| 2.4.5 | 🔴 Subprocess success: 200 | Command exits 0 | HTTP 200; `{"ok": true}` |
| 2.4.6 | 🔴 Subprocess failure: 500 | Command exits non-zero | HTTP 500; error detail in body |
| 2.4.7 | 🟡 Non-JSON body: 400 | Plain text | HTTP 400 |

---

### 2.5 `POST /api/update` [unit + integration]

Body: `{}`. Runs: `python3 scripts/claude-skill sync-local --all -y`

| # | Test | Input | Expected |
|---|------|-------|----------|
| 2.5.1 | 🔴 Correct command executed | `{}` | Subprocess called with `['...claude-skill', 'sync-local', '--all', '-y']` |
| 2.5.2 | 🔴 Subprocess success: 200 | Command exits 0 | HTTP 200; `{"ok": true}` |
| 2.5.3 | 🔴 Subprocess failure: 500 | Command exits non-zero | HTTP 500 |
| 2.5.4 | 🟡 Body content ignored | `{"extra": "field"}` | Command runs normally; no 400 |

---

### 2.6 Version detection [unit]

Compares the installed skill's `plugin.json` version against the marketplace version.
Used by `/api/state` to flag outdated skills.

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 2.6.1 | 🔴 Installed version matches marketplace: not outdated | `installed: "1.0.0"`, `marketplace: "1.0.0"` | Skill not in `outdated` list |
| 2.6.2 | 🔴 Installed version older than marketplace: outdated | `installed: "1.0.0"`, `marketplace: "1.0.1"` | Skill in `outdated` list |
| 2.6.3 | 🔴 Installed version newer: not outdated | `installed: "1.0.1"`, `marketplace: "1.0.0"` | Not outdated |
| 2.6.4 | 🔴 SNAPSHOT version comparison | `installed: "1.0.0-SNAPSHOT"`, `marketplace: "1.0.0"` | Define and test expected behavior (outdated or equal — document the decision) |
| 2.6.5 | 🟡 Missing plugin.json: skill treated as unknown version | No `plugin.json` in skill dir | Not flagged as outdated (version unknown, not stale) |
| 2.6.6 | 🟡 Skill not in marketplace: ignored | Installed skill name not in `plugins` list | No crash; skill listed as installed but no version comparison |

**Decision required before writing test 2.6.4:** Decide whether `1.0.0-SNAPSHOT` is considered
older than, equal to, or newer than `1.0.0`. Document the rule in `web_installer.py`.

---

### 2.7 Static file serving [unit + integration]

`GET /` serves `docs/index.html`.

| # | Test | Request | Expected |
|---|------|---------|----------|
| 2.7.1 | 🔴 Root path serves index.html | `GET /` | HTTP 200; `Content-Type: text/html`; body contains `<title>cc-praxis` |
| 2.7.2 | 🔴 Unknown path: 404 | `GET /nonexistent` | HTTP 404 |
| 2.7.3 | 🟡 index.html not found: 500 | `docs/index.html` deleted | HTTP 500 or 404 with clear error |
| 2.7.4 | 🟡 Path traversal rejected | `GET /../../../etc/passwd` | HTTP 400 or 404; file not served |

---

### 2.8 Context detection (integration)

The server runs on localhost, so `isLocal` in `index.html` should evaluate to `true` when
served by `web_installer.py`. This is verified via the UI behaviour of the served page.

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 2.8.1 | 🟡 Install tab visible when served locally | Browser opens `http://localhost:<port>/` | `#tab-install` is not hidden (`display` is not `none`) |
| 2.8.2 | 🟡 Install tab hidden on github.io | Navigate to `https://mdproctor.github.io/...` | `#tab-install` has `display: none` (covered by CSS `.is-web` rule) |

**Test approach for 2.8.1:** Use Playwright or Selenium to open the locally-served page and
assert the computed style of `#tab-install`.

---

## Section 3: Web UX Behaviour Tests (JavaScript)

### 3.1 `isLocal` detection [unit]

`isLocal` is computed as `['localhost', '127.0.0.1', ''].includes(location.hostname)`.

| # | Test | `location.hostname` | Expected `isLocal` |
|---|------|--------------------|--------------------|
| 3.1.1 | 🔴 localhost | `'localhost'` | `true` |
| 3.1.2 | 🔴 127.0.0.1 | `'127.0.0.1'` | `true` |
| 3.1.3 | 🔴 file:// protocol (empty hostname) | `''` | `true` |
| 3.1.4 | 🔴 GitHub Pages domain | `'mdproctor.github.io'` | `false` |
| 3.1.5 | 🟡 Custom domain | `'example.com'` | `false` |

**Test approach:** These must mock `window.location.hostname` before the script runs.
Use a jsdom environment and set `Object.defineProperty(window, 'location', ...)`.

---

### 3.2 Install tab hidden when `!isLocal` [integration]

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 3.2.1 | 🔴 `is-web` class applied to body when `!isLocal` | `isLocal = false` | `document.body.classList.contains('is-web')` is `true` |
| 3.2.2 | 🔴 `#tab-install` has `display:none` | `is-web` class on body | Computed style of `#tab-install` is `display: none` (from CSS `.is-web #tab-install { display: none !important }`) |
| 3.2.3 | 🔴 `is-web` class NOT applied when `isLocal` | `isLocal = true` | `document.body.classList.contains('is-web')` is `false` |

---

### 3.3 CTA promoted to top of About when `!isLocal` [integration]

When `isLocal = false`, the script moves `#about-cta` to be the first child of its container.

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 3.3.1 | 🔴 CTA is first child when web | `isLocal = false` | `#about-cta` is `container.firstChild` (or first element child) |
| 3.3.2 | 🔴 CTA not moved when local | `isLocal = true` | `#about-cta` remains in its original DOM position (after hero content) |

---

### 3.4 `setView('install')` redirects to `about` when `!isLocal` [unit]

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 3.4.1 | 🔴 Install redirected to about on web | `isLocal = false`; call `setView('install')` | `document.body.classList.contains('view-about')` is `true`; NOT `view-install` |
| 3.4.2 | 🔴 Install works normally when local | `isLocal = true`; call `setView('install')` | `document.body.classList.contains('view-install')` is `true` |
| 3.4.3 | 🟡 Tab active state correct after redirect | `isLocal = false`; `setView('install')` | `#tab-about` has class `active`; `#tab-install` does not |

---

### 3.5 About → Browse: all bundles auto-expand [integration]

When `setView('browse')` is called, all bundle elements in `BUNDLE_IDS` get class `open`.

| # | Test | Setup | Expected |
|---|------|-------|----------|
| 3.5.1 | 🔴 All bundles open when switching to browse | Start from `view-about` with all bundles closed; call `setView('browse')` | All 5 bundle elements (`b-core`, `b-principles`, `b-java`, `b-ts`, `b-individual`) have class `open` |
| 3.5.2 | 🟡 Switching to About does not auto-expand | `setView('about')` | Bundle `open` states unchanged |

---

### 3.6 Search (`filterSkills`) [unit]

| # | Test | Query | Expected |
|---|------|-------|----------|
| 3.6.1 | 🔴 Empty query shows all skills | `filterSkills('')` | No `.skill-row` or `.overview-skill` has class `hidden`; no bundle has class `all-hidden` |
| 3.6.2 | 🔴 Query matching skill name | `filterSkills('ts-dev')` in Browse view | `.overview-skill` for `ts-dev` visible; unrelated skills hidden |
| 3.6.3 | 🔴 Query matching description | `filterSkills('strict mode')` | Skills whose `.overview-desc` contains `strict mode` are visible |
| 3.6.4 | 🔴 No matches: bundle hidden | `filterSkills('zzznomatch')` | All `.bundle` elements have class `all-hidden` |
| 3.6.5 | 🔴 Partial matches show bundle open | `filterSkills('ts')` | Bundles with matching skills get class `open` |
| 3.6.6 | 🟡 Search is case-insensitive | `filterSkills('TS-DEV')` | `ts-dev` card is visible |
| 3.6.7 | 🟡 In Install view: filters `.skill-row` not `.overview-skill` | Set body to `view-install`; `filterSkills('git')` | Only `.skill-row` elements are filtered; `.overview-skill` unaffected |

**Note:** Test 3.6.7 relies on `isOverview = document.body.classList.contains('view-browse')` logic.
In Install view, `isOverview` is `false`, so `.skill-row` elements are filtered instead.

---

### 3.7 Collapse / Expand All (`toggleAll`) [unit]

| # | Test | Starting state | Action | Expected |
|---|------|---------------|--------|----------|
| 3.7.1 | 🔴 Collapse all when any open | At least one bundle has `open` | `toggleAll()` | All 5 bundles lose `open` class |
| 3.7.2 | 🔴 Expand all when all closed | No bundle has `open` | `toggleAll()` | All 5 bundles gain `open` class |
| 3.7.3 | 🔴 Button label updates: collapse → expand | All closed | `toggleAll()` | `#btn-toggle-all` text becomes `⊟ Collapse All` |
| 3.7.4 | 🔴 Button label updates: expand → collapse | All open, then `toggleAll()` | | `#btn-toggle-all` text becomes `⊞ Expand All` |
| 3.7.5 | 🟡 One bundle open, rest closed: toggleAll collapses | One `open`, four closed | `toggleAll()` | All closed (any-open logic: `anyOpen` is `true`) |

---

## Section 4: Data Integrity Tests

### 4.1 Existing coverage in `tests/test_mockup_chaining.py`

| Test | What it verifies | Status |
|------|-----------------|--------|
| `test_mockup_has_overview_card_for_every_skill` | All 33 skills have overview cards in `docs/web-installer-mockup.html` | Covered |
| `test_mockup_chains_match_ground_truth` | Overview card `scrollToSkill` tags match `CHAINING_TRUTH` | Covered |
| `test_ground_truth_is_bidirectional` | `CHAINING_TRUTH` is internally consistent (chains_to ↔ invoked_by) | Covered |
| `test_ground_truth_references_known_skills_only` | No typos or unknown skill names in `CHAINING_TRUTH` | Covered |
| `test_skillmd_chains_roughly_match_truth` | `SKILL.md` chaining sections haven't drifted from `CHAINING_TRUTH` | Covered |

### 4.2 Identified gap: CHAIN data in `index.html` not validated against `CHAINING_TRUTH`

**GAP — not currently tested.** `docs/index.html` contains a hardcoded `CHAIN` object
(lines ~1520–1556) that defines `{parents: [...], children: [...]}` for each skill. This
data is used by the chain graph renderer. It can drift from `CHAINING_TRUTH` in
`test_mockup_chaining.py` without any test catching it.

#### 4.2.1 Test: CHAIN parents in index.html match CHAINING_TRUTH invoked_by [unit] 🔴

**Name:** `test_chain_js_parents_match_chaining_truth`

**File:** `tests/test_chain_data_drift.py`

**What it tests:** For every skill in `CHAIN` (parsed from `index.html`), the set of
`parents` should correspond to the skill's `invoked_by` + `builds_on` entries in
`CHAINING_TRUTH`. Direction note: `CHAIN.parents` uses `invoked_by` semantics
(skills that invoke this one).

**Inputs:** Parse the `CHAIN = {...}` literal from `docs/index.html` using a regex or
`ast.literal_eval` after extraction. Load `CHAINING_TRUTH` from the existing test file
(import or duplicate).

**Expected:** For each skill `S`:
- `set(CHAIN[S]['parents'])` == `set(CHAINING_TRUTH[S]['invoked_by'])`
  with the following documented exceptions (review these):
  - `java-code-review.parents` includes `java-git-commit` but `CHAINING_TRUTH['java-code-review']['invoked_by']`
    also includes `java-git-commit` — should match.
  - Any intentional asymmetry (e.g. `git-commit` as a terminal suggestion) must be explicitly
    documented in the test's `EXEMPT` set, mirroring the bidirectionality exemption in the
    existing tests.

**Failure message:** `"[{skill}] CHAIN.parents has {diff} not in CHAINING_TRUTH.invoked_by — update CHAIN in index.html"`

#### 4.2.2 Test: CHAIN children in index.html match CHAINING_TRUTH chains_to [unit] 🔴

**Name:** `test_chain_js_children_match_chaining_truth`

**Same file:** `tests/test_chain_data_drift.py`

**What it tests:** For every skill `S`, `set(CHAIN[S]['children'])` should equal
`set(CHAINING_TRUTH[S]['chains_to'])`.

**Expected:** Exact match. Failures indicate `index.html`'s `CHAIN` object has drifted
from the Python ground truth.

**Note:** `CHAIN` uses `children` for what `CHAINING_TRUTH` calls `chains_to`.
The mapping is: `CHAIN[S].children == CHAINING_TRUTH[S].chains_to`.

#### 4.2.3 Test: No skills in CHAINING_TRUTH are missing from CHAIN [unit] 🟡

**Name:** `test_chain_js_has_all_skills`

**What it tests:** Every skill name in `ALL_SKILLS` (from the existing test file) appears
as a key in the `CHAIN` object parsed from `index.html`.

**Expected:** `set(CHAIN.keys()) == ALL_SKILLS`

#### 4.2.4 Implementation note: parsing CHAIN from index.html

The `CHAIN` object in `index.html` is written as a JavaScript object literal, not JSON.
Recommended parse strategy:

```python
import re, ast

def parse_chain_from_html(html_path):
    html = Path(html_path).read_text()
    # Extract the CHAIN = {...}; block
    m = re.search(r'const CHAIN\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not m:
        raise ValueError("CHAIN not found in index.html")
    raw = m.group(1)
    # Convert JS object to Python: replace bare keys with quoted keys
    raw = re.sub(r"'([^']+)':", r'"\1":', raw)  # single-quoted keys
    raw = re.sub(r'(\w[\w-]*):', r'"\1":', raw)   # bare keys (careful with regex)
    # Also convert array brackets and values
    return json.loads(raw)
```

**Warning:** The bare-key regex approach is fragile. Prefer extracting the block and using
a proper JS parser (e.g., `js2py` or `node -e "JSON.stringify(...)"`), or maintain the
`CHAIN` data as a separate JSON file imported by both `index.html` and the Python tests.

---

## Appendix: Test File Layout

```
tests/
  test_mockup_chaining.py          # Existing: data integrity for overview cards
  test_chain_data_drift.py         # New (Section 4.2): CHAIN JS object vs CHAINING_TRUTH
  test_web_installer_server.py     # New (Section 2): web_installer.py server API
  js/                              # New (Section 1, 3): JavaScript unit tests
    chain-graph.test.js            # Section 1: getAncestors, buildChainRowHTML, etc.
    ux-behaviour.test.js           # Section 3: isLocal, setView, filterSkills, toggleAll
    setup.js                       # jsdom setup + CHAIN/DEPS data fixtures
```

**JavaScript test runner:** Vitest (preferred) or Jest with jsdom. The `docs/index.html`
script block should be extracted into a testable module, OR the tests should inject it
into a jsdom document and call functions directly via `window.*`.

**Python test runner:** pytest. Server tests use a subprocess to start `web_installer.py`
and `requests` to call it, or mock the subprocess layer for unit tests.
