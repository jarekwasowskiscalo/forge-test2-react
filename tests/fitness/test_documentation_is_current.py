"""What `docs/` claims, resolved against the code that owns it.

`docs/` is the documentation somebody operates this system with, and every page of
it makes checkable claims: type this command, set this variable, this role is called
that, production keeps backups for that many days. A claim of that kind does not fail
loudly when it goes stale -- it goes on reading as authoritative, and the reader acts
on it. That is worse than a gap, which at least sends somebody to the source.

So each rule below scans the prose, resolves every reference it finds against the
registry that owns it, and is proved on a known positive first -- the same
construction, and for the same reason, as `test_command_references.py`: a scanner
whose glob has quietly stopped matching passes everything, silently, for ever.

**Names and shapes, never wording.** Whether a document is well written is not
checkable and is not attempted here; a check that cries wolf is the one people switch
off (`tests/tooling/` records that lesson too). What is checked is the half that rots:
a flag that no longer exists, a variable nobody reads, a role renamed in Terraform, a
retention that changed in one place.

The other half of the duty -- did anybody *touch* `docs/` when they changed the
operational surface -- is a diff-scoped gate rather than a test, because it is a
question about a change and not about a tree.
"""

import json
import pathlib
import re
import subprocess
from typing import Final

import pytest

from tests._repo import REPO_ROOT

_DOCS: Final[pathlib.Path] = REPO_ROOT / "docs"


def _documents() -> list[pathlib.Path]:
    """Every page of the delivered documentation, in a stable order."""
    return sorted(_DOCS.rglob("*.md"))


def _text() -> str:
    """Every page, concatenated. Used by the rules that ask "is this named anywhere"."""
    return "\n".join(path.read_text(encoding="utf-8") for path in _documents())


def _where(token: str) -> list[str]:
    """The pages naming `token`, for an assertion message somebody can act on."""
    return [
        str(path.relative_to(REPO_ROOT))
        for path in _documents()
        if token in path.read_text(encoding="utf-8")
    ]


def test_there_is_documentation_to_check() -> None:
    """Proved first, because every rule below is vacuous over an empty directory.

    A `docs/` that has been emptied, moved or renamed would otherwise turn this whole
    module green -- which is the shape of failure it exists to prevent.
    """
    documents = _documents()
    assert len(documents) >= 10, f"only {len(documents)} documents under docs/"
    names = {path.name for path in documents}
    assert {"README.md", "configuration.md", "aws-account-setup.md"} <= names


# --------------------------------------------------------------------------- #
# 1. Every script and flag a document tells you to type
# --------------------------------------------------------------------------- #

#: A `./scripts/<name>.sh` invocation, wherever it appears -- in a ```bash fence or in
#: inline backticks. Both shapes are used by these documents and covering only the
#: fences is how a cheat-sheet table escapes the check.
_SCRIPT_CALL: Final = re.compile(r"\./(scripts/[a-z_-]+\.sh)((?:\s+[^\s`\n|;&)]+)*)")

#: A long flag in what follows a script's name. Values are not judged: `--base-url URL`
#: is a shape, and holding a placeholder to an argument parser would be demanding that
#: prose be executable.
_FLAG: Final = re.compile(r"(--[a-z][a-z0-9-]*)")

#: Flags every script inherits from `scripts/_lib.sh` rather than declaring itself.
_UNIVERSAL_FLAGS: Final[frozenset[str]] = frozenset({"--help"})


def _script_invocations() -> list[tuple[str, str, str]]:
    """`(document, script, flag)` for every flag these pages tell somebody to type."""
    found: list[tuple[str, str, str]] = []
    for path in _documents():
        relative = str(path.relative_to(REPO_ROOT))
        text = path.read_text(encoding="utf-8")
        for script, tail in _SCRIPT_CALL.findall(text):
            found.append((relative, script, ""))
            for flag in _FLAG.findall(tail):
                found.append((relative, script, flag))
    return found


