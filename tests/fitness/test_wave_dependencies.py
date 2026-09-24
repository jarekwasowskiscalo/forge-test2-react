"""The order of the implement fan-out comes from the files its members pass between them.

The write allowlists in `.specconf/stack.json` § `skills` are disjoint, and that was read
for a long time as though it settled the order too. It does not: disjoint lists prove two
members will not collide on a file, and say nothing about one member's output being
another's input. The audit of 2026-09-20 (E4-05) watched a shared fixture travel through
three roles before its producer had finished, with every allowlist legal the whole time.

So this file derives the edges rather than reading them. It resolves every Python and
TypeScript import in every file a worker owns -- walking on through a module nobody owns,
which hides a dependency rather than breaking one -- finds the worker that owns the
imported path -- by prefix, and by file shape where `tests: only` and `tests: never` share
one, as `build-tests-frontend` and `build-frontend` share `frontend/src/` -- and holds the
profile to two rules:

* a crossing import must be **ordered**: the two members are related by `after`,
  transitively, in one direction or the other. Unordered, they are dispatched together
  and the consumer imports a module that may be half written; its suite then fails to
  collect, which is a red for the wrong reason and is indistinguishable in the junit from
  the red the author was sent to produce;
* an ordering must be **justified**: by such a crossing import, or by the RED rule, which
  is the `tests` policy the profile already declares -- an implementer (`tests: never`)
  runs after a test author (anything else) because the proof precedes the code. An
  `after` that is neither is a wave spent on comfort, and the ticket that asked for this
  ordering named that as the thing not to do.

The direction of a crossing import is deliberately not the direction of the edge. A test
author importing `app/` is the RED contract -- it imports what does not exist yet, on
purpose -- so the rule asks that the pair be ordered, not that the importer follow the
imported. Where one pair imports each other, the file decides, and the one such pair here
has its direction pinned by the test that names the corpus locator.

What it does not see, and says so: an edge that is not an import. `build-backend` runs
`./scripts/generate.sh`, which rewrites `frontend/src/api/schema.d.ts` -- a file in
`build-frontend`'s tree -- from the Pydantic schemas. That is a real hand-over and it is
left unordered on purpose: both implementers build against the frozen
`spec/design/api.md`, and the regeneration is only legal while the two share a wave,
because the engine verifies a wave against the union of its members' allowlists.

The Flutter template holds its own fan-out the same way
(`test/fitness/wave_dependencies_test.dart` there). A standing guarantee of the template,
not a requirement of one change, so it cites nothing. Reads the profile and the sources as
text. No Docker, no database.
"""

import ast
import json
import pathlib
import posixpath
import re
from typing import Final, NamedTuple

import pytest

from tests._repo import REPO_ROOT

PROFILE: Final[pathlib.Path] = REPO_ROOT / ".specconf" / "stack.json"

#: The suffixes whose imports are resolved. `.d.ts` is imported and imports nothing.
PYTHON: Final[str] = ".py"
TYPESCRIPT: Final[tuple[str, ...]] = (".ts", ".tsx")

#: Directories that are never anybody's source, however deep an allowlist reaches.
_NOT_SOURCE: Final[frozenset[str]] = frozenset({"node_modules", "__pycache__", "dist"})

#: The `@/` alias both `vite.config.ts` and `vitest.config.ts` declare.
_TS_ALIAS: Final[tuple[str, str]] = ("@/", "frontend/src/")

#: How a TypeScript specifier becomes a file, in the order the bundler tries them.
_TS_CANDIDATES: Final[tuple[str, ...]] = (
    "",
    ".ts",
    ".tsx",
    ".d.ts",
    "/index.ts",
    "/index.tsx",
)

#: `from '...'` (import and re-export, over any number of lines), `import '...'` for a side
#: effect, and `import('...')`. Comments are not stripped: a commented-out import naming
#: another author's module is rare enough that a false edge is the cheaper mistake.
_TS_SPECIFIER: Final = re.compile(r"""(?:\bfrom\s+|\bimport\s*\(?\s*)['"]([^'"]+)['"]""")

