#  ReefCraft Releases

We follow [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

- `MAJOR` for breaking changes to the public interface (e.g., removing or changing function names, arguments, return types)
- `MINOR` for backward-compatible features (e.g., adding a logger, new GUI control)
- `PATCH` for bug fixes or small tweaks that don’t add or remove functionality

Release tags use the format `vX.Y.Z` (e.g., `v0.1.0`).

---

##  What Triggers a Version Bump?

Here are some common examples to help decide when and how to bump the version:

| Change Type                       | Version Impact? | Bump Type |
|-----------------------------------|-----------------|-----------|
| Add new simulation feature        |  Yes            | MINOR     |
| Fix coral growth bug              |  Yes            | PATCH     |
| Change function signature         |  Yes            | MAJOR     |
| Add logging system (user-visible) |  Yes            | MINOR     |
| Add new test suite                |  No             | None      |
| Improve docs only                 |  No             | None      |
| Add release automation            |  Maybe*         | MINOR or None |
| Internal refactor (no API change) |  No             | None      |

> *If automation affects user-visible behavior (e.g., changelog output), it may justify a MINOR bump.

---

##  How to Release

###  Release Requirements (Manual)

Before publishing a release, ensure the following:

- All automated tests (CI) are passing on the main branch
- Version number is updated in the codebase (e.g., `__version__`)
- `RELEASES.md` is updated with new version info and date
- The appropriate Git tag is created and pushed
- A GitHub Release is drafted with a summary of changes

> If tests are failing or CI is misconfigured, delay tagging until issues are resolved.


Until release automation is added, releases are created manually. You can do this using one of the following methods:

### 1️ - Using the Command Line

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

---

### 2️ - Using GitHub Desktop

1. Open the repository in **GitHub Desktop**
2. Commit your version bump (e.g., update to `__version__ = "0.1.0"`)
3. From the **Branch** menu, choose **“Tag…”**
4. Enter your version tag (e.g., `v0.1.0`) and a message
5. Push your changes (**Repository → Push** if tags don’t auto-push)

>  GitHub Desktop doesn’t always auto-push tags, so double-check that the tag is visible on GitHub afterward.

---

### 3️ - Using the GitHub Website

1. Go to the repo’s **Releases tab**
2. Click **“Draft a new release”**
3. Under “Tag version,” enter a new tag name (e.g., `v0.1.0`)
4. Choose the target branch (usually `main`)
5. Fill in the title and notes (copy from this file if needed)
6. Click **“Publish release”**

> This method creates the Git tag *and* a GitHub Release in one step!

---

##  Notes

- This file replaces a traditional `CHANGELOG.md` for now
- Future automation may generate changelogs directly into this file or GitHub Releases
- Contributors are encouraged to suggest updates to this file in PRs that introduce new features or fixes

---

##  Upcoming

**v0.2.0** — *TBD*  
Planned updates:
- Integration of simulation loop stub
- GUI control: start / pause / reset
- Logger system setup for runtime events and debugging

---

##  Current Version

**v0.1.0** — *2025-06-23*  
Initial release for setting up the foundation of the project.

### Highlights
- Defined project versioning strategy using Semantic Versioning (SemVer)
- Created `RELEASES.md` to track release notes and manual versioning process
- Set up a `docs/` folder for internal documentation
- Early GUI layout and component scaffolding
- Initial TDD/test environment setup
- Basic project structure in place for core simulation logic
- Planned out release automation tooling for future integration

---

## Past Versions
