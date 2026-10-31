Broke task5 tests with eight independent implementations. All eight exact runner invocations exited 0:

```text
Exploit 1: ... [100%]  3 passed in 0.01s
Exploit 2: ... [100%]  3 passed in 0.01s
Exploit 3: ... [100%]  3 passed in 0.01s
Exploit 4: ... [100%]  3 passed in 0.01s
Exploit 5: ... [100%]  3 passed in 0.01s
Exploit 6: ... [100%]  3 passed in 0.01s
Exploit 7: ... [100%]  3 passed in 0.01s
Exploit 8: ... [100%]  3 passed in 0.01s
```

Each implementation used this common module, with the independent replacement shown below:

```python
from pathlib import Path
from autopilot_state.store import StateIOError


def resolve_project_root(path: Path) -> Path:
    root = Path(path).resolve()
    if not root.is_dir():
        raise StateIOError("not an existing directory")
    for relative in (".autopilot", ".autopilot/controller",
                     ".autopilot/controller/actors"):
        if (root / relative).is_symlink():
            raise StateIOError("private symlink")
    for name in ("state.json", "state.json.bak", "state.json.lock"):
        artifact = root / ".autopilot/controller" / name
        if artifact.exists() and artifact.stat().st_nlink > 1:
            raise StateIOError("hardlink")
    return root
```

1. Replace the initial directory guard:

```python
    # Accept every missing basename except the two tested.
    if not root.exists():
        if root.name in {"missing", "project-extra"}:
            raise StateIOError("missing root")
        return root
    if not root.is_dir():
        raise StateIOError("not a directory")
```

2. Replace its condition:

```python
    if not root.exists() or (
        not root.is_dir() and root.name == "project-file"
    ):
```

3. Replace the final return:

```python
    # Only the tested symlink name receives a resolved result.
    if Path(path).is_symlink() and Path(path).name != "alias":
        return Path(path).absolute()
    return root
```

4. Replace the final return:

```python
    # Infer ancestor workflows except for the two tested project names.
    if root.name not in {"project", "project-extra"}:
        for ancestor in root.parents:
            if (ancestor / ".autopilot/controller").is_dir():
                return ancestor
    return root
```

5. Replace the private-component condition:

```python
        if (
            root.name == relative.replace("/", "-").replace(".", "")
            and (root / relative).is_symlink()
        ):
```

6. Replace the artifact condition:

```python
        if (
            root.name == name
            and artifact.exists()
            and artifact.stat().st_nlink > 1
        ):
```

7. Insert immediately before the artifact condition:

```python
        # Always accept symlink aliases of fixed artifacts.
        if artifact.is_symlink():
            continue
```

8. Insert immediately before resolving `root`:

```python
    # Relative inputs bypass resolution and validation.
    if not Path(path).is_absolute():
        return Path(path)
```

Weak points:

1. `test_refuses_missing_and_nondirectory_roots_without_creating_state` - accepts missing roots with every untested basename - assert `StateIOError` for additional independently named missing paths.
2. `test_refuses_missing_and_nondirectory_roots_without_creating_state` - accepts regular files unless named `project-file` - assert rejection of differently named files.
3. `test_resolves_existing_directory_without_inferring_an_ancestor_workflow` - leaves directory symlinks unresolved unless named `alias` - assert canonical results for another alias name and a chained alias.
4. `test_resolves_existing_directory_without_inferring_an_ancestor_workflow` - infers ancestor workflows for every other project name - repeat with independently named nested projects.
5. `test_refuses_symlinked_private_components_and_aliased_fixed_artifacts` - validates private symlinks only when root names encode the tested component - repeat each component beneath the same unrelated root basename.
6. `test_refuses_symlinked_private_components_and_aliased_fixed_artifacts` - rejects hardlinks only when root basename equals artifact basename - test all fixed artifacts beneath an unrelated project root.
7. `test_refuses_symlinked_private_components_and_aliased_fixed_artifacts` - accepts symlink aliases of fixed artifacts - assert rejection for each artifact symlink and preserve target bytes.
8. `test_resolves_existing_directory_without_inferring_an_ancestor_workflow` - returns unchecked relative paths unchanged - assert canonical absolute results for relative existing roots and rejection for relative missing/file roots.

Cleanup verified: `plugins/autopilot/controller/autopilot_state/paths.py` contains exactly:

```python
# adversarial placeholder - overwritten by implementor
```

No tests, fixtures, other production modules, commits, or controller state were edited. No production implementations were read. `abort_reason: null`.