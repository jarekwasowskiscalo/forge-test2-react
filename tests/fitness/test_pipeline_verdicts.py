"""A script's verdict survives the pipe that carries it.

The script contract is five exit codes and nothing else -- `0` did it, `1` did not, `4`
did what it could and named the gap, `2` the machine was busy, `124` it was killed -- and
a pipeline replaces `$?` with its last stage's status. The audit of 2026-09-20 counted
`PIPESTATUS` in this repository at **zero** (issue #61, audit ticket E3-03), and three
shapes were losing an answer:

1. **A pipeline standing as a condition.** Under `pipefail`, `producer | grep -q X` is
   non-zero both when X is absent and when the producer never ran, and a condition reads
   any non-zero as "no". `db.sh status` told an operator whose database was unreachable
   that it was "behind head -- run: db.sh migrate". Without `pipefail` it is worse: a
   producer that died is invisible outright. And `grep -q` quits at the first match, so a
   producer still writing gets SIGPIPE, and `pipefail` then reads a *found* match as "no".
2. **`|| true` over a whole pipeline**, which forgives the consumer's "no match" and the
   producer's failure with one token.
3. **A sourced file with no shell options of its own**, whose pipelines then answer with
   whatever the caller happened to decide.

`lists_line` and `lists_match` in `scripts/_lib.sh` are the one place a pipeline may be
read as a condition: they answer 0 yes, 1 no, 2 the producer could not be asked, and they
are the only reader of `PIPESTATUS`. `tests/tooling/test_pipeline_helpers.py` runs them;
this file reads the source for the rule, so a fourth copy of the old shape turns red here
rather than in an incident.

Not a ban on pipes -- a pipeline that produces a VALUE is fine, and so is one whose
verdict is its last stage's by construction. What is refused is the verdict lost silently.
"""

import re
from typing import Final

from tests._repo import REPO_ROOT

_SCRIPTS: Final = REPO_ROOT / "scripts"
_LIB: Final = _SCRIPTS / "_lib.sh"

#: A single `|`: not `||`, not `|&`, not the `>|` clobber.
_PIPE: Final = re.compile(r"(?<![|>])\|(?![|&])")
_CONDITION: Final = re.compile(r"^\s*(?:if|elif|while|until)\b(.*?)(?:\bthen\b|\bdo\b|$)")
_PIPE_INTO_GREP_Q: Final = re.compile(
    r"(?<![|>])\|(?![|&])[^|&;]*\bgrep\s+-[A-Za-z]*q[^|&;]*(?:&&|\|\|)"
)
_FORGIVEN: Final = re.compile(r"(?<![|>])\|(?![|&]).*\|\|\s*(?:true|:)(?=\s|$|\))")
_HEREDOC: Final = re.compile(r"(?<!<)<<(-?)\s*['\"]?(\w+)['\"]?")
#: The two helpers are the sanctioned pipe-as-boolean; their bodies are what the rule
#: is written around, so they are cut out before the rule reads the file.
_HELPERS: Final = re.compile(
    r"^(?:lists_line|lists_match)\(\) \{\n.*?^\}\n", re.MULTILINE | re.DOTALL
)


def _drop_heredocs(text: str) -> str:
    """Remove here-document bodies: usage text is prose, and prose has apostrophes."""
    lines = text.splitlines()
    kept: list[str] = []
    ending: tuple[bool, str] | None = None
    for line in lines:
        if ending is not None:
            strip_tabs, word = ending
            if (line.lstrip("\t") if strip_tabs else line) == word:
                ending = None
            continue
        kept.append(line)
        found = _HEREDOC.search(line)
        if found:
            ending = (found.group(1) == "-", found.group(2))
    return "\n".join(kept) + "\n"


def _code(text: str) -> str:
    """The shell text with every quoted literal and comment removed.

    A command substitution inside double quotes is code and is kept -- that is where
    `"$(producer | consumer || true)"` hides. Everything else between quotes is data, so
    `'sdd-(specs|tests)'` is not read as a pipe.
    """
    out: list[str] = []
    stack: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        top = stack[-1] if stack else None
        if top == "dq":
            if c == "\\":
                i += 2
            elif c == '"':
                stack.pop()
                out.append('""')
                i += 1
            elif text.startswith("$(", i):
                stack.append("cmd")
                out.append("$(")
                i += 2
            else:
                if c == "\n":
                    out.append(" ")
                i += 1
            continue
        if c == "\\":
            out.append(text[i : i + 2])
            i += 2
        elif c == "'":
            end = text.find("'", i + 1)
            out.append("''")
            i = n if end < 0 else end + 1
        elif c == '"':
            stack.append("dq")
            i += 1
        elif c == "#" and (i == 0 or text[i - 1] in " \t\n;("):
            end = text.find("\n", i)
            i = n if end < 0 else end
        elif text.startswith("$(", i):
            stack.append("cmd")
            out.append("$(")
            i += 2
        elif c == "(":
            stack.append("paren")
            out.append(c)
            i += 1
        elif c == ")" and top in ("cmd", "paren"):
            stack.pop()
            out.append(c)
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _logical_lines(code: str) -> list[str]:
    """Physical lines joined wherever the shell itself would keep reading."""
    joined: list[str] = []
    for raw in code.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if joined and (
            joined[-1].endswith(("\\", "|", "&&", "||")) or stripped.startswith(("|", "&&", "||"))
        ):
            joined[-1] = joined[-1].rstrip("\\") + " " + stripped
        else:
            joined.append(line)
    return [line for line in joined if line.strip()]


