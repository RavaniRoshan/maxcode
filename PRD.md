PRD: maxcode
Status: Draft 1. Date: 29 October 2026. Owner: Roshan Ravani.
1. Purpose
This document defines an open-source coding tool. The tool runs in the terminal. It builds on the Codex CLI. It adds a verifier loop.
The name is maxcode. It is the repository name and the product name. Search trademarks before you use it in public.
Claude Code agent: sections 19 to 28 are your build spec. Read all of them before you write code. Sections 1 to 18 define the product.
2. Terms
This document uses each term below with one meaning only.
Term
Meaning
Task
One request from the user.
Step
One item in the plan for a task.
Role
The planner, the worker, or the verifier.
Provider
A model API endpoint.
Check
A command that the verifier runs.
Run
One full execution of a task.
Checkpoint
A saved git state before a step.
Fork
Our changed copy of the Codex CLI source.
Wrapper
A tool that runs the unchanged Codex CLI.
3. Background
Sarvam Code is a coding product from Sarvam AI. It is in closed beta. Its public docs page says the product is coming soon.
Public sources describe three roles: planner, worker, and verifier. They also describe checkpoints, plan steering, and pricing by completed work.
No public Sarvam Code product exists. We cannot copy it. We build only from these public ideas.
The OpenAI Codex CLI is open source. It uses the Apache-2.0 license. This license lets us copy, change, and distribute the code.
4. Problem
Coding tools often report a task as done when the task is not done. The user must find the failure by hand.
Assumption A1: no open tool makes a pass-or-fail gate its core feature. Phase 0 tests this assumption.
5. Goals
• G1: Run the Codex workflow on any OpenAI-compatible provider, including open-weight models.
• G2: Mark a task done only after all checks pass.
• G3: Let the user undo any step with one command.
• G4: Show the cost of each completed task.
• G5: Publish a benchmark that anyone can reproduce.
6. Non-goals
The team does not build any item below in version 1.
• A graphical interface.
• Voice input.
• Multi-user sessions.
• Cloud hosting.
• Our own model.
• An IDE plugin.
Rule: the team adds one new item only after it removes one existing item.
7. Users
The primary user is a developer who works in a terminal. This user brings an own API key.
The tool supports any provider that follows the OpenAI API format. This includes India-hosted providers.
8. Legal requirements
Each requirement below is mandatory. The team checks all of them before launch.
• L1: Keep the LICENSE and NOTICE files from the Codex repository.
• L2: Mark every changed file with a change notice.
• L3: Remove the Codex name and logo from all output.
• L4: Do not use the Sarvam name, logo, copy, images, or fonts.
• L5: Do not decompile or inspect any Sarvam binary.
• L6: Write all site copy and all assets from zero.
• L7: Do not claim any link with Sarvam AI or OpenAI.
• L8: Describe the product as an open alternative. Do not use the word clone.
• L9: Search trademarks for the final name in India, the US, and the EU.
• L10: Check the license of every font and library.
• L11: Ask a lawyer to review the brand before launch.
Note: the Codex security plugin is proprietary and is not in the repository. Do not use it.
9. Functional requirements
FR-1 Provider layer
The tool reads the provider URL, key, and model name from a config file. The tool works with any OpenAI-compatible endpoint.
The tool must support tool calls on at least two open-weight models. Phase 0 tests this.
FR-2 Planner role
The planner reads the task and the repository. The planner outputs a list of steps in JSON. Each step has a goal and a check.
The user can edit the plan before the worker starts. The user can skip this with a flag.
FR-3 Worker role
The worker receives one step at a time. The worker edits files to complete that step. The worker never marks a step as done.
FR-4 Verifier role
The verifier runs the checks for the current step. The verifier ignores any claim in the worker text. The verifier returns pass or fail.
Default checks are the test command, the build command, and the lint command. The tool detects these commands from the repository.
The verifier also fails a step when the diff exceeds the size limit. The default limit is 400 changed lines.
FR-5 Checkpoints
The tool creates a git ref before each step. The ref name is refs/maxcode/RUN_ID/STEP_NUMBER. The command undo restores the last checkpoint.
The tool never changesnow the user branch history. It only writes to its own refs.
FR-6 Cost report
The tool counts input tokens and output tokens for every call. The tool shows the cost per completed task at the end of each run.
The tool counts cost from failed retries in the total. It reports failed tasks with their cost.
FR-7 Run log
The tool writes one JSONL file for each run. Each line is one event. Events include plan, edit, check result, retry, and cost.
The benchmark uses these logs as proof.
FR-8 Commands
Command
Action
run TASK
Plans, edits, and verifies a task.
plan TASK
Shows the plan and stops.
undo
Restores the last checkpoint.
cost
Shows the cost of the last run.
bench
Runs the benchmark suite.
FR-9 Config file
The config file is in TOML format. It sets the provider, one model for the planner, one model for the worker, the retry limit, and the cost cap.
10. Architecture
The user starts a run with the run command. The tool sends the task to the planner. The planner returns steps.
For each step, the tool creates a checkpoint. The tool sends the step to the worker. The worker edits files.
The tool then starts the verifier. The verifier runs the checks. A pass moves the run to the next step.
A fail returns the failure output to the worker. The worker tries again. The retry limit is 3 tries per step.
After the retry limit, the tool stops the run. It restores the last checkpoint. It reports the failure to the user.
The planner and the worker each call a provider. The verifier calls no model. It runs commands only.
11. Verifier loop rules
• Rule 1: A step is done only when every check passes.
• Rule 2: A task is done only when every step is done.
• Rule 3: The verifier rejects any step that edits a protected path.
• Rule 4: The tool stops a run when the cost cap is reached.
• Rule 5: The tool stops a run when the retry limit is reached.
• Rule 6: The tool logs every stop with its reason.
12. Build decision: wrapper or fork
Phase 0 makes this decision. The decision uses the rules below.
Choose the wrapper if the Codex config alone sets a custom provider and tool calls still work.
Choose the fork if the Codex code blocks a custom provider.
If the team chooses the fork, the first patch must change fewer than 500 lines. The patch only adds the provider layer.
The team pins the Codex version. The team merges upstream changes once each month.
13. Marketing site
The site has four pages: home, docs, benchmark, and GitHub link.
The team studies the public Sarvam site for page structure and message order only. The team does not copy its palette, layout, text, or assets.
The team picks its own palette and fonts. The team writes all copy from zero.
The home page shows three things: the problem, the verifier loop, and a 60-second install command.
The benchmark page shows the logs, the script, and the result of each run. It shows failures as well as passes.
14. Plan
Phase 0: Spike (days 1 to 2)
• Install the Codex CLI from source.
• Read the code path that selects a provider.
• Set one OpenAI-compatible endpoint in the config.
• Run one coding task on one open-weight model.
• Repeat the task on a second open-weight model.
• Write the results in a file named SPIKE.md.
• Apply the rules in section 12.
• Test assumption A1 with a search of GitHub.
Exit rule: one task completes on a non-OpenAI model.
Phase 1: Verifier loop (days 3 to 7)
• Write the three role prompts as plain text files.
• Build the planner call. It returns steps in JSON.
• Build the worker call. It edits files for one step.
• Build the verifier. It runs checks and returns pass or fail.
• Add the retry limit of 3 tries per step.
• Add the cost cap for each task.
• Write the JSONL run log.
Exit rule: a demo task finishes only after all checks pass.
Phase 2: Checkpoints and benchmark (days 8 to 14)
• Add checkpoints with git refs.
• Add the undo command.
• Add the cost report.
• Write a suite of 20 tasks from small public repositories.
• Run the suite with the verifier on.
• Run the suite again with the verifier off.
• Publish the logs and the script.
Exit rule: anyone can run the script and get the same table of results.
Phase 3: Brand and site (days 15 to 18)
• Confirm the name maxcode after the trademark search.
• Search trademarks for the name.
• Write the README in plain English.
• Build the four-page site.
• Complete the legal checklist in section 8.
Exit rule: all legal items L1 to L11 show done.
Phase 4: Launch (days 19 to 21)
• Tag version 0.1.
• Publish the repository.
• Publish the site.
• Post the benchmark results with the logs.
• Answer every issue within 24 hours for one week.
15. Success metrics
Metric
Target
Demo task passes on an open-weight model
By day 2
Verifier-on pass rate vs verifier-off
At least 10 points higher
Benchmark reproduced by one outside person
Within 30 days of launch
Install to first task
Under 5 minutes
GitHub stars
200 in 30 days
If the verifier gain is under 10 points, the team publishes the result as it is. The team then changes the product claim.
16. Risks
Risk
Action
Upstream Codex changes break the fork.
Pin the version. Merge each month.
The verifier gain is small.
Publish the real number. Change the claim.
Sarvam Code launches publicly first.
Keep the open source and own-key advantages.
The name conflicts with a trademark.
Search before launch. Change the name if needed.
Scope grows.
Apply the one-in, one-out rule.
Open models fail at tool calls.
Test two models in Phase 0.
17. Open questions
• Q1: Which two open-weight models does Phase 0 test?
• Q2: Does maxcode pass the trademark search?
• Q3: Is the goal a product with users or a portfolio piece? The answer sets how deep the fork goes.
• Q4: Which checks run when the repository has no tests?
18. Launch checklist
• The legal items L1 to L11 show done.
• The README install command works on a clean machine.
• The benchmark script runs from a fresh clone.
• The site shows no Sarvam or OpenAI asset.
• The repository has a LICENSE file and a NOTICE file.
• The repository has a CONTRIBUTING file and a security contact.
19. Rules for the Claude Code agent
You build maxcode from this document. Follow every rule below in every task.
• Read sections 1 to 28 before you write code.
• Work on one task from section 25 at a time.
• Write a failing test first. Finish the task when the test passes.
• Commit after each task. Use the message format T<number>: <summary>.
• Run ruff, mypy, and pytest before each commit.
• Stop and ask the user when a task needs a decision that this document does not make.
• Never invent a Codex CLI flag. Read each flag from the Codex repository or from its help output.
• Never copy text, assets, or code from Sarvam. Never open or decompile any Sarvam binary.
• Never remove the LICENSE file or the NOTICE file.
• Never weaken or delete a test to make it pass.
• Never store an API key in a file. Read keys from environment variables only.
• Keep each function under 40 lines. Keep each file under 400 lines.
• Add a type hint to every function.
• Write each error message in three parts: what failed, why it failed, and what to do next.
20. Stack and repository layout
maxcode is a Python program. It calls the Codex CLI as a child process. Task T0 decides whether that child is stock Codex or a fork.
Python keeps the build fast. The Codex CLI stays a separate program, so Python does not limit the speed of a run.
Item
Choice
Language
Python 3.12
Package manager
uv
CLI framework
Typer
HTTP client
httpx
Schemas
pydantic v2
Config format
TOML, read with tomllib
Tests
pytest
Lint and types
ruff and mypy
Git calls
The git command through subprocess
License
Apache-2.0
The package name on PyPI is maxcode. Task T1 checks that the name is free.
Create this layout in task T1.
maxcode/
  pyproject.toml
  README.md
  LICENSE
  NOTICE
  CONTRIBUTING.md
  SECURITY.md
  CLAUDE.md
  SPIKE.md
  src/maxcode/
    __init__.py
    cli.py            # Typer commands
    config.py         # load and validate config
    schemas.py        # pydantic models
    errors.py         # error types
    loop.py           # run controller
    checks.py         # detect and run checks
    checkpoints.py    # git refs
    cost.py           # token and cost counting
    runlog.py         # JSONL writer
    providers/
      base.py         # Provider protocol
      openai_compat.py
    engine/
      codex.py         # Codex CLI adapter
    roles/
      planner.py
      worker.py
      prompts/
        planner.md
        worker.md
    bench/
      runner.py
      tasks/          # 20 task files
  tests/
  site/               # marketing site (Phase 3)