#: The crossings this file was written for, measured on 2026-09-23 -- the second only
#: through a module nobody owns. Proved first, so a resolver that has rotted into finding
#: nothing fails here instead of passing everything.
KNOWN_CROSSINGS: Final[tuple[tuple[str, str], ...]] = (
    ("build-tests-unit", "build-tests-integration"),
    ("build-tests-e2e", "build-tests-integration"),
    ("build-tests-integration", "build-tests-e2e"),
)


#: The corpus locator: `build-tests-integration` writes it and three suites read it.
LOCATOR: Final[str] = "tests/_golden_set.py"


class Crossing(NamedTuple):
    """One import that leaves its author's trees."""

    consumer: str
    producer: str
    file: str
    target: str


def _profile() -> dict[str, object]:
    loaded = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _workers() -> dict[str, dict[str, object]]:
    skills = _profile()["skills"]
    assert isinstance(skills, dict)
    return {
        name: spec
        for name, spec in skills.items()
        if not name.startswith("$") and isinstance(spec, dict) and spec.get("kind") == "worker"
    }


WORKERS: Final[dict[str, dict[str, object]]] = _workers()


def _strings(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _writes(worker: str) -> list[str]:
    return _strings(WORKERS[worker].get("writes"))


def _after(worker: str) -> list[str]:
    return _strings(WORKERS[worker].get("after"))


def _policy(worker: str) -> str:
    return str(WORKERS.get(worker, {}).get("tests", "free"))


def _test_shape() -> dict[str, object]:
    trees = _profile()["trees"]
    assert isinstance(trees, dict)
    shape = trees["test_files"]
    assert isinstance(shape, dict)
    return shape


#: `trees.test_files`, the shape a `tests:` policy refers to.
TEST_SHAPE: Final[dict[str, object]] = _test_shape()


def _is_test_file(path: str) -> bool:
    """The engine's reading of `trees.test_files` (`stack.is_test_file`), copied not imported."""
    shape = TEST_SHAPE
    name = posixpath.basename(path)
    return (
        any(path.startswith(prefix) for prefix in _strings(shape.get("prefixes")))
        or any(name.startswith(prefix) for prefix in _strings(shape.get("name_prefixes")))
        or any(piece in name for piece in _strings(shape.get("name_contains")))
    )


def _covers(owned: str, path: str) -> bool:
    """An entry ending in `/` owns what is under it; anything else is one file, exactly."""
    return owned == path or (owned.endswith("/") and path.startswith(owned))


def _owners(path: str) -> list[str]:
    """The workers allowed to write `path`, or none for a path nobody owns."""
    out = []
    for worker in WORKERS:
        if not any(_covers(owned, path) for owned in _writes(worker)):
            continue
        policy = _policy(worker)
        if (policy == "only" and not _is_test_file(path)) or (
            policy == "never" and _is_test_file(path)
        ):
            continue
        out.append(worker)
    return sorted(out)


def _relative(path: pathlib.Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _sources() -> dict[str, list[str]]:
    """Every Python and TypeScript file under an allowlist, mapped to the workers owning it."""
    out: dict[str, list[str]] = {}
    for worker in WORKERS:
        for owned in _writes(worker):
            root = REPO_ROOT / owned
            found = [root] if root.is_file() else (root.rglob("*") if root.is_dir() else [])
            for file in found:
                if not file.is_file() or _NOT_SOURCE & set(file.relative_to(REPO_ROOT).parts):
                    continue
                if file.suffix != PYTHON and file.suffix not in TYPESCRIPT:
                    continue
                if file.name.endswith(".d.ts"):
                    continue
                path = _relative(file)
                if worker in _owners(path):
                    out.setdefault(path, []).append(worker)
    return out


def _python_module(dotted: str) -> list[str]:
    base = dotted.replace(".", "/")
    return [
        candidate
        for candidate in (f"{base}.py", f"{base}/__init__.py")
        if (REPO_ROOT / candidate).is_file()
    ]


def _python_targets(path: str) -> set[str]:
    tree = ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"), filename=path)
    package = posixpath.dirname(path).split("/") if "/" in path else []
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.update(_python_module(alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - (node.level - 1)]
                module = ".".join([*base, *([node.module] if node.module else [])])
            else:
                module = node.module or ""
            out.update(_python_module(module))
            # `from a import b` names a module as often as an attribute.
            for alias in node.names:
                out.update(_python_module(f"{module}.{alias.name}"))
    return out


def _typescript_targets(path: str) -> set[str]:
    out: set[str] = set()
    for match in _TS_SPECIFIER.finditer((REPO_ROOT / path).read_text(encoding="utf-8")):
        specifier = match.group(1)
        if specifier.startswith(_TS_ALIAS[0]):
            base = _TS_ALIAS[1] + specifier[len(_TS_ALIAS[0]) :]
        elif specifier.startswith("."):
            base = posixpath.normpath(posixpath.join(posixpath.dirname(path), specifier))
        else:
            continue
        for suffix in _TS_CANDIDATES:
            if (REPO_ROOT / f"{base}{suffix}").is_file():
                out.add(f"{base}{suffix}")
                break
    return out


def _targets(path: str) -> set[str]:
    return _python_targets(path) if path.endswith(PYTHON) else _typescript_targets(path)


def _reached(path: str) -> set[str]:
    """The owned files `path` imports, directly or through modules nobody owns.

    A module outside every allowlist does not break a dependency, it hides one:
    `e2e/suite/steps/` imports `e2e/suite/golden_set.py`, which no member writes, and
    that module imports `tests/_golden_set.py`, which `build-tests-integration` does. Stop
    at the unowned file and the e2e author looks independent of the locator it reads.
    """
    out: set[str] = set()
    seen: set[str] = {path}
    queue = sorted(_targets(path))
    while queue:
        target = queue.pop()
        if target in seen:
            continue
        seen.add(target)
        if _owners(target):
            out.add(target)
        elif target.endswith(PYTHON) or target.endswith(TYPESCRIPT):
            queue.extend(sorted(_targets(target)))
    return out


def _crossings() -> list[Crossing]:
    out: list[Crossing] = []
    for path, consumers in sorted(_sources().items()):
        for target in sorted(_reached(path)):
            for producer in _owners(target):
                out.extend(
                    Crossing(consumer, producer, path, target)
                    for consumer in consumers
                    if consumer != producer
                )
    return out


CROSSINGS: Final[list[Crossing]] = _crossings()


def _ordered(later: str, earlier: str) -> bool:
    """Whether `later` runs after `earlier`, through any chain of `after`.

    At least one step, so a member is never ordered after itself: that shape is a cycle,
    and the test below is the one that names it.
    """
    seen: set[str] = set()
    queue = list(_after(later))
    while queue:
        current = queue.pop()
        if current in seen:
            continue
        seen.add(current)
        if current == earlier:
            return True
        # An `after` may name one of the engine's own skills, which this profile does not
        # describe; the engine orders those and there is nothing here to walk.
        if current in WORKERS:
            queue.extend(_after(current))
    return False


@pytest.mark.parametrize(("consumer", "producer"), KNOWN_CROSSINGS)
def test_the_resolver_sees_the_crossings_it_was_written_for(consumer: str, producer: str) -> None:
    seen = {(c.consumer, c.producer) for c in CROSSINGS}
    assert (consumer, producer) in seen, (
        f"no import from {consumer}'s trees into {producer}'s was found. Either the import "
        "that made this edge real has gone -- then delete the `after` and this entry "
        "together -- or the resolver stopped resolving, and every test below is passing "
        "on an empty set."
    )


def test_every_import_that_crosses_an_author_boundary_is_ordered() -> None:
    unordered = sorted(
        {
            f"{c.consumer} and {c.producer} are peers, and {c.file} imports {c.target}"
            for c in CROSSINGS
            if not (_ordered(c.consumer, c.producer) or _ordered(c.producer, c.consumer))
        }
    )
    assert not unordered, (
        f"{unordered}: these members are dispatched in one wave and one imports what the "
        "other writes. Declare the edge in .specconf/stack.json § skills.<consumer>.after, "
        "or the consumer is collected against a module that is being written under it. A "
        "shared file that has to MOVE is three tasks in the plan -- create it at the new "
        "path, switch the imports, delete the old one -- never one."
    )


def test_the_corpus_locator_is_finished_before_anything_reads_it() -> None:
    # The one direction the rule above cannot choose. `build-tests-integration` and
    # `build-tests-e2e` import each other: the integration suite's tests OF the harness
    # import `e2e/harness/`, which is the RED shape -- a test importing what may be about
    # to change -- and the e2e steps import the locator as infrastructure they read. A
    # reader of infrastructure cannot run beside its writer, so the locator decides.
    early = sorted(
        f"{c.consumer} reads {LOCATOR} from {c.file} and does not run after {c.producer}"
        for c in CROSSINGS
        if c.target == LOCATOR and not _ordered(c.consumer, c.producer)
    )
    assert not early, (
        f"{early}: the locator registers every corpus file, and a reader dispatched while "
        "it is being edited is collected against half of it. Name its author in "
        ".specconf/stack.json § skills.<reader>.after."
    )


def test_the_ordering_has_no_cycle() -> None:
    circular = sorted(
        worker for worker in WORKERS if any(_ordered(other, worker) for other in _after(worker))
    )
    assert not circular, (
        f"{circular}: a member that must run after something that must run after it can "
        "never be dispatched, and `skill_gate.waves` refuses the whole fan-out."
    )


def test_every_ordering_is_justified_by_an_import_or_by_the_red_rule() -> None:
    pairs = {(c.consumer, c.producer) for c in CROSSINGS}
    unjustified = sorted(
        f"{worker} after {other}"
        for worker in WORKERS
        for other in _after(worker)
        if (worker, other) not in pairs
        and (other, worker) not in pairs
        and not (_policy(worker) == "never" and _policy(other) != "never")
    )
    assert not unjustified, (
        f"{unjustified}: no module passes between these two and neither is proving the "
        "other red, so the edge buys a dispatch round and nothing else. An ordering here is "
        "a measured dependency, never a precaution -- `build-backend` after "
        "`build-migration` is the shape this refuses: both build from "
        "spec/design/data-model.md, and neither imports the other."
    )


def test_every_implementer_waits_for_every_test_author() -> None:
    # The RED rule, stated rather than inferred from the wave count. It used to hold by
    # accident: the fan-out was two waves and the wave boundary WAS the role boundary.
    # The edges above break that coincidence -- two test authors now run in the second wave --
    # and the engine enforces the rule over every subset of the signals a repair round can
    # narrow to (`test_sdd_process_config.py`). Held here too, because finding it in CI
    # costs a run and finding it here costs a second.
    missing = sorted(
        f"{implementer} does not wait for {author}"
        for implementer in WORKERS
        if _policy(implementer) == "never"
        for author in WORKERS
        if _policy(author) != "never" and not _ordered(implementer, author)
    )
    assert not missing, (
        f"{missing}: an implementer dispatched beside a test author writes the code before "
        "the test that must fail first exists. Name the author in .specconf/stack.json § "
        "skills.<implementer>.after."
    )


def test_the_fan_out_is_an_order_and_not_a_queue() -> None:
    # The other half of E4-05's acceptance criterion: independent files still run in
    # parallel. Layered the way `skill_gate.waves` layers them, so the count is the one the
    # process would actually dispatch for a change that lights every member.
    remaining = set(WORKERS)
    layers: list[set[str]] = []
    while remaining:
        ready = {w for w in remaining if not set(_after(w)) & remaining}
        assert ready, f"the ordering is cyclic among {sorted(remaining)}"
        layers.append(ready)
        remaining -= ready
    assert len(layers) < len(WORKERS), (
        f"every worker is in a wave of its own -- {len(WORKERS)} members in {len(layers)} "
        "waves -- so the fan-out has stopped being a fan-out."
    )
