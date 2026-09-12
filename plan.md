# Build Plan: Test-Case Triage Coach

## Ground rules for the agent (read before every phase)

- Follow the file structure below exactly. Do not create files, folders, or dependencies that aren't listed in the current phase.
- Do not invent AWS resource names, ARNs, region, account ID, or API keys. Where a value is needed (table name, model ID, region), read it from `backend/src/triage_coach/config.py` / `.env` — if it isn't defined yet, stop and ask instead of guessing.
- Do not call real AWS services (Bedrock, DynamoDB) from unit tests. Every AWS client must be mockable; unit tests use mocks, not live calls.
- Do not proceed to the next phase until the "Definition of done" for the current phase is met. If a test fails, fix it before moving on — do not comment it out or skip it.
- Do not touch `frontend/` before Phase 8. Do not touch AWS deploy scripts before Phase 6.
- If a phase references a function/class from an earlier phase, use the exact name given here — do not rename.
- Keep node functions in `graph/nodes.py` pure: input state in, partial state out. No `boto3`, no `print`-based side effects, no direct DynamoDB/Bedrock calls inside a node — those go through `clients/`.

---

## Phase 0 — Repo scaffolding

**Goal**: Create the folder/file skeleton with empty stubs. No logic yet.

**Create**:
```
test-case-triage-coach/
├── README.md
├── ARCHITECTURE.md
├── .env.example
├── .gitignore
├── Makefile
├── backend/
│   ├── pyproject.toml
│   ├── template.yaml
│   ├── src/triage_coach/{__init__.py, handler.py, config.py}
│   ├── src/triage_coach/graph/{__init__.py, state.py, nodes.py, routing.py, build_graph.py, sandbox.py}
│   ├── src/triage_coach/clients/{bedrock_client.py, dynamo_client.py}
│   ├── src/triage_coach/problems/sample_problems.py
│   └── tests/unit/{test_sandbox.py, test_routing.py, test_classify_failure.py}
│   └── tests/integration/test_graph_end_to_end.py
├── infra/dynamodb-table.json
└── scripts/{deploy_backend.sh, deploy_frontend.sh}
```

**Definition of done**: every file above exists (can be empty or have a `# TODO` placeholder). `pyproject.toml` lists deps: `langgraph`, `boto3`, `pytest`, `moto`. Nothing executes yet.

---

## Phase 1 — Sample problems + state schema

**Files**: `problems/sample_problems.py`, `graph/state.py`

**Task**: Define 2 canned problems in `sample_problems.py`, each as a dict with: `problem_id`, `prompt` (text), `starter_code`, `test_cases` (list of `{input, expected_output}`), at least one with an off-by-one bug variant and one with a wrong-data-structure bug variant, so both failure classes are demonstrable.

Define `state.py` as a `TypedDict` named `TriageState` with exactly these fields: `session_id: str`, `problem_id: str`, `code: str`, `test_results: list`, `failure_type: str | None`, `hint_tier: int`, `attempt_count: int`, `hint_text: str | None`, `resolved: bool`.

**Definition of done**: `python -c "from triage_coach.problems.sample_problems import PROBLEMS; print(len(PROBLEMS))"` runs without error and prints 2. `TriageState` importable with no circular imports.

---

## Phase 2 — Sandbox

**File**: `graph/sandbox.py`

**Task**: Implement `run_against_tests(code: str, test_cases: list) -> list[dict]`. It must:
- Execute `code` in a restricted namespace (no `__import__`, no `os`, no `open`, no network) — use a minimal allowed-builtins dict, do not use `eval`/`exec` with the full global namespace.
- Enforce a wall-clock timeout per test case (use `signal.alarm` or a subprocess with `timeout=`) — pick one approach and use it consistently, don't mix.
- Return a list of `{test_case, passed: bool, actual_output, error: str | None}` — never let an exception propagate out of this function.

**Tests**: `test_sandbox.py` covers: correct code passes all tests, code with a runtime error is caught and reported (not raised), code that infinite-loops is killed by the timeout, code trying `import os` is blocked.

**Definition of done**: `pytest backend/tests/unit/test_sandbox.py -v` — all pass.

---

## Phase 3 — Nodes (pure functions, no AWS)

**File**: `graph/nodes.py`

**Task**: Implement these functions, each taking `TriageState` and returning a partial state update:
- `run_tests_node(state)` → calls `sandbox.run_against_tests`, sets `test_results`
- `classify_failure_node(state)` → given `test_results`, sets `failure_type` to one of `"off_by_one" | "wrong_data_structure" | "edge_case" | "passed" | "other"`. This function may call the model (via `clients/bedrock_client.py`, injected as a parameter with a default, so it can be mocked in tests) — but do not hardcode the classification logic to only string-match; use the model for ambiguous cases and simple pattern checks only for the obvious ones (e.g. `IndexError` → likely off-by-one).
- `generate_hint_node(state)` → produces `hint_text` at the tier in `state["hint_tier"]` (0 = conceptual nudge, 1 = specific pointer to the failing logic, 2 = full patch). Never generate a tier-2 patch if `hint_tier < 2`.
- `escalate_check_node(state)` → increments `hint_tier` by 1 if called (this node only runs when the user reports still stuck — do not auto-increment elsewhere).

