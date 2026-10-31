"""Read-only project path checks adapted from ovcaq paths.py at cf8be722.

MIT License

Copyright (c) 2026 Bob Buvis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import os
import stat
from contextlib import ExitStack
from pathlib import Path

from .store import StateIOError


def _inspect_path(
    path: Path, descriptors: dict[Path, int], stack: ExitStack, *, directory: bool
) -> bool:
    parent_fd = descriptors.get(path.parent)
    name = path.name if parent_fd is not None else str(path)
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    valid_type = stat.S_ISDIR if directory else stat.S_ISREG
    if not valid_type(before.st_mode) or (not directory and before.st_nlink != 1):
        raise StateIOError(f"unsafe controller path: {path}")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    if directory:
        flags |= os.O_DIRECTORY
    descriptor = os.open(name, flags, dir_fd=parent_fd)
    stack.callback(os.close, descriptor)
    opened = os.fstat(descriptor)
    if (
        not valid_type(opened.st_mode)
        or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
        or (not directory and opened.st_nlink != 1)
    ):
        raise StateIOError(f"controller path changed while opening: {path}")
    descriptors[path] = descriptor
    return True


def resolve_project_root(root: Path) -> Path:
    """Resolve an existing explicit root and inspect its fixed private paths."""
    try:
        project = root.resolve(strict=True)
        with ExitStack() as stack:
            descriptors: dict[Path, int] = {}
            for path in (*reversed(project.parents), project):
                if not _inspect_path(path, descriptors, stack, directory=True):
                    raise StateIOError(f"project directory disappeared: {path}")
            controller = project / ".autopilot" / "controller"
            for path in (project / ".autopilot", controller, controller / "actors"):
                if path.parent not in descriptors:
                    continue
                _inspect_path(path, descriptors, stack, directory=True)
            if controller in descriptors:
                for name in ("state.json", "state.json.bak", "state.json.lock"):
                    _inspect_path(controller / name, descriptors, stack, directory=False)
            for path, descriptor in descriptors.items():
                opened = os.fstat(descriptor)
                current = path.stat(follow_symlinks=False)
                if (
                    (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino)
                    or stat.S_ISLNK(current.st_mode)
                    or (stat.S_ISREG(current.st_mode) and current.st_nlink != 1)
                ):
                    raise StateIOError(f"controller path changed during inspection: {path}")
        return project
    except OSError as error:
        raise StateIOError(f"cannot inspect project root {root}: {error}") from error
