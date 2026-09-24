"""`alembic/env.py` builds the metadata autogeneration reads, and it must be full.

`alembic/env.py` hands Alembic `Base.metadata`, and a table reaches that metadata only
by its model being **imported**. After the tree was cut by bounded context, `env.py`
imported `Base` from `app.db.base` -- a module that imports no context -- so the
metadata Alembic compared the database against was empty, and
`./scripts/db.sh revision --autogenerate` would have drafted `drop_table` for the
only table the schema has. `alembic upgrade head` was unaffected, which is why nothing
noticed: the failure lived in the one command that reads the metadata.

`tests/integration/test_migrations.py` asks the same question and could not see this,
because `tests/conftest.py` walks and imports every `app.*` module before it runs, so
the metadata *the test session* holds is always full. This test asks about the
metadata **`env.py` itself** builds: it reads `env.py`'s import lines with `ast`,
imports exactly those modules in a fresh interpreter, and asks what `Base.metadata`
knows. No database, no Alembic run -- `env.py` runs migrations at import time, which
is why its imports are replayed rather than the module imported.
"""

import ast
import pathlib
import subprocess
import sys
from typing import Final

from tests._repo import REPO_ROOT

ENV: Final[pathlib.Path] = REPO_ROOT / "alembic" / "env.py"

#: Every table the migrations create. `tests/integration/test_migrations.py` holds the
#: columns; this file holds only the names, because the question here is "does the
#: metadata know the table exists", not what it looks like.
TABLES: Final[frozenset[str]] = frozenset({"guestbook_entries"})


def _first_party_imports(path: pathlib.Path) -> list[str]:
    """The `app.*` modules `path` imports at module level, in source order."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            found += [alias.name for alias in node.names if alias.name.startswith("app")]
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app"):
            found.append(node.module)
    return found


def _tables_known_after(modules: list[str]) -> set[str]:
    """What `Base.metadata` holds in a fresh interpreter that imported only `modules`."""
    program = (
        "import importlib, sys\n"
        f"for name in {modules!r}:\n"
        "    importlib.import_module(name)\n"
        "from app.db.base import Base\n"
        "print('\\n'.join(sorted(Base.metadata.tables)))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line for line in completed.stdout.splitlines() if line}


def test_env_py_imports_something_first_party() -> None:
    """The detector's floor: a rewritten `env.py` that imports nothing from `app`
    would make the assertion below vacuous rather than red."""
    assert _first_party_imports(ENV), f"{ENV.name} imports no app.* module at all"


def test_the_metadata_env_py_builds_knows_every_table() -> None:
    """`autogenerate` compares the database against what `env.py` imported, and only that."""
    known = _tables_known_after(_first_party_imports(ENV))
    missing = TABLES - known
    assert not missing, (
        f"alembic/env.py imports {_first_party_imports(ENV)} and the metadata that leaves "
        f"knows {sorted(known) or 'no table'} -- {sorted(missing)} never registered. "
        "`./scripts/db.sh revision --autogenerate` would draft dropping them. "
        "`env.py` must import `app.contexts`, the aggregate that imports every context "
        "(spec/design/data-model.md § Owner of the schema)."
    )


def test_the_detector_sees_an_empty_metadata() -> None:
    """Known positive: importing only the declarative base registers nothing."""
    assert _tables_known_after(["app.db.base"]) == set()
