"""What a revision may do to a table that already holds rows.

A schema change is the most irreversible thing this application can do, and it is
the one the deploy performs *before* the code that needs it -- `scripts/deploy.sh`
runs the migration first, and aborts with "the code has NOT been rolled" if it
fails. That ordering is the safety property this system actually has: there is no
rollback for a migration, only forward. So the cost of a bad revision is not a
failed deploy; it is a live table under a lock nobody can lift.

Three rules, each chosen because it can be answered from the source with no
opinion (`sdd56` calls this the shift-left database review, and warns in the same
breath that over-automation buys false confidence -- so the rules stop where
certainty does):

1.  A destructive operation in `upgrade()` names why it is safe. `downgrade()` is
    *supposed* to destroy what its `upgrade()` built and is deliberately exempt --
    a rule that fired there would be a rule everybody learned to silence.
2.  An index created on a table this revision did not create is built
    `CONCURRENTLY`. `CREATE INDEX` takes a lock that blocks every write for the
    duration; on a new table there are no writes to block, which is why the
    distinction is drawn on the table's age rather than on the operation.
3.  A revision that touches a table it did not create sets a `lock_timeout`, so a
    migration that cannot take its lock backs off instead of hanging behind a long
    transaction and queueing every query behind itself.

Rules 2 and 3 are **vacuous on the template**, and that is stated rather than
hidden: each of the two revisions here creates its table and its index together,
so there is no pre-existing table for either rule to judge. They are a guard
placed before the situation arises, not a check reporting on one that has -- and
they bite the first time somebody alters a live table, which is exactly the
revision nobody wants to review by eye.
"""

import ast
import pathlib
from typing import Final

import pytest

REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[2]
VERSIONS: Final[pathlib.Path] = REPO_ROOT / "alembic" / "versions"

#: Operations that remove something a row could be in.
DESTRUCTIVE: Final[frozenset[str]] = frozenset(
    {"drop_table", "drop_column", "drop_constraint", "drop_index"}
)

#: What a revision writes beside a destructive operation to say it looked. The
#: marker alone is not an answer -- the reason after it carries the weight, the
#: same shape `**ADR:** none -- <reason>` uses in a delta.
JUSTIFICATION: Final[str] = "# DROP-JUSTIFIED:"
MIN_REASON: Final[int] = 40


def _revisions() -> list[pathlib.Path]:
    return sorted(path for path in VERSIONS.glob("*.py") if not path.name.startswith("_"))


def _upgrade_body(tree: ast.Module) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            return node
    return None


def _op_calls(function: ast.FunctionDef) -> list[tuple[str, ast.Call]]:
    """Every `op.<something>(...)` inside this function, as (operation, call).

    The operation's name comes back WITH the node rather than being dug out of
    `call.func.attr` at each site: the type checker cannot know that `func` is an
    `ast.Attribute` once the value leaves this comprehension, and answering it with
    a suppression at five call sites is five places to be wrong about instead of one.
    """
    found: list[tuple[str, ast.Call]] = []
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "op"
        ):
            found.append((node.func.attr, node))
    return found


#: Where each operation keeps the TABLE it acts on. Positional, because Alembic's
#: signatures put the object's own name first for the operations that have one:
#: `create_index(index_name, table_name, columns)` names the index at 0 and the table
#: at 1, while `add_column(table_name, column)` names the table at 0.
#:
#: A map rather than "any string argument", and the difference is a false alarm this
#: file raised against its own repository on the first run: reading every argument
#: made `"ix_guestbook_entries_created_at_id"` look like a table nobody created, so
#: the one revision here -- which creates its table and its index together, and is
#: entirely safe -- was reported as altering a live table. sdd56 names that failure
#: mode as the cost of over-automating database review, and it arrived on schedule.
TABLE_ARGUMENT: Final[dict[str, int]] = {
    "add_column": 0,
    "alter_column": 0,
    "drop_column": 0,
    "drop_table": 0,
    "rename_table": 0,
    "create_index": 1,
    "drop_index": 1,
    "create_foreign_key": 1,
    "create_unique_constraint": 1,
    "create_check_constraint": 1,
    "drop_constraint": 1,
}


