# AGENTS.md instructions

Software engineering agents like Codex or Claude Code use this file to understand how to contribute changes to the repository.

## Project Overview

The Python package userprovided checks input for validity and / or plausibility. Besides that it contains some methods to convert input into standardized formats.

## Project Structure for Agent Navigation

* userprovided
  * .github
    * /workflows       # GitHub workflows used for testing every commit
  * userprovided        # source code of the python package
  * CHANGELOG.md        # list the changes in any new version
  * LICENSE             # text of the License
  * README.md           # The homepage of the project and also the documentation
  * pytest.ini          # Instructions for pytest
  * tests.py            # tests to run with pytest

## Pull Request target
- All pull requests must use `develop` as the base branch. Do not send pull requests to main!

## Testing
- Install dependencies via `pip install -r requirements.txt`.
- Running the tests also requires `pytest` and `hypothesis`
- Run `pytest -q` for the test suite.
- Run `flake8` to check style.

## Code Guidelines

- Respect PEP 8 style guidelines
- The code must run with the lowest supported Python version
- Write code with type hints (PEP 484)
- If possible add tests
- Aim to provide useful log and error messages

## Security Guidlines

- Follow secure coding best practices.
- The library "userprovided" relies solely on the Python standard library.
- Adding external runtime dependencies is only allowed for the creation of tests.
- Use secure algorithms from `hashlib` and avoid deprecated ones such as MD5 or SHA1.
- Run a static security analyzer (e.g. bandit) before submitting a PR.
- Ensure no secrets are added to the repository.


## Commits and PRs
- One logical change per commit.
- If a commit only contains very minor changes like fixing typos in the documentation use the prefix "nit: " for the commit message.
- Keep commit messages clear and concise.
- Include a brief summary of changes and test results in the pull request description.
- Ensure the working tree is clean before committing.
- Make clear that this commit or PR was written by a software agent and write its name into the PR.
- Do not increment version numbers and do not set release dates. You may describe changes in CHANGELOG.md under the header "upcoming version"
- Do not rewrite history or create new branches.
- Provide code citations in summaries where relevant.
- All commits and PRs must accept that their contribution to the projects falls under the project's licence - for example by writing that into the PR.
