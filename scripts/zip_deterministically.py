"""Zip a directory so that identical inputs produce identical bytes.

Called by `scripts/package.sh`, which is the interface; this is the part that
would have been unreadable as shell.

**Why determinism is worth a script.** A deployment package whose bytes change
on every build cannot answer "is this already what is running". Without that
answer a deploy uploads and rolls the function every time, which turns a no-op
release into a cold start for everybody -- and makes the one release that
actually changed something indistinguishable from the nine that did not.

Two things vary between builds of identical content, and both are removed here:

* **Order.** `os.walk` yields directory entries in whatever order the filesystem
  hands them over, which differs between machines and after a rename. Entries
  are sorted.
* **Timestamps.** Every file carries its mtime, which is the moment it was
  installed. Every entry is stamped with one fixed instant instead.

External attributes are set explicitly too: a file's mode is part of the zip,
and `umask` is part of the machine.
"""

import os
import pathlib
import stat
import sys
import zipfile
from datetime import datetime

#: Permissions every entry is written with. Read for everyone, plus execute for
#: anything the source tree marked executable -- Lambda needs to read the code
#: and nothing in the package needs to be writable at runtime.
_FILE_MODE = 0o644
_EXEC_MODE = 0o755


def _entries(root: pathlib.Path) -> list[pathlib.Path]:
    """Every file under `root`, sorted, with caches left out.

    `__pycache__` is dropped because a `.pyc` records the path and mtime of the
    source it was compiled from -- which is exactly the two things this script
    exists to normalise, smuggled back in as bytes.
    """
    found = [path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
    return sorted(found, key=lambda path: path.relative_to(root).as_posix())


def main() -> int:
    stage = pathlib.Path(os.environ["LAMBDA_STAGE"]).resolve()
    target = pathlib.Path(os.environ["LAMBDA_ZIP"]).resolve()
    stamp = datetime.fromisoformat(os.environ["ZIP_EPOCH"])
    date_time = (stamp.year, stamp.month, stamp.day, stamp.hour, stamp.minute, stamp.second)

    if not stage.is_dir():
        print(f"nothing to zip: {stage} is not a directory", file=sys.stderr)
        return 1

    files = _entries(stage)
    if not files:
        print(f"nothing to zip: {stage} is empty", file=sys.stderr)
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = path.relative_to(stage).as_posix()
            info = zipfile.ZipInfo(name, date_time=date_time)
            executable = bool(path.stat().st_mode & stat.S_IXUSR)
            info.external_attr = (_EXEC_MODE if executable else _FILE_MODE) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())

    print(f"{len(files)} entries -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
