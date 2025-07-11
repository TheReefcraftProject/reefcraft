# Reefcraft Contributor Guide

Welcome to the Reefcraft Project! This document outlines our coding standards, development process, and collaboration practices. Whether you're an intern, core team member, or an open-source contributor, this guide will help you understand how we work together.

---

## 🌊 Project Overview
Reefcraft is a scientific simulation platform that models coral growth and marine ecosystems using physically-based methods. The core logic is implemented in Python using Taichi for high-performance kernels.

We value:
- Scientific accuracy
- Code quality and clarity
- Collaboration and shared ownership

---

## 🔁 Agile Development Process
We work in **1-week iterations**, starting Sunday and ending the following Friday, with planning on Friday before the new iteration.

### Team Roles
- **Sage & Gaeryth** – Software development (core code, DevOps)
- **Marcus** – Business modeling and research
- **Amy** – Business, sales, marketing expert and leadership
- **Justin** – Contributor across all domains and team lead

### Weekly Flow
- **Friday** – Review current iteration, plan next
- **Sunday** – New iteration officially begins
- **Monday** – First full workday of new sprint
- Contributors **select their own work** based on interests and team needs

---
## 🧪 Test-Driven Development (TDD) Practices for Reefcraft

Test-Driven Development (TDD) is a software development approach where tests are written before the code itself. It ensures correctness, reliability, and bug-free code by creating automated tests early in the development process. We encourage all contributors to adopt TDD to ensure that our code is thoroughly tested and reliable.

### 1. TDD Workflow
The TDD process follows a simple **Red-Green-Refactor** cycle:

- **Red**: Write a failing test that describes the new functionality you want to implement.
- **Green**: Write just enough code to make the test pass.
- **Refactor**: Refactor the code to improve quality and maintainability, ensuring that all tests still pass.

### 2. Writing Tests
- **Test Case Structure**: 
  - Each test should be clear, concise, and self-contained.
  - Name your tests to describe what the test is verifying.
  - Each test should cover a single aspect of the functionality.
  
  Example:
  ```python
  def test_sim_value_returns_finite_float():
      result = reefcraft.sim_value(1.0)
      assert isinstance(result, float)
      assert -1.05 <= result <= 1.05
---

## ✅ User Story & Task Workflow
We use GitHub Issues to track work. Each feature or problem should begin as a **User Story** with small actionable sub-issues.

### ✏️ Standard Prompt for Creating User Stories & Subtasks
> "Write a GitHub-formatted user story and checklist of 1–4 hour subtasks using the following format. Prefix each subtask with `[Subtask]` for automation. Include any validation or test work as subtasks."

### ✅ Example
```
**User Story**
As a contributor, I want to integrate logging into the simulation loop so that we can debug and analyze coral growth over time.

**Tasks**
- [ ] [Subtask] Create a `logger.py` module with basic logging config
- [ ] [Subtask] Add log events for growth step and voxel updates
- [ ] [Subtask] Write a test that asserts log output is generated
- [ ] [Subtask] Validate logs are visible in console and saved to file
```

---

## 🔧 Coding Standards

### Python
- Use `pytest` for unit testing (required)
- Type annotations are encouraged and should be validated manually (no `mypy` enforced yet)
- Follow [PEP8](https://peps.python.org/pep-0008/) and [PEP257](https://peps.python.org/pep-0257/) (docstrings)
- We use [`ruff`](https://docs.astral.sh/ruff/) for automatic linting and formatting


### Git
- Use descriptive branch names: `feat/<feature>`, `fix/<bug>`, `test/<module>`
- Write clear commit messages
- Squash merge all PRs (see below)

---

## 🔀 Pull Request Process

### Guidelines
- Open a PR as early as possible (even in draft) for visibility
- Include a clear title and description
- Link issues using `Closes #<issue>`
- Keep commits clean and scoped
- Add test coverage where applicable

### Merge Strategy
We use **Squash and Merge** only.
- This ensures a clean, linear history
- The **author is responsible** for merging after approval
- The final commit message should summarize the full change

---

## 🔁 Continuous Integration (CI)
We use **GitHub Actions** for automated testing and linting:

- All pull requests and commits to `main` trigger the CI pipeline
- Tests are run using `pytest`
- Code style and formatting are enforced via `ruff`
- CI must pass before merging any PR

## 🤖 Using Codex for Development
We support using **Codex via ChatGPT Pro** for feature development and bug fixing.

### Setup Instructions
1. Ensure you have a ChatGPT Pro account
2. Visit [https://chat.openai.com/codex](https://chat.openai.com/codex) to launch Codex
3. During Codex setup, connect it to the [Reefcraft repo](https://github.com/TheReefcraftProject/reefcraft)
4. Enable **default limited internet access** so Codex has a writable container and repo context to enable builds and CI
- Paste a GitHub issue into your Codex prompt when requesting help
- Keep all task context in the issue for transparency and traceability
- Submit work as a pull request (PR) as usual
- Ensure all CI checks pass before merging

### Expectations
- For each new feature, start by writing a failing test
- Then implement the feature until the test passes
- Refactor code with confidence knowing tests cover it
- Submit all relevant tests in the same PR as the feature or bugfix

### Python TDD
- Use `pytest` and include tests under the `tests/` directory
- Aim for clarity and coverage; mock external dependencies if needed
- Parametrize tests where useful (`@pytest.mark.parametrize`)
- Include edge cases and regression scenarios


## 💡 Contributor Tips
- Always link work to issues
- Use Codespaces or pull locally to review full file context
- Ask for review early
- Suggest `RELEASES.md` entries in your PR

---

Let us know if you’d like to add tools, workflows, or suggestions to this guide. Thanks for contributing to Reefcraft 🪸
