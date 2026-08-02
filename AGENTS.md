# AGENTS.md instructions

This file extends [CONTRIBUTING.md](CONTRIBUTING.md) and applies specifically to software engineering agents (e.g. OpenAI Codex, Anthropic Claude, ...)
Agents must also follow all guidelines in CONTRIBUTING.md, including style, testing, and licensing requirements.
The sections below add constraints and clarifications that apply to agents only.

## Project Overview

The Python package userprovided checks input for validity and plausibility. It also includes methods to convert input into standardized formats. This helps ensure robust data handling by validating and standardizing user inputs for various applications.

## Project Structure for Agent Navigation

* userprovided          # top-level project directory
  * .github
    * /workflows        # GitHub workflows used for testing every commit
  * tests               # test files (one test_<module>.py per source module)
    * test_date.py
    * test_finance.py
    * test_geo.py
    * test_hashing.py
    * test_ip.py
    * test_mail.py
    * test_parameters.py
    * test_url.py
  * userprovided        # source code of the python package
    * date.py
    * err.py
    * finance.py
    * geo.py
    * hashing.py
    * ip.py
    * mail.py
    * parameters.py
    * url.py
  * CHANGELOG.md        # list the changes in any new version
  * CONTRIBUTING.md     # a guide on how to contribute to this project
  * LICENSE             # text of the License
  * pyproject.toml      # project metadata and dependencies managed by Poetry
  * pytest.ini          # instructions for pytest
  * README.md           # the homepage of the project and also the documentation
  * SECURITY.md         # how to report a vulnerability privately

## Dependencies

* The library "userprovided" relies solely on the Python Standard Library (PSL) for runtime dependencies. External dependencies are prohibited in the main library code.
* External dependencies ARE allowed and encouraged for testing purposes (pytest, ...).
* Agents must not modify pyproject.toml or any configuration/metadata files unless explicitly instructed in the task.

## Supported Python versions

* The code must run with all supported Python versions from 3.11 to 3.14 (inclusive). CI runs the full matrix on Linux, macOS and Windows.

## Coding Style

CONTRIBUTING.md covers PEP 8, type hints, naming and docstrings. In addition:

* Use consistent naming and error message patterns that match the rest of the codebase.
* Use specific exception types (ValueError, TypeError, ...) and provide messages that guide users toward a solution.
* **Non-string input to a string-validating `is_*` predicate raises `TypeError`** (with a clear message), it does not return `False`. A boolean result is reserved for actual string input — `False` means "a string that is not valid", never "wrong type". This applies to `is_isin`, `is_iban`, `is_email`, `is_url`, `is_shortened_url`, `is_aws_s3_bucket_name`, and the `ip.is_*` predicates. (`is_port` and `is_valid_coordinates` are deliberately different: they accept non-string domains.)
* Logging levels — the package must not spam the logs of the application using it:
  * `logging.debug` for handled validation failures and other expected, recoverable conditions (the default for nearly everything here). If a traceback is useful, pass `exc_info=True` to `debug` rather than using `logging.exception`.
  * `logging.error` only for caller contradictions that also raise (e.g. mutually exclusive arguments).
  * Do **not** use `logging.exception`.
  * **Log user-provided values with `%r`, not `%s`** (e.g. `logging.debug('bad value %r', value)`). `repr()` escapes newlines and control characters, preventing log injection / forged log lines from attacker-controlled input. Use lazy `%`-args, never f-strings or string concatenation, so the formatting only happens when the message is emitted.

## Test driven development

* **MANDATORY**: Add tests for new code in the matching `tests/test_<module>.py` file (e.g. `tests/test_url.py` for `userprovided/url.py`) - agents must do this automatically, not wait to be asked.
* **Tests are required before code submission** - incomplete PRs will be rejected.
* CI fails the build if coverage (line and branch) drops below **100%**, so new code needs tests covering every branch.
* Cover both expected and edge case inputs.
* Write property-based tests using `@given(...)` from hypothesis to automatically check your code against a wide range of inputs, including edge cases you might not think of.
* Do **not** copy the implementation logic into the test: Tests should verify what the code does, not how it does it. Avoid repeating the same expressions or algorithms from the main code in your tests. If both are wrong, the test would still pass.
* Run `pytest -q` (or `python -m pytest -q`) before considering the task complete.

## Branching

* ALL pull requests must target the `develop` branch only. Pull requests to `main` or `master` will be rejected without review.
* Agents should work on the `develop` branch or a feature branch as assigned, and must not create new branches unless explicitly instructed.
* Agents must **not** rewrite commit history (e.g. via git rebase).

## Commits and Pull Requests

* Prefer minimal, self-contained changes. One logical change per commit.
* Start commit messages with a clear verb, e.g. "Fix", "Add", "Refactor". Avoid vague summaries like "updates" or "tweaks".
* Use the prefix "nit: " for commits containing only trivial changes (typos, whitespace, minor comment updates) and do not bundle those with functional changes.
* Do not increment version numbers and do not set release dates. Describe changes in CHANGELOG.md under the header "upcoming".
* Accept that all contributions fall under the project's license, and explicitly state this in the PR.
* Always state which agent produced the code (Claude, Codex, GPT-4, ...) in the pull request description.
* State any known limitations or uncertainty about the code. When unsure about ambiguous requirements, add a comment describing the uncertainty.
* **Do not paste tool output into the PR.** Every push runs the tests, the coverage gate, ruff, mypy, bandit and CodeQL, and a release cannot be published unless they pass. Reproducing that output in the description adds nothing.

## Security

* Always follow secure coding best practices (avoid `eval`, insecure hashes, etc)!
* Ensure no secrets like API-keys are added to the repository.

## Before Submitting Checklist

- [ ] **Tests added**: New functionality has tests in the matching `tests/test_<module>.py`
- [ ] **Coverage**: `pytest --cov=userprovided --cov-fail-under=100 tests/` passes
- [ ] **Documentation**: New public functions are in README.md (with a TOC link) and CHANGELOG.md under "Upcoming"
- [ ] **Branch target**: Pull request targets `develop` (not `main` or `master`)
- [ ] **PR description**: names the agent and any known limitations
- [ ] **No collateral damage**: no unrelated files changed, no partial updates, no hallucinated modules or functions