21. Data schemas and config
The tool looks for the config file in this order: the --config flag, then ./maxcode.toml, then the user config folder. The first file found wins.
[provider.main]
base_url    = "https://api.example.com/v1"
api_key_env = "MAXCODE_API_KEY"

[planner]
provider = "main"
model    = "MODEL_NAME"

[worker]
provider = "main"
model    = "MODEL_NAME"

[limits]
max_retries_per_step  = 3
max_cost_usd_per_task = 2.00
max_diff_lines        = 400
max_steps             = 12

[checks]
test  = ""   # empty means auto-detect
build = ""
lint  = ""

[protected]
paths      = ["**/*.lock", ".github/**"]
test_paths = ["tests/**", "**/test_*.py", "**/*.test.*"]

[pricing."MODEL_NAME"]
input_per_mtok_usd  = 0.0
output_per_mtok_usd = 0.0
The tool shows token counts only when a model has no pricing entry. It never guesses a price.
The planner outputs a plan in this JSON shape.
{
  "task": "string",
  "steps": [
    {
      "id": 1,
      "goal": "string",
      "files": ["relative/path.py"],
      "checks": ["test", "lint", "cmd:pytest tests/test_x.py"],
      "edits_tests": false
    }
  ]
}
A check is test, build, lint, or cmd: plus a command. The tool runs a cmd: check only after the user approves the plan or sets --yes.
A step with edits_tests set to false cannot change a path in paths or in test_paths. A step with edits_tests set to true can change a path in test_paths only. The verifier fails the step if it breaks this rule.
The tool writes each run to .maxcode/runs/RUN_ID/log.jsonl. It adds .maxcode/ to .gitignore on first use.
Each log line is one JSON object with the fields ts, run_id, type, and data. The table lists the values of type.
Type
Fields in data
run_start
task, config_hash, repo_head
plan
steps
step_start
step_id, checkpoint_ref
worker_call
model, input_tokens, output_tokens, seconds
check_result
step_id, check, passed, exit_code, output_tail
retry
step_id, attempt
step_end
step_id, passed, diff_lines
stop
reason (retry_limit, cost_cap, step_cap, user_abort, error)
run_end
passed, steps_done, cost_usd, tokens_in, tokens_out
22. Module specs
Build each module as specified. Every public function has a unit test.
Module
Public function
Behavior
config.py
load_config(path) -> Config
Reads the TOML file. Validates it with pydantic. Raises ConfigError with the bad key name.
providers/openai_compat.py
chat(messages, model) -> ChatResult
Sends a chat request to the base URL. Returns text, input tokens, and output tokens. Raises ProviderError on HTTP failure.
roles/planner.py
make_plan(task, repo_summary, cfg) -> Plan
Calls the provider. Parses the JSON plan. Retries once if the JSON is invalid.
roles/worker.py
do_step(step, failure, cfg) -> EngineResult
Builds the worker prompt. Passes the previous failure output when it exists. Calls the engine.
engine/codex.py
run_step(prompt, repo, provider, model, timeout_s) -> EngineResult
Starts the Codex CLI as a child process in non-interactive mode. Returns exit code, transcript, and token counts when available.
checks.py
detect_checks(repo) -> dict
Finds the test, build, and lint commands from repository files.
checks.py
run_check(name, cmd, repo, timeout_s) -> CheckResult
Runs one command. Keeps the last 4000 characters of output. Fails on timeout.
checkpoints.py
create(run_id, step_id) -> ref
Saves the working tree as a commit under refs/maxcode/.
checkpoints.py
restore(ref)
Restores the working tree from the ref.
cost.py
CostMeter
Adds token counts per call. Returns total cost. Reports when the cap is reached.
runlog.py
RunLog.write(type, data)
Appends one JSON line. Flushes after each line.
loop.py
run_task(task, cfg, options) -> RunResult
Runs the state machine in section 23.
Engine rules. The engine adapter passes the provider URL and key to Codex. Task T0 finds the correct method in the Codex source.
The adapter reads token counts from the Codex output when Codex reports them. When Codex does not report them, the cost report shows the word partial. It then lists the planner cost only.
Check rules. The tool detects checks in this order: Python (pytest, ruff), Node (package.json scripts test, build, lint), Rust (cargo test, cargo build, cargo clippy), Go (go test, go build, go vet).
A step with zero checks ends as unverified, not as done. The run summary lists every unverified step.
Checkpoint rules. The checkpoint code uses a temporary git index file. This keeps the user index unchanged. The code saves untracked files that git does not ignore.
The tool stops with NotAGitRepo outside a git repository. It tells the user to run git init.
Repo summary rules. The planner receives a file tree with depth 3 and at most 200 entries. It also receives the first 2000 characters of the README.
Exit codes.
Code
Meaning
0
The task passed.
1
The task failed a check or hit a limit.
2
The config or the command line is wrong.
3
The provider or the engine failed.
130
The user aborted the run.
4
The task finished with unverified steps.
Commands.
Command
Options
maxcode run TASK
--yes, --config PATH, --max-cost USD
maxcode plan TASK
--config PATH
maxcode undo
none
maxcode cost [RUN_ID]
none
maxcode bench
--verifier on or --verifier off, --suite PATH
The run command shows the plan and asks for approval. The option --yes skips this approval.
23. Run loop: states and transitions
Implement loop.py as this state machine. Each row is one transition. Write one log event for each row that names an event.
From
Event
To
Action
INIT
Config valid and repository is git
PLAN
Write run_start. Record the repository HEAD.
INIT
Config invalid or no git repository
STOPPED
Exit 2.
PLAN
Plan parsed
REVIEW
Write plan.
PLAN
Plan invalid twice
STOPPED
Exit 3.
REVIEW
User approves or --yes is set
STEP_START
Start at step 1.
REVIEW
User rejects
STOPPED
Reason user_abort. Exit 130.
STEP_START
Always
WORK
Create the checkpoint. Write step_start. Set attempt to 1.
WORK
Engine returns
VERIFY
Write worker_call.
WORK
Engine fails or times out
STOPPED
Restore the step checkpoint. Exit 3.
VERIFY
All checks pass, diff is within the limit, no protected path changed
STEP_DONE
Write check_result and step_end.
VERIFY
Any check fails, or the diff is too large, or a protected path changed
RETRY
Save the failure output. Write check_result.
RETRY
Attempt is below the retry limit
WORK
Add 1 to attempt. Keep the edits. Pass the failure output to the worker.
RETRY
Attempt equals the retry limit
STOPPED
Reason retry_limit. Restore the step checkpoint. Exit 1.
STEP_DONE
More steps remain
STEP_START
Move to the next step.
STEP_DONE
No steps remain
TASK_DONE
Write run_end. Exit 0. Exit 4 when any step is unverified.
Any
Cost cap reached
STOPPED
Reason cost_cap. Restore the step checkpoint. Exit 1.
Any
Step count exceeds max_steps
STOPPED
Reason step_cap. Exit 1.
Any
User presses Ctrl-C
STOPPED
Reason user_abort. Keep the files. Print the undo command. Exit 130.
The retry limit counts all attempts, including the first. The default limit is 3 attempts.
A restore keeps the work of earlier steps that passed. It removes only the failed step.
The diff size is the number of added and removed lines since the step checkpoint.
The protected path test compares the changed file list with the glob patterns in the config. Use the step flag edits_tests as section 21 defines.
A task that ends with unverified steps exits 4. The summary shows the word unverified beside each such step.
24. Prompt contracts
Store each prompt as a text file in roles/prompts/. The code fills the braces at run time.
The file planner.md holds this text.
You are the planner for a coding tool.
Read the task and the repository summary.
Output one JSON object. Output nothing else.
The JSON must match the schema below.
Rules:
1. Use at most {max_steps} steps.
2. Make each step small. One step changes at most 100 lines.
3. Order the steps so each step builds on the one before.
4. List the checks for each step. Use only: {available_checks}.
5. Use a cmd: check only when no named check covers the step.
6. Set edits_tests to true only when the step adds or changes tests.
7. For a bug fix, make step 1 add a test that fails now.
Schema: {schema}
Task: {task}
Repository summary: {repo_summary}
The file worker.md holds this text.
You are the worker for a coding tool.
Complete this one step. Do not work on other steps.
Step goal: {goal}
Files to focus on: {files}
Task context: {task}
Rules:
1. Change only what the step needs.
2. Do not edit these paths: {protected_paths}.
3. Do not disable, skip, or delete any existing test.
4. Do not claim the step is done. A separate program checks your work.
5. Stop when you finish the edits.
{failure_block}
The code sets failure_block to an empty string on the first attempt. On later attempts it holds the text below.
The last attempt failed these checks. Fix the cause.
{failure_output}
The planner parser removes code fences. It parses the JSON and validates it with pydantic. On failure it retries once. The retry adds the error text and the words: Output the JSON only.
The code cuts failure_output to the last 4000 characters.
25. Build tasks and acceptance tests
Do the tasks in order. A task is done only when its acceptance test passes. Phase names match section 14.
Phase 0: Spike
ID
Task
Acceptance test
T0
Install the Codex CLI from source. Find where it selects a provider. Run one coding task on two open-weight models. Write the results in SPIKE.md.
SPIKE.md answers four questions: wrapper or fork, the exact non-interactive command and flags, whether Codex reports token counts, and how to pass the provider URL and key. It includes one successful run log for each model.
If T0 chooses the fork, add task T0b. Put the fork in a separate repository named maxcode-engine. Keep the first patch under 500 changed lines. Update the NOTICE file.
Phase 1: Verifier loop
ID
Task
Acceptance test
T1
Create the layout from section 20. Add pyproject.toml, the Apache-2.0 LICENSE, and a CI workflow that runs ruff, mypy, and pytest.
uv run pytest passes with one smoke test. CI is green.
T2
Build config.py.
Tests cover a valid file, a missing file, a bad key, and a missing environment variable.
T3
Build schemas.py and runlog.py.
A test writes three events and reads them back as valid JSONL.
T4
Build the OpenAI-compatible provider.
A test with a mock transport returns text and token counts. An HTTP 500 raises ProviderError.
T5
Build the planner and planner.md.
A fake provider returns valid JSON: the test gets a Plan. Invalid then valid: one retry. Invalid twice: an error.
T6
Build checks.py.
Fixture repositories for Python, Node, and no tests give the right commands. A timeout test fails the check.
T7
Build checkpoints.py.
In a temporary repository: change a tracked file, add an untracked file, create a checkpoint, change both again, restore. The files match the checkpoint. git diff --cached is the same before and after.
T8
Build cost.py.
A test reaches the cap and reports it. A model without pricing returns tokens only.
T9
Build the Codex engine adapter from SPIKE.md.
A unit test uses a fake Codex program. A slow integration test creates hello.txt with a real provider. It skips when no key is set.
T10
Build the worker role and worker.md.
The prompt matches section 24. The failure block appears only after attempt 1.
T11
Build step verification: protected paths and diff size.
An edit to a protected path fails. With edits_tests true, an edit to a test path passes. A diff over the limit fails.
T12
Build loop.py.
One test for each row of the table in section 23, using fakes.
T13
Build cli.py.
A CliRunner test for each exit code in section 22. The plan review prompt works.
Phase 1 exit test: use a toy repository with a failing function. Run maxcode run on it. The run ends with exit 0 only after the test passes.
Phase 2: Checkpoints and benchmark
ID
Task
Acceptance test
T14
Finish the undo and cost commands.
After a run, undo restores the last checkpoint. cost shows totals and the word partial when needed.
T15
Build the benchmark runner and 20 tasks. Each task has a repository URL, a commit, a task text, and a score command.
maxcode bench writes results.csv and one log for each task. With --verifier off, the loop skips the verify state. Both modes use the same final score command.
T16
Build the report script.
The script reads the logs and prints a table: pass rate, cost per completed task, and unverified count. The README shows this table.
Phase 3 and 4: Brand, site, and release
ID
Task
Acceptance test
T17
Write README.md, CONTRIBUTING.md, and SECURITY.md.
A new user installs and runs the demo in under 5 minutes on a clean machine.
T18
Build the site in site/. Use plain HTML and CSS. Host it on GitHub Pages.
The four pages exist. The site loads no external asset. It contains no Sarvam or OpenAI asset or text.
T19
Tag version 0.1. Publish to PyPI. Write CHANGELOG.md.
uvx maxcode --help works on a clean machine. All legal items in section 8 show done.
26. Test plan
Write a unit test for every public function in section 22. Unit tests use no network and write only to temporary folders.
Mark tests that need a real provider with slow. They need the variables MAXCODE_BASE_URL and MAXCODE_API_KEY. They skip when a variable is missing.
CI runs only the tests that are not marked slow. It runs them on every push.
Use a fake Codex program in tests/fixtures/. The fake program edits files in a fixed way, so loop tests stay fast and exact.
Add these security tests.
• Set a fake API key in the environment, run a task, and search the log files. The key must not appear.
• Plan a cmd: check without approval. The tool must not run it.
• Edit a protected path in a fake step. The verifier must fail the step.
Keep line coverage on src/maxcode at 85 percent or higher. The bench folder is not counted.
Add one regression test for every bug fix. Run the benchmark by hand, not in CI. Publish its logs.
27. CLAUDE.md for the repository
Create this file in task T1. Place it in the repository root.
# maxcode