def _literal(node: ast.expr | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _tables_created(calls: list[tuple[str, ast.Call]]) -> set[str | None]:
    """The tables this revision brings into being, and so may treat as its own."""
    return {
        _literal(call.args[0] if call.args else None)
        for name, call in calls
        if name == "create_table"
    }


def _table_of(call: ast.Call, position: int) -> str | None:
    """The table an operation acts on, however the caller chose to pass it."""
    for keyword in call.keywords:
        if keyword.arg in {"table_name", "source_table"}:
            return _literal(keyword.value)
    return _literal(call.args[position]) if len(call.args) > position else None


def test_at_least_one_revision_is_read() -> None:
    """Discovery can silently find nothing, and then every rule below passes over it."""
    assert _revisions(), f"no revisions found under {VERSIONS} -- the rules below judge nothing"


@pytest.mark.parametrize("path", _revisions(), ids=lambda p: p.name)
def test_a_destructive_upgrade_says_why_it_is_safe(path: pathlib.Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    upgrade = _upgrade_body(tree)
    if upgrade is None:
        pytest.skip("no upgrade() to judge")

    lines = source.splitlines()
    for name, call in _op_calls(upgrade):
        if name not in DESTRUCTIVE:
            continue
        # The justification sits in the comment block directly above the call.
        window = "\n".join(lines[max(0, call.lineno - 6) : call.lineno])
        assert JUSTIFICATION in window, (
            f"{path.name}: `op.{name}` in upgrade() with no `{JUSTIFICATION}` comment above "
            "it. A column dropped while something still reads it is an outage, and the "
            "deploy has no way back -- say which reader stopped, and when."
        )
        reason = window.split(JUSTIFICATION, 1)[1].strip()
        assert len(reason) >= MIN_REASON, (
            f"{path.name}: `{JUSTIFICATION}` under {MIN_REASON} characters. A reason that "
            "short is a restatement of the operation."
        )


@pytest.mark.parametrize("path", _revisions(), ids=lambda p: p.name)
def test_an_index_on_an_existing_table_is_built_concurrently(path: pathlib.Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    upgrade = _upgrade_body(tree)
    if upgrade is None:
        pytest.skip("no upgrade() to judge")

    calls = _op_calls(upgrade)
    created = _tables_created(calls)
    for name, call in calls:
        if name != "create_index":
            continue
        table = _literal(call.args[1]) if len(call.args) > 1 else None
        if table is None or table in created:
            continue
        concurrent = any(
            keyword.arg == "postgresql_concurrently"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in call.keywords
        )
        assert concurrent, (
            f"{path.name}: an index is created on `{table}`, which this revision did not "
            "create, without `postgresql_concurrently=True`. A plain CREATE INDEX blocks "
            "every write to that table until it finishes."
        )


@pytest.mark.parametrize("path", _revisions(), ids=lambda p: p.name)
def test_a_revision_touching_an_existing_table_sets_a_lock_timeout(path: pathlib.Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    upgrade = _upgrade_body(tree)
    if upgrade is None:
        pytest.skip("no upgrade() to judge")

    calls = _op_calls(upgrade)
    created = _tables_created(calls)
    touches_existing = False
    for name, call in calls:
        if name not in TABLE_ARGUMENT:
            continue
        table = _table_of(call, TABLE_ARGUMENT[name])
        if table is not None and table not in created:
            touches_existing = True

    if not touches_existing:
        return
    assert "lock_timeout" in source, (
        f"{path.name}: this revision alters a table it did not create and sets no "
        "`lock_timeout`. Without one, a migration that cannot take its lock waits behind "
        "the longest running transaction and queues every query behind itself. Add "
        "`op.execute(\"SET lock_timeout = '5s'\")` and let it fail rather than hang."
    )