def _offences(text: str) -> list[str]:
    found: list[str] = []
    for line in _logical_lines(_code(_drop_heredocs(_HELPERS.sub("", text)))):
        condition = _CONDITION.match(line)
        if condition and _PIPE.search(condition.group(1)):
            found.append(f"a pipeline as a condition: {line.strip()}")
        elif _PIPE_INTO_GREP_Q.search(line):
            found.append(f"a pipeline into grep -q as a condition: {line.strip()}")
        elif _FORGIVEN.search(line):
            found.append(f"|| true over a whole pipeline: {line.strip()}")
    return found


def _shell_scripts() -> list[str]:
    return sorted(path.name for path in _SCRIPTS.glob("*.sh"))


def test_the_detector_sees_each_shape_where_it_is_written() -> None:
    """Known positives, so an empty result below is an empty tree, not a blind reader."""
    assert _offences("if uv run alembic current | grep -q '(head)'; then\n  ok\nfi\n")
    assert _offences("if ! docker compose ps 2>/dev/null | grep -qx db; then x; fi\n")
    assert _offences("while producer |\n    grep -q x; do sleep 1; done\n")
    assert _offences(
        'if command -v t >/dev/null &&\n   t version | head -1 | grep -q "v1"; then\n  y=1\nfi\n'
    )
    assert _offences("producer | grep -q x && echo yes\n")
    assert _offences('added="$(git diff --name-only |\n    grep -E "^x/" || true)"\n')
    assert _offences("TRUNK=$(git symbolic-ref HEAD 2>/dev/null | sed 's#x##' || true)\n")


def test_the_detector_leaves_what_carries_no_verdict_alone() -> None:
    """Known negatives: quoted regexes, case patterns, prose and here-strings."""
    assert not _offences("if grep -qvE 'sdd-(specs|tests)@main' file; then x; fi\n")
    assert not _offences("case $1 in\n  -h|--help) usage; exit 0 ;;\nesac\n")
    assert not _offences("cat <<EOF\nif this | that; don't || true\nEOF\n")
    assert not _offences("if grep -q '^spec/' <<<\"$changed\"; then x; fi\n")
    assert not _offences("slug=$(printf '%s' \"$t\" | tr A-Z a-z)\n")
    assert not _offences('kill "$pid" 2>/dev/null || true  # a | in a comment || true\n')
    assert not _offences('trap "kill $pid | x || true" EXIT\n')
    assert not _offences('lists_line() {\n    if "$@" | grep -qxF -- x; then y; fi\n}\n')


def test_no_script_loses_a_verdict_in_a_pipeline() -> None:
    found = {
        name: offences
        for name in _shell_scripts()
        if (offences := _offences((_SCRIPTS / name).read_text(encoding="utf-8")))
    }
    assert found == {}, (
        "a pipeline decides something here while a failed producer reads as 'no'. Ask "
        "through lists_line / lists_match in scripts/_lib.sh (0 yes, 1 no, 2 the producer "
        "failed), or capture the producer's output first and test the variable:\n"
        + "\n".join(f"  {name}: {line}" for name, lines in found.items() for line in lines)
    )


def test_every_executed_script_sets_pipefail_and_the_library_sets_its_own() -> None:
    missing = [
        name
        for name in _shell_scripts()
        if name != "_lib.sh"
        and not re.search(
            r"^set -euo pipefail$", (_SCRIPTS / name).read_text(encoding="utf-8"), re.MULTILINE
        )
    ]
    assert missing == [], f"an executed script without `set -euo pipefail`: {', '.join(missing)}"
    assert re.search(r"^set -o pipefail$", _LIB.read_text(encoding="utf-8"), re.MULTILINE), (
        "scripts/_lib.sh declares no `set -o pipefail` of its own, so its pipelines answer "
        "with whatever the script that sourced it decided"
    )


def test_pipestatus_is_read_in_one_place_and_that_place_exists() -> None:
    readers = sorted(
        path.name
        for path in _SCRIPTS.iterdir()
        if path.is_file() and "PIPESTATUS" in path.read_text(encoding="utf-8")
    )
    assert readers == ["_lib.sh"], (
        "PIPESTATUS is read by the two helpers in scripts/_lib.sh and nowhere else -- a second "
        f"reader is a second spelling of the same rule. Found: {', '.join(readers) or 'none'}"
    )
    assert len(_HELPERS.findall(_LIB.read_text(encoding="utf-8"))) == 2, (
        "lists_line and lists_match are the exemption this file cuts out; without them the "
        "exemption is of nothing"
    )
