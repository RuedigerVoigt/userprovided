# AGENTS.md instructions

This file extends [CONTRIBUTING.md](CONTRIBUTING.md) and applies specifically to software engineering agents (e.g., Codex, Claude Code, GPT-4, etc.)
Agents must also follow all guidelines in CONTRIBUTING.md, including style, testing, and licensing requirements.
The sections below add special constraints or clarifications for agents.
This helps ensure automated contributions are robust, transparent, and safe.

## Project Overview

The Python package userprovided checks input for validity and plausibility. It also includes methods to convert input into standardized formats. This helps ensure robust data handling by validating and standardizing user inputs for various applications.

## Project Structure for Agent Navigation

* userprovided          # top-level project directory
  * .github
    * /workflows        # GitHub workflows used for testing every commit
  * userprovided        # source code of the python package
  * CHANGELOG.md        # list the changes in any new version
  * CONTRIBUTING.md     # a guide on how to contribute to this project
  * LICENSE             # text of the License
  * README.md           # The homepage of the project and also the documentation
  * pytest.ini          # Instructions for pytest
  * tests.py            # tests to run with pytest

## Agent-specific Guidelines

### Dependencies:

* The library "userprovided" relies solely on the Python Standard Library (PSL) for runtime dependencies.
* External dependencies are prohibited in the main library code.
* External dependencies ARE allowed and encouraged for testing purposes (pytest, hypothesis, requests, etc.).
* Agents must not modify pyproject.toml or any configuration/metadata files unless explicitly instructed in the task.

### Supported Python versions:

* The code must run with all supported Python versions from 3.10 to 3.13 (inclusive).
* Test compatibility with both the minimum (3.10) and maximum (3.13) supported versions.
* Testing with intermediate versions (3.10, 3.11, 3.12) is encouraged but not required.

### Coding Style:

* Use consistent naming conventions that match the rest of the codebase.
* Respect PEP 8 style guidelines.
* Write code with comprehensive type hints (PEP 484) for all function signatures, parameters, and return values.
* Write docstrings using the Google format.
* Error handling:
  * Use specific exception types (ValueError, TypeError, etc.).
  * Provide helpful error messages that guide users toward solutions.
  * Follow existing error message patterns in the codebase.

### Test driven development:

* **MANDATORY**: Add tests for new code in [tests.py](tests.py) - agents must do this automatically, not wait to be asked.
* **Tests are required before code submission** - incomplete PRs will be rejected.
* **Verify tests pass**: Run `pytest -q` to confirm all tests pass before considering the task complete.
* **Document new features**: Add new functions, classes, or significant changes to [CHANGELOG.md](CHANGELOG.md) under the "Upcoming" section.
* Cover both expected and edge case inputs.
* Write property-based tests using `@given(...)` from hypothesis to automatically check your code against a wide range of inputs, including edge cases you might not think of.
* Do **not** copy the implementation logic into the test: Tests should verify what the code does, not how it does it. Avoid repeating the same expressions or algorithms from the main code in your tests. If both are wrong, the test would still pass.
* Required testing dependencies: `pytest` and `hypothesis`
* Additional testing dependencies are allowed (see dependency policy above)
* Run `pytest -q` for the test suite (or `python -m pytest -q` if pytest command not found).
* Run `flake8` to check style.
* Run `mypy`.
* REQUIRED: Run a static security analyzer (e.g. `bandit`) before submitting a PR and include results in the PR description.
* Include code coverage data using `pytest --cov=userprovided`. Aim for >90% for new code unless justified.


###  Branching:

* ALL pull requests must target the `develop` branch only.
* Agents must not create new branches (use the assigned working branch only).
* Pull requests to `main` branch will be rejected without review.

### The Pull Request:

  * Accept that all contributions fall under the project's license, and explicitly state this in the PR.
  * Always state which agent produced the code (Claude, Codex, GPT-4, etc.) in the pull request description.
  * When unsure about ambiguous requirements, add a comment describing the uncertainty.
  * Do not increment version numbers and do not set release dates. You may describe changes in CHANGELOG.md under the header "upcoming"
  * Agents must **not** rewrite commit history (e.g., via git rebase).
  * Prefer minimal, self-contained changes with testable outputs.
  * One logical change per commit.
  * Use the prefix "nit: " for commits containing only trivial changes such as:
    * Fixing typos in documentation
    * Correcting whitespace/formatting
    * Minor comment updates
  * For `nit:` commits, avoid bundling them with functional changes.
  * Commit Messages:
    * Keep commit messages clear and concise:
      * Start with a clear verb, e.g., "Fix", "Add", "Refactor"
      * Avoid vague summaries like "updates" or "tweaks"
    * Include a brief summary of changes and test results in the pull request description.
    * Include citations / prompt excerpts where relevant.
    * Include the Python version used for generation.
    * Include library versions of testing tools like pytest, hypothesis.
    * In the PR description, include any known limitations or uncertainty the agent has about its code.
    * Include test output in PR description:
      * Full pytest output with coverage information.
      * Mypy results (should show no errors).
      * Bandit security scan results.
      * Flake8 style check results.

### Security:

* Always follow secure coding best practices (avoid `eval`, insecure hashes, etc)!
* Ensure no secrets like API-keys are added to the repository.

### Quality Checks

To improve PR quality, please review for:
  * hallucinated modules or functions
  * unintended changes to unrelated files
  * partial updates across files
  * insecure practices
  * branch / version rules