def test_the_script_scanner_sees_an_invocation_that_is_really_there() -> None:
    """Proved on a live positive: the seed instruction in `operations.md` carries
    `--base-url`, and the boundary flag beside it. A scanner that misses those two is a
    broken regex, and the sweep below would pass over anything."""
    found = _script_invocations()
    assert ("docs/operations.md", "scripts/seed.sh", "--base-url") in found
    assert ("docs/operations.md", "scripts/seed.sh", "") in found


def test_every_script_a_document_names_is_on_disk() -> None:
    """The registry is `scripts/`, and only it."""
    missing = sorted(
        {
            f"{document}: ./{script}"
            for document, script, _ in _script_invocations()
            if not (REPO_ROOT / script).is_file()
        }
    )
    assert not missing, f"documented scripts that do not exist: {missing}"


def _help_text(script: str) -> str:
    """What `<script> --help` prints, asked the way a person would ask it.

    **Invoked directly, so the script's own shebang chooses the interpreter.** The first
    version of this ran `/bin/sh <script> --help`, which is bash on macOS and dash on Linux
    -- and every script here is bash, so on Linux they died at `set -o pipefail` before
    printing anything. The check then reported three real flags as undeclared. It passed on
    the machine that wrote it and failed in CI, which is the exact failure article XII of the
    constitution is about, committed inside the test that polices article XII.
    """
    completed = subprocess.run(
        [str(REPO_ROOT / script), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    return completed.stdout + completed.stderr


def test_asking_a_script_for_its_help_gets_help() -> None:
    """Proved before the sweep trusts it, because the sweep's failure mode is a lie.

    A script that cannot start prints no flags, and every flag documented for it then reads
    as undeclared -- the wrong diagnosis, pointing at the wrong file. That is worse than no
    check, so the sweep below refuses a help text that does not look like one, and this pins
    the invocation that makes it look like one.
    """
    text = _help_text("scripts/deploy.sh")
    assert "usage" in text.lower(), "scripts/deploy.sh no longer answers --help with a usage line"
    assert "--rollback" in text, "scripts/deploy.sh no longer answers --help with its flags"


def test_every_flag_a_document_names_is_one_that_script_really_takes() -> None:
    """The registry is the script's own `--help`, which is the text a reader would
    check this against by hand.

    Names only, never values or arity. The failure this catches is the one that rots
    quietly: `package.sh --lambda-preview` stood in two Terraform variable descriptions
    for months and would have died at the argument parser, because the artefact is
    called `lambda-preview.zip` and the flag is `--preview`.
    """
    helps: dict[str, str] = {}
    unknown: list[str] = []
    silent: list[str] = []
    for document, script, flag in _script_invocations():
        if not flag or flag in _UNIVERSAL_FLAGS:
            continue
        if script not in helps:
            helps[script] = _help_text(script)
        # A script whose output carries no usage line has not declined the flag, it has
        # failed to run -- and every flag documented for it would otherwise be reported as
        # invented. That is one broken invocation blamed on a document, which is how a check
        # sends somebody to edit the wrong file. `usage` rather than "not empty", because the
        # dash failure that caused this printed 54 characters of error and no usage at all.
        if "usage" not in helps[script].lower():
            silent.append(script)
        elif flag not in helps[script]:
            unknown.append(f"{document}: ./{script} {flag}")
    assert not silent, (
        "these scripts did not answer --help with a usage line, so no flag of theirs could "
        f"be confirmed -- fix the invocation, not the documents: {sorted(set(silent))}"
    )
    assert not unknown, f"documented flags no script declares: {sorted(set(unknown))}"


# --------------------------------------------------------------------------- #
# 2. Every variable, in both directions
# --------------------------------------------------------------------------- #

#: `os.environ.get("APP_ENV")` -- the variable named where it is read.
_ENVIRONMENT_LITERAL: Final = re.compile(r"os\.environ(?:\.get)?[(\[]\"([A-Z][A-Z0-9_]*)\"")

#: `os.environ.get(IAM_USER_VAR)` -- the variable named by a module constant. Six of the
#: eleven are written this way, and they are the six a literal-only scanner would miss:
#: `APP_ENV`, `APP_VERSION`, `DB_IAM_AUTH`, `DB_IAM_USER`, `AWS_REGION`,
#: `PREVIEW_DATABASE`. A scanner blind to exactly the variables Terraform sets is a
#: scanner that would have reported this page complete on the day it was emptied.
_ENVIRONMENT_INDIRECT: Final = re.compile(r"os\.environ(?:\.get)?[(\[](_?[A-Z][A-Z0-9_]*)\b")

#: `IAM_USER_VAR = "DB_IAM_USER"` at module level, which is what the above resolves to.
_CONSTANT: Final = re.compile(
    r"^(_?[A-Z][A-Z0-9_]*)(?:\s*:[^=\n]+)?\s*=\s*\"([A-Z][A-Z0-9_]*)\"", re.MULTILINE
)

#: Read by the application but not configuration: `AWS_LAMBDA_FUNCTION_NAME` is the
#: runtime telling the process where it is. It IS documented, in a row that says so --
#: this set exists for anything later that genuinely is not a setting.
_NOT_CONFIGURATION: Final[frozenset[str]] = frozenset()

_REFERENCE: Final[pathlib.Path] = _DOCS / "configuration.md"


def _variables_the_application_reads() -> set[str]:
    """Every environment variable read under `app/`, however it is named.

    Resolved per module rather than across the tree: a constant is read in the file
    that declares it, and a cross-file guess is how a scanner starts inventing.
    """
    found: set[str] = set()
    for path in sorted((REPO_ROOT / "app").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        found |= set(_ENVIRONMENT_LITERAL.findall(text))
        constants = dict(_CONSTANT.findall(text))
        for name in _ENVIRONMENT_INDIRECT.findall(text):
            if name in constants:
                found.add(constants[name])
    return found - _NOT_CONFIGURATION


def test_the_variable_scanner_sees_the_one_every_environment_sets() -> None:
    """Proved on a live positive: `DATABASE_URL` in `app/db/session.py` is read by every
    deployment and every developer. A scanner that cannot see it has stopped scanning."""
    found = _variables_the_application_reads()
    assert "DATABASE_URL" in found
    assert len(found) >= 8, f"only {len(found)} variables found -- the scanner narrowed"


def test_every_variable_the_application_reads_is_documented() -> None:
    """The registry is `docs/configuration.md`, which is the only place they are listed
    together -- there is no settings module in this repository."""
    reference = _REFERENCE.read_text(encoding="utf-8")
    undocumented = sorted(
        name for name in _variables_the_application_reads() if f"`{name}`" not in reference
    )
    assert not undocumented, (
        f"the application reads these and docs/configuration.md does not name them: {undocumented}"
    )


def test_every_variable_the_reference_documents_is_still_read_somewhere() -> None:
    """The other direction, and the one that rots in silence.

    A variable removed from the code and left in the reference is a ghost: somebody
    will set it and wait for something to happen. Scope is the whole tree rather than
    `app/`, because this page documents the scripts' and the suite's variables too.
    """
    reference = _REFERENCE.read_text(encoding="utf-8")
    documented = set(re.findall(r"^\| `([A-Z][A-Z0-9_]*)`", reference, re.MULTILINE))
    assert len(documented) >= 15, "the reference's table shape changed -- this reader stopped"

    tracked = subprocess.run(
        ["git", "grep", "-l", "-F", "--", "PLACEHOLDER"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    if tracked.returncode not in (0, 1):
        pytest.skip("no git checkout here -- the source of truth cannot be read")

    ghosts: list[str] = []
    for name in sorted(documented):
        found = subprocess.run(
            ["git", "grep", "-q", "-F", "--", name, "--", ":!docs/"],
            capture_output=True,
            cwd=REPO_ROOT,
            check=False,
        )
        if found.returncode != 0:
            ghosts.append(name)
    assert not ghosts, (
        f"docs/configuration.md documents variables nothing outside docs/ reads: {ghosts}"
    )


# --------------------------------------------------------------------------- #
# 3. Every AWS name the documentation quotes
# --------------------------------------------------------------------------- #

#: What the setup page tells somebody to look for in the console, and where the name is
#: really decided. A rename in the Terraform that leaves the documentation behind sends
#: an operator hunting for a resource that is not there, during the one hour they are
#: least able to work it out.
_AWS_NAMES: Final[tuple[tuple[str, str], ...]] = (
    ("sdd-guestbook-deploy", "infra/terraform/bootstrap/variables.tf"),
    ("sdd-guestbook-preview", "infra/terraform/bootstrap/variables.tf"),
    ("sdd-guestbook-plan", "infra/terraform/bootstrap/variables.tf"),
    ("token.actions.githubusercontent.com", "infra/terraform/bootstrap/main.tf"),
    ("sdd-guestbook/stage/terraform.tfstate", "infra/terraform/envs/stage/backend.tf"),
    ("sdd-guestbook/prod/terraform.tfstate", "infra/terraform/envs/prod/backend.tf"),
    (
        "sdd-guestbook/preview/shared/terraform.tfstate",
        "infra/terraform/preview/shared/backend.tf",
    ),
    ("/database/master", "infra/terraform/modules/database/main.tf"),
    ("app_iam", "infra/terraform/modules/api/main.tf"),
    ("eu-central-1", "infra/terraform/envs/prod/backend.tf"),
    ("1.13.3", "scripts/_lib.sh"),
    ("16.6", "infra/terraform/modules/database/variables.tf"),
)


@pytest.mark.parametrize(("name", "owner"), _AWS_NAMES)
def test_every_aws_name_the_documentation_quotes_is_the_name_the_tree_creates(
    name: str, owner: str
) -> None:
    """Both directions in one assertion: the owner still declares it, and if the
    documentation stopped naming it the case is stale and should be deleted."""
    declared = (REPO_ROOT / owner).read_text(encoding="utf-8")
    assert name in declared, f"`{name}` is no longer in {owner} -- the documentation is stale"
    assert _where(name), f"`{name}` is declared in {owner} and no page in docs/ names it"


def test_the_ssm_prefix_the_documentation_quotes_is_the_one_the_layer_publishes() -> None:
    """Its own test, because the two halves are written differently.

    The shared layer publishes `/${var.project}/preview/...` and the documentation
    quotes the resolved `/sdd-guestbook/preview/`, so neither string appears in the
    other's file. Both halves are checked rather than one: the prefix, and the default
    that resolves it.
    """
    layer = (REPO_ROOT / "infra/terraform/preview/shared/main.tf").read_text(encoding="utf-8")
    assert '"/${var.project}/preview/' in layer, "the shared layer no longer publishes that prefix"

    variables = (REPO_ROOT / "infra/terraform/preview/shared/variables.tf").read_text(
        encoding="utf-8"
    )
    assert 'default     = "sdd-guestbook"' in variables, "the project name's default changed"
    assert _where("/sdd-guestbook/preview/"), "no page names the prefix a branch reads"


# --------------------------------------------------------------------------- #
# 4. Every number the documentation quotes about an environment
# --------------------------------------------------------------------------- #

#: `(environment, terraform variable, the value the documentation states)`. These are the
#: numbers an operator acts on -- how long a backup is kept, how much capacity there is,
#: how many connections the ceiling allows -- and a stale one reads exactly like a
#: current one.
_ENVIRONMENT_NUMBERS: Final[tuple[tuple[str, str, str], ...]] = (
    ("stage", "database_backup_retention_days", "7"),
    ("prod", "database_backup_retention_days", "14"),
    ("stage", "log_retention_days", "14"),
    ("prod", "log_retention_days", "30"),
    ("stage", "database_min_capacity", "0"),
    ("prod", "database_min_capacity", "0.5"),
    ("stage", "database_max_capacity", "4"),
    ("prod", "database_max_capacity", "8"),
    ("stage", "api_reserved_concurrency", "20"),
    ("prod", "api_reserved_concurrency", "40"),
)


@pytest.mark.parametrize(("environment", "variable", "documented"), _ENVIRONMENT_NUMBERS)
def test_every_environment_number_the_documentation_states_is_the_declared_one(
    environment: str, variable: str, documented: str
) -> None:
    """The registry is that environment's own `main.tf`."""
    declaration = (REPO_ROOT / "infra" / "terraform" / "envs" / environment / "main.tf").read_text(
        encoding="utf-8"
    )
    match = re.search(rf"^\s*{re.escape(variable)}\s*=\s*([0-9.]+)", declaration, re.MULTILINE)
    assert match, f"{variable} is no longer set in envs/{environment}/main.tf"
    assert match.group(1) == documented, (
        f"envs/{environment}/main.tf sets {variable} = {match.group(1)}, and the "
        f"documentation says {documented}. docs/configuration.md holds this table"
    )


# --------------------------------------------------------------------------- #
# 5. Every GitHub variable and secret the documentation names
# --------------------------------------------------------------------------- #

_WORKFLOW_VARIABLE: Final = re.compile(r"\bvars\.([A-Z][A-Z0-9_]*)")
_WORKFLOW_SECRET: Final = re.compile(r"\bsecrets\.([A-Z][A-Z0-9_]*)")


def _workflow_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    )


def test_the_workflow_scanner_sees_the_one_variable_that_exists() -> None:
    """Proved on a live positive: `AWS_DEPLOY_ROLE_ARN` is read by three workflows."""
    assert "AWS_DEPLOY_ROLE_ARN" in _WORKFLOW_VARIABLE.findall(_workflow_text())


def test_the_documentation_names_exactly_the_repository_variables_that_exist() -> None:
    """Both directions. A documented variable nobody reads is a setting somebody will
    create and wonder about; an unread one nobody documented is a setup step missing
    from the procedure."""
    declared = set(_WORKFLOW_VARIABLE.findall(_workflow_text()))
    text = _text()
    undocumented = sorted(name for name in declared if f"`{name}`" not in text)
    assert not undocumented, f"workflows read these and docs/ names none of them: {undocumented}"


def test_the_documentation_does_not_promise_secrets_that_do_not_exist() -> None:
    """`docs/aws-account-setup.md` tells the reader to create no Actions secrets at all.

    That instruction is only safe while it is true, and it is the kind of claim a later
    workflow breaks without anybody rereading the setup page.
    """
    declared = sorted(set(_WORKFLOW_SECRET.findall(_workflow_text())) - {"GITHUB_TOKEN"})
    assert not declared, (
        "a workflow now reads a secret, and docs/aws-account-setup.md says to create "
        f"none: {declared}"
    )


# --------------------------------------------------------------------------- #
# 6. Nothing that should not be written down
# --------------------------------------------------------------------------- #

#: A handover pack is the likeliest place in a repository for a credential to be pasted
#: "just as an example". Article XI of the constitution, applied to the tree it is most
#: often forgotten in. `test_infra_layout.py` makes the same check over `infra/`.
_FORBIDDEN: Final[tuple[tuple[str, str], ...]] = (
    (r"\b\d{12}\b(?!\D*(?:byte|line|char))", "what looks like an AWS account id"),
    (r"\bAKIA[0-9A-Z]{16}\b", "an AWS access key id"),
    (r"\bASIA[0-9A-Z]{16}\b", "a temporary AWS access key id"),
    (r"arn:aws:[a-z0-9-]+:[a-z0-9-]*:\d{12}:", "an ARN carrying a real account id"),
    (r"(?i)\bpassword\s*[:=]\s*[\"'][^\"'\s]{8,}", "a password with a value beside it"),
)

#: The one twelve-digit-shaped literal a page is allowed to carry: the placeholder in the
#: example ARN that shows the shape of `plan_role_principals`. Listed rather than
#: pattern-matched, so a second one has to be added here deliberately.
_ALLOWED_LITERALS: Final[frozenset[str]] = frozenset({"123456789012"})


def test_the_credential_scanner_still_detects() -> None:
    """Proved on a known positive, because a regex that stopped matching passes every
    document silently -- and this is the rule where that failure costs the most."""
    sample = "role_arn = arn:aws:iam::999988887777:role/deploy"
    assert any(re.search(pattern, sample) for pattern, _ in _FORBIDDEN)


def test_no_credential_or_account_id_is_written_into_the_documentation() -> None:
    """Article XI, over the tree most likely to be handed to somebody else."""
    problems: list[str] = []
    for path in _documents():
        relative = str(path.relative_to(REPO_ROOT))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(literal in line for literal in _ALLOWED_LITERALS):
                continue
            for pattern, description in _FORBIDDEN:
                if re.search(pattern, line):
                    problems.append(f"{relative}:{number} carries {description}")
    assert not problems, problems


# --------------------------------------------------------------------------- #
# The set itself: indexed, and shaped
# --------------------------------------------------------------------------- #


def test_every_document_is_reachable_from_an_index() -> None:
    """A page nobody links to is a page nobody reads, and it goes stale first."""
    indexes = {
        _DOCS / "README.md": _DOCS,
        _DOCS / "runbooks" / "README.md": _DOCS / "runbooks",
    }
    listed = "\n".join(path.read_text(encoding="utf-8") for path in indexes)
    orphans = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in _documents()
        if path not in indexes and path.name not in listed
    )
    assert not orphans, f"documents no index names: {orphans}"


def test_every_document_declares_its_reader_and_what_it_defers_to() -> None:
    """`**For:**` and `**Normative source:**`, which is how "nothing here binds" stops
    being an assertion and becomes a property of every file."""
    incomplete = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in _documents()
        if "**For:**" not in path.read_text(encoding="utf-8")
        or "**Normative source:**" not in path.read_text(encoding="utf-8")
    )
    assert not incomplete, f"documents that declare no reader or no source: {incomplete}"


def test_every_runbook_has_a_runbook_s_shape() -> None:
    """When to use it, and how you know it worked.

    The second is the one that gets left out, and it is the one that matters at three in
    the morning: without it the person who did not write the procedure cannot tell
    finished from half-finished.
    """
    missing: list[str] = []
    for path in sorted((_DOCS / "runbooks").glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        relative = str(path.relative_to(REPO_ROOT))
        if "## When to use this" not in text:
            missing.append(f"{relative}: no '## When to use this'")
        if "## How you know it worked" not in text:
            missing.append(f"{relative}: no '## How you know it worked'")
    assert not missing, missing


def test_the_runbook_directory_is_not_empty() -> None:
    """The shape check above is vacuous over an empty directory."""
    runbooks = [p for p in (_DOCS / "runbooks").glob("*.md") if p.name != "README.md"]
    assert len(runbooks) >= 5, f"only {len(runbooks)} runbooks"


def test_the_documentation_declares_itself_non_normative() -> None:
    """The rule this whole tree stands on, asserted where it is written down."""
    index = (_DOCS / "README.md").read_text(encoding="utf-8")
    assert "never normative" in index
    conventions = (REPO_ROOT / "spec" / "design" / "conventions.md").read_text(encoding="utf-8")
    assert "## Documentation — where a document goes" in conventions


def test_the_reference_agrees_with_what_the_openapi_dump_would_say() -> None:
    """A guard on the guard: `docs/` must not be the only place an endpoint is written.

    The contract is `contracts/openapi/`, hand-written and versioned, and a document
    that names an endpoint the contract does not carry has invented a surface.
    """
    contracts = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((REPO_ROOT / "contracts" / "openapi").glob("*.yaml"))
    )
    named = set(re.findall(r"/api/([a-z-]+)", _text()))
    invented = sorted(path for path in named if f"/{path}" not in contracts)
    assert not invented, f"docs/ names endpoints no contract carries: {invented}"


def test_the_health_shape_the_documentation_prints_is_the_shape_it_returns() -> None:
    """`operations.md` prints a health response. Its three keys are a contract."""
    printed = (_DOCS / "operations.md").read_text(encoding="utf-8")
    match = re.search(r"\{ \"status\".*?\}", printed, re.DOTALL)
    assert match, "operations.md no longer shows a health response"
    keys = set(json.loads(match.group(0)))
    declared = (REPO_ROOT / "app" / "platform" / "schemas" / "health.py").read_text(
        encoding="utf-8"
    )
    fields = set(re.findall(r"^    ([a-z_]+): str$", declared, re.MULTILINE))
    assert keys == fields, f"documented {sorted(keys)}, HealthRead declares {sorted(fields)}"
