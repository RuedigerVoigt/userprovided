# AGENTS.md instructions

This file extends [CONTRIBUTING.md](CONTRIBUTING.md) and is specifically meant for software engineering agents like Codex or Claude Code.
Agents must also follow all guidelines in CONTRIBUTING.md, including style, testing, and licensing requirements.
The sections below add special constraints or clarifications for agents.
This helps ensure automated contributions are robust, transparent, and safe.

## Project Overview

The Python package userprovided checks input for validity and / or plausibility. Besides that it contains some methods to convert input into standardized formats.

## Project Structure for Agent Navigation

* userprovided
  * .github
    * /workflows        # GitHub workflows used for testing every commit
  * userprovided        # source code of the python package
  * CHANGELOG.md        # list the changes in any new version
  * CONTRIBUTING.md     # a guide how to contribute to this project
  * LICENSE             # text of the License
  * README.md           # The homepage of the project and also the documentation
  * pytest.ini          # Instructions for pytest
  * tests.py            # tests to run with pytest

## Agent-specific Guidelines

* The library "userprovided" relies solely on the Python Standard Library (PSL).
* Without exception, external runtime dependencies outside the PSL are only allowed for tests.
* The code must run with the lowest and highest supported Python version. Currently these are Python 3.9 and 3.13.
* Coding Style:
  * Respect PEP 8 style guidelines.
  * Write code with type hints (PEP 484).
  * Write docstrings using the Google format.
  * Provide meaningful log and error messages.
  * Add tests for new code in [tests.py](tests.py).
* The pull request:
  * Always submit changes via pull requests to `develop`. Never send pull requests to main!
  * Accept that all contributions fall under the project's license, and explicitly state this in the PR.
  * Always state which agent produced the code (Claude, Codex, GPT-4, etc).
  * Do not increment version numbers and do not set release dates. You may describe changes in CHANGELOG.md under the header "upcoming"
  * Do not rewrite history or create new branches.
  * One logical change per commit.
  * If a commit only contains very minor changes like fixing typos in the documentation use the prefix "nit: " for the commit message.
  * Keep commit messages clear and concise.
  * Include a brief summary of changes and test results in the pull request description.
  * Include citations / prompt excerpts where relevant.
* Security:
  * Always follow secure coding best practices (avoid `eval`, insecure hashes, etc)!
  * Ensure no secrets like API-keys are added to the repository.
* To improve PR quality, please review for:
  * hallucinated modules or functions
  * unintended changes to unrelated files
  * partial updates across files
  * insecure practices
  * branch / version rules

## Testing

* Running the tests requires `pytest` and `hypothesis`
* Run `pytest -q` for the test suite.
* Run `flake8` to check style.
* Run `mypy`.
* Run a static security analyzer (e.g. `bandit`) before submitting a PR.
