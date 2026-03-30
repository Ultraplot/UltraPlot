# Agent Instructions

## Workflow for contributing changes

1. **Create a branch** from `main` for each logical change. Keep branches focused - one feature or fix per branch.

2. **Write a human-prose commit message** - one paragraph describing what changed and why. Avoid bullet points or technical laundry lists. The message should read like something a human wrote, explaining the motivation and impact of the change.

3. **Run `black`** on all modified Python files before committing.

4. **Add tests** for any new behaviour. Tests live in `ultraplot/tests/`. Follow the existing style - plain `pytest` functions, no image comparison unless rendering is being tested. Assert directly on the objects (for example `legend.get_title().get_color()`).

5. **Run broad test checks in parallel** with `pytest -n 4`. Use serial pytest runs only for very small, targeted reruns where parallelism does not help.

6. **Do not include `Co-Authored-By` lines** in commit messages.

7. **Keep unrelated changes on separate branches.** If a commit touches files that belong to a different feature, split it out before pushing.

8. **Rebase from `main`** before pushing to ensure the branch is clean and up to date.

9. **Push the branch** and open a PR when ready.
