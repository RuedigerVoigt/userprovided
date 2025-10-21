# How to contribute

Welcome,

Open Source thrives on code contributions so pull requests (PRs) are always welcome.

## The use of Software Coding Agents

Software engineering agents like OpenAI Codex or Claude Code are becoming an important part of modern software development.
So it is ok if you use artificial intelligence to find bugs or to support you in the development of a new feature.
As those tools sometimes hallucinate or choose overcomplicated ways to solve an issue, check your pull requests before submitting them.
Specific instructions for these agents are found in the [AGENTS.md](AGENTS.md) file.



## Pull Requests / Code Guidelines

* This project uses the **[Apache License 2.0](LICENSE)**. In order to submit you must agree with its terms.
* **The library "userprovided" relies solely on the Python Standard Library (PSL). Any PR introducing external dependencies outside the PSL will be rejected.** (The exception to this is introducing dependencies for tests and not the library itself.)
* Please respond to comments and requests for change of your PR.
* Use develop as your base branch for PRs.
* If you add a new feature, please add corresponding unit tests.
* Please do not put too many changes in one PR. Instead group them logically.
* Please check that there are no untracked, modified, or staged files left unintentionally before you make a commit (e.g. run `git status` to confirm a clean working tree).

## Coding Style

* Respect [PEP 8](https://peps.python.org/pep-0008/) style guidelines.
* The use of type hints ([PEP 484](https://peps.python.org/pep-0484/)) is encouraged.
* Please provide useful log and error messages.
* Docstrings are required for all functions and classes using [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

This project supports Python 3.10 to 3.14 and uses [Poetry](https://python-poetry.org/) for packaging and dependency management.