maxcode is an open-source coding CLI. It plans a task, edits code with the Codex engine, and marks the task done only after checks pass.

## Commands
- Install: `uv sync`
- Test: `uv run pytest -m "not slow"`
- Lint: `uv run ruff check . && uv run mypy src`
- Run: `uv run maxcode --help`

## Rules
- Read the PRD before you start. The PRD is the source of truth.
- Work on one task at a time. Write the failing test first.
- Commit after each task: `T<number>: <summary>`.
- Never invent a Codex CLI flag. Read it from the Codex source or help output.
- Never copy text, assets, or code from Sarvam. Never inspect a Sarvam binary.
- Never remove LICENSE or NOTICE.
- Never weaken or delete a test to make it pass.
- Never store an API key in a file.
- Keep functions under 40 lines and files under 400 lines.
- Ask the user when the PRD does not decide something.

## Layout
See the repository layout in the PRD, section 20.
28. Definition of done
The build is done only when every item below is true.
[ ] All tasks T0 to T19 pass their acceptance tests.
[ ] CI is green on the main branch.
[ ] Line coverage is 85 percent or higher.
[ ] The Phase 1 exit test passes.
[ ] The benchmark logs and the report script are in the repository.
[ ] The legal items L1 to L11 in section 8 show done.
[ ] The README install steps work on a clean machine.
[ ] A secret scan finds no API key in the repository.
[ ] The tag v0.1 exists.