**Tests**: `test_classify_failure.py` — mock the Bedrock client, assert correct routing for an off-by-one test-result fixture and a wrong-data-structure fixture.

**Definition of done**: `pytest backend/tests/unit/test_classify_failure.py -v` passes with the mocked client, no real AWS call made.

---

## Phase 4 — Routing + graph assembly

**Files**: `graph/routing.py`, `graph/build_graph.py`

**Task**: `routing.py` holds conditional-edge functions only, e.g. `route_after_tests(state) -> Literal["classify_failure", "resolved"]` and `route_after_classification(state) -> Literal["generate_hint", "end"]`. `build_graph.py` imports nodes + routing functions and wires a `StateGraph(TriageState)` — this file contains no logic of its own, only `.add_node` / `.add_conditional_edges` calls.

**Definition of done**: `build_graph.py` compiles (`graph.compile()`) without error when imported.

---

## Phase 5 — Local integration test (still no AWS)

**File**: `tests/integration/test_graph_end_to_end.py`

**Task**: Run the compiled graph against both sample problems end-to-end with mocked Bedrock responses. Assert: buggy code produces a non-empty `failure_type` and `hint_text`; correct code produces `resolved: True` with no hint generated.

**Definition of done**: `pytest backend/tests/integration -v` passes. Do not proceed to Phase 6 until this is green — this is the point where the actual agent logic is proven correct, before any AWS is involved.

---

## Phase 6 — AWS clients (mockable) + config

**Files**: `clients/bedrock_client.py`, `clients/dynamo_client.py`, `config.py`

**Task**: `config.py` reads `MODEL_ID`, `TABLE_NAME`, `AWS_REGION` from environment variables with no hardcoded fallback values for `TABLE_NAME` (must be explicit or raise). `bedrock_client.py` wraps `boto3.client("bedrock-runtime").invoke_model` behind a single function `invoke(prompt: str) -> str`. `dynamo_client.py` implements `get_session(session_id) -> dict | None` and `put_session(session_id, state: dict) -> None` against `TABLE_NAME`.

**Tests**: use `moto` to mock DynamoDB in a unit test for `get_session`/`put_session`. Do not test `bedrock_client.py` against real Bedrock — mock the `boto3` client.

**Definition of done**: `pytest backend/tests/unit -v` all green, still zero real AWS calls made anywhere in the test suite.

---

## Phase 7 — Lambda handler + SAM template

**Files**: `handler.py`, `template.yaml`, `infra/dynamodb-table.json`

**Task**: `handler.py` — parse the API Gateway event body (JSON: `session_id`, `code`, `problem_id`, `user_still_stuck: bool`), load/create session state via `dynamo_client`, run the compiled graph starting from the right node depending on whether this is a fresh submission or an escalation request, save state back, return a JSON response (`statusCode`, `body`). Keep this file thin — no graph logic lives here.

`template.yaml` — one `AWS::Serverless::Function` (Python 3.12 runtime, points at `handler.lambda_handler`), one `AWS::Serverless::Api`, one `AWS::DynamoDB::Table` (partition key `session_id`), IAM policy scoped to that one table + `bedrock:InvokeModel` on the specific model ARN only — do not use `"Resource": "*"`.

**Definition of done**: `sam validate` passes. Do not run `sam deploy` yet.

---

## Phase 8 — Deploy backend

**Task**: Run `sam build && sam deploy --guided` once manually (agent should present the command, not auto-run a real deploy without confirmation). Confirm the returned API Gateway URL responds to a test `curl` POST with a 200 and the expected JSON shape.

**Definition of done**: A real `curl` call against the deployed endpoint returns a valid triage response for one of the two sample problems. Record the endpoint URL in `.env` (frontend) and `README.md` — do not hardcode it in frontend source.

---

## Phase 9 — Frontend (Astro)

**Files**: `frontend/` per the structure agreed earlier (`src/pages/index.astro`, `src/components/TriageForm.astro`, `src/lib/api.ts`)

**Task**: Static page with a code textarea, problem picker (dropdown of the 2 sample problems), submit button, and a "still stuck" button that re-submits with `user_still_stuck: true` and the same `session_id`. `TriageForm.astro` is the only interactive island (`client:load`); everything else stays static. `api.ts` reads the API base URL from an Astro public env var, not a hardcoded string.

**Definition of done**: `npm run build` succeeds locally; manually submitting a form against the deployed backend URL renders a real hint response in the browser.

---

## Phase 10 — Deploy frontend + final demo pass

**Task**: Deploy the Astro build output as a static site (S3+CloudFront or Amplify Hosting — pick one, do not set up both). Do one full walkthrough: submit buggy code → get tier-0 hint → click "still stuck" → get tier-1 hint → click again → get patch. Capture screenshots/video of this sequence for the article.

**Definition of done**: Public URL live, full hint-escalation sequence demoed and captured. This is the finish line — do not add further features (multi-language support, more problems, auth, etc.) unless there's spare time after this is done and documented.