29. Next update: V2 provider system (deferred)
Status: Not part of v1. Do not build this before T19 and the v1 launch checklist are done.
Goal: make maxcode a multi-provider, multi-model tool with provider and model catalogs, like the OpenCode CLI.
V1 stays as written: one provider config that can point at any OpenAI-compatible endpoint, text only.
V2 adds:
• A provider registry with named providers, not one hardcoded provider.
• Model catalogs: list the models for each provider with context size, tool support, image support, and pricing.
• Auth: environment variables first, then the OS keyring. Never store keys in the repository or the logs.
• Start with 2 to 5 providers: OpenRouter, Groq, DeepSeek, Qwen/DashScope, and local Ollama or LM Studio. Add more only under the one-in-one-out rule.
• Capability flags: tool calls, image input, streaming, and the wire API (Responses or Chat Completions).
• Provider selection per role. The verifier stays command-only.
• A health check with clear errors for a missing key, a bad URL, or an unsupported model.
• Multimodal image input for the planner and worker only when the selected model declares image support. Audio and voice stay out of scope unless the non-goals change.
• A model picker command and a config command.
• Benchmarks that record the provider and model for each task.
Acceptance test: one config can switch between at least five providers. The same task runs on two models from different catalogs. A missing capability fails with an actionable error. No key appears in the logs.
Open questions for V2:
• Q5: Which five providers start the V2 catalog?
• Q6: Which image inputs does V2 support?
• Q7: Is auth environment-only, or does V2 add the OS keyring?
• Q8: Does V2 need native Anthropic and Gemini adapters, or only OpenAI-compatible endpoints?
