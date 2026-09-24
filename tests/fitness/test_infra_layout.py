"""The Terraform roots stay the shapes they are meant to be.

There are four kinds of root here and they are guarded differently, which is the
whole structure of this file:

- **environments** -- `infra/terraform/envs/{stage,prod}/`, long-lived, one state
  each, directories rather than Terraform workspaces
  (`spec/design/architecture.md` § Environments). The cost of that choice is that
  two directories can drift, and the one that drifts is always the one nobody
  deploys often enough to notice: a `stage` that silently stopped matching `prod`
  is a rehearsal that proves nothing.
- **singletons** -- `bootstrap/` and `preview/shared/`, applied once per account.
- **the template** -- `preview/branch/`, applied once per branch, whose state key
  is supplied at `init` rather than written down. That absence is load-bearing and
  is asserted directly.
- **the refusals** -- `refusals/*/`, which exist to FAIL. Each one sets a module
  parameter this stack declares unsupported, and `scripts/infra-check.sh` requires
  `terraform validate` to reject it by name. They are the one kind that is neither
  in `ROOTS` nor reachable from `infra.sh`, and both of those absences are asserted
  rather than left to be noticed -- the alternative is a barrier nothing exercises,
  which is a barrier the next person deletes.

The environment set is **discovered**, not listed. It was listed, and the list
said `dev` for as long as it took somebody to notice; a name in two places is a
name that disagrees with itself eventually.

Reads the files as text. No Terraform binary, no credentials, no network -- so
this runs in the `--no-db` subset, on every platform leg, and inside
`check.sh --fast`.
"""

import pathlib
import re
from typing import Final

import pytest

from tests._repo import REPO_ROOT

INFRA: Final[pathlib.Path] = REPO_ROOT / "infra" / "terraform"


def _directories(parent: pathlib.Path) -> tuple[str, ...]:
    """Real subdirectories, sorted. `.terraform/` caches are not roots."""
    if not parent.is_dir():
        return ()
    return tuple(sorted(p.name for p in parent.iterdir() if p.is_dir() and p.name[0] != "."))


#: The long-lived environments, whatever they are today.
ENVIRONMENTS: Final[tuple[str, ...]] = _directories(INFRA / "envs")

#: `preview/shared` (applied once) and `preview/branch` (applied once per branch).
PREVIEW_ROOTS: Final[tuple[str, ...]] = tuple(
    f"preview/{name}" for name in _directories(INFRA / "preview")
)

#: Every directory Terraform is ever pointed at and expected to ACCEPT. `modules/`
#: are not roots: they are called, never initialised on their own, and have no
#: backend of their own.
ROOTS: Final[tuple[str, ...]] = (
    "bootstrap",
    *PREVIEW_ROOTS,
    *(f"envs/{name}" for name in ENVIRONMENTS),
)

#: The roots that exist to be rejected. Discovered like the environments, and for
#: the same reason: a list would be the thing that goes stale.
REFUSAL_ROOTS: Final[tuple[str, ...]] = tuple(
    f"refusals/{name}" for name in _directories(INFRA / "refusals")
)

#: The root that is applied many times, and therefore the one that must NOT carry
#: a state key. Named rather than derived, because what makes it special is a
#: decision rather than its position in the tree.
TEMPLATE_ROOT: Final = "preview/branch"

#: `key = "..."` inside a backend block.
_BACKEND_KEY: Final = re.compile(r'^\s*key\s*=\s*"([^"]+)"', re.MULTILINE)

#: `source = "../../modules/stack"` and friends.
_MODULE_SOURCE: Final = re.compile(r'source\s*=\s*"([^"]+)"')

#: Any dotted-quad with a prefix length, wherever in a root it is written.
_CIDR: Final = re.compile(r'"(\d{1,3}(?:\.\d{1,3}){3}/\d{1,2})"')

#: One `"<root>|<phrase>"` element of infra-check.sh's REFUSALS array. Quoted
#: because the phrase carries spaces, which is also why the script cannot use a
#: bare word list there.
_REFUSAL_ENTRY: Final = re.compile(r'"([^"]+)"')


def _read(relative: str) -> str:
    return (INFRA / relative).read_text(encoding="utf-8")


def _root_text(root: str) -> str:
    """Every `.tf` file in one root, concatenated. Which file said it rarely matters."""
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((INFRA / root).glob("*.tf"))
    )


# --------------------------------------------------------------------------- #
# Every root
# --------------------------------------------------------------------------- #


#: `preview-branch) ROOT="infra/terraform/preview/branch" ;;` in infra.sh's own case.
_INFRA_CASE: Final = re.compile(r'^\s*([a-z|-]+)\)\s*ROOT="infra/terraform/([^"]+)"', re.MULTILINE)


def test_the_gate_checks_every_root_that_exists() -> None:
    """`infra-check.sh` carries the same list, and until now nothing compared them.

    A root absent from that list is never `fmt`-checked and never `validate`d --
    it simply is not in the gate, which is the one failure a file about
    infrastructure layout exists to prevent. This is the assertion that closes it.
    """
    script = (REPO_ROOT / "scripts" / "infra-check.sh").read_text(encoding="utf-8")
    declared = re.search(r"^ROOTS=\(([^)]*)\)", script, re.MULTILINE)
    assert declared is not None, "scripts/infra-check.sh no longer declares ROOTS=(...)"

    assert tuple(sorted(declared.group(1).split())) == tuple(sorted(ROOTS)), (
        f"infra-check.sh checks {sorted(declared.group(1).split())}, "
        f"but the tree holds {sorted(ROOTS)}"
    )


def test_the_interface_can_reach_every_root_that_exists() -> None:
    """The other half, and the one that hurts sooner.

    A root the gate checks but `infra.sh` cannot address is a root nobody can plan
    or apply -- correct Terraform that no supported command reaches, discovered by
    whoever needed it in a hurry. Article XII says the script is the interface, so
    a root outside the interface is not really there.
    """
    script = (REPO_ROOT / "scripts" / "infra.sh").read_text(encoding="utf-8")
    reachable = {
        path.replace("$ENVIRONMENT", label)
        for labels, path in _INFRA_CASE.findall(script)
        for label in labels.split("|")
    }
    assert reachable, "scripts/infra.sh no longer maps an environment name to a root"

    assert reachable == set(ROOTS), (
        f"infra.sh reaches {sorted(reachable)}, but the tree holds {sorted(ROOTS)}"
    )


def test_every_root_pins_the_provider_and_the_language() -> None:
    """An unpinned provider is one plan per machine. An unpinned Terraform is
    worse than that: state written by a newer one cannot be read by an older,
    so the first person to run an upgraded binary locks everybody else out."""
    for root in ROOTS:
        text = _root_text(root)
        assert "required_version" in text, f"{root} pins no Terraform version"
        assert re.search(r'version\s*=\s*"~>', text), f"{root} pins no provider version"


def test_the_pinned_terraform_is_the_one_the_scripts_use() -> None:
    """One version, named in one place. `scripts/_lib.sh` is that place, and CI
    plus `infra.sh` both read it rather than carrying a second copy."""
    lib = (REPO_ROOT / "scripts" / "_lib.sh").read_text(encoding="utf-8")
    pinned = re.search(r'TERRAFORM_VERSION="([^"]+)"', lib)
    assert pinned is not None, "scripts/_lib.sh pins no Terraform version"

    major_minor = ".".join(pinned.group(1).split(".")[:2])
    for root in ROOTS:
        required = re.search(r'required_version\s*=\s*">=\s*([0-9.]+)"', _root_text(root))
        assert required is not None, f"{root} does not state a minimum Terraform version"
        assert tuple(int(part) for part in required.group(1).split(".")) <= tuple(
            int(part) for part in major_minor.split(".")
        ), f"{root} requires more than the pinned {pinned.group(1)}"


def test_every_workflow_pins_the_same_terraform_as_the_scripts() -> None:
    """The literal copies in `.github/workflows/` say what `scripts/_lib.sh` says.

    An Actions step cannot source a shell file, so each workflow that sets up
    Terraform carries the version as a literal. `ci.yml` has said in a comment since
    it was written that this test compares those copies -- and it did not: the test
    above reads `_lib.sh` and the Terraform roots, and never opens a workflow. The
    comment was a promise of a check that did not exist, which is worse than no
    comment, because the next person to change one copy reads it and stops looking.

    Discovered rather than listed, the lesson `tests/tooling/test_uv_pin.py` records
    for `UV_VERSION`: a workflow added tomorrow is covered without anybody
    remembering this file. Discovery can silently find nothing, so the count is
    asserted too.
    """
    lib = (REPO_ROOT / "scripts" / "_lib.sh").read_text(encoding="utf-8")
    pinned = re.search(r'TERRAFORM_VERSION="([^"]+)"', lib)
    assert pinned is not None, "scripts/_lib.sh pins no Terraform version"

    workflows = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflows, "no workflows found; this test would then pass over nothing"

    found: dict[str, str] = {}
    for path in workflows:
        text = path.read_text(encoding="utf-8")
        match = re.search(r'^\s*TERRAFORM_VERSION:\s*"([^"]+)"', text, flags=re.MULTILINE)
        if match is None:
            assert "terraform_version:" not in text, (
                f"{path.name} configures Terraform and declares no TERRAFORM_VERSION, "
                "so it installs whatever is latest that morning"
            )
            continue
        found[path.name] = match.group(1)

    assert found, (
        "no workflow was found to pin Terraform, which cannot be true while the "
        "infrastructure jobs run"
    )
    disagreeing = {name: value for name, value in found.items() if value != pinned.group(1)}
    assert not disagreeing, (
        f"scripts/_lib.sh pins Terraform {pinned.group(1)} and these copies disagree: "
        f"{disagreeing}. A workstation and CI would then plan with two different binaries."
    )


def test_no_account_id_or_secret_is_written_down_here() -> None:
    """Terraform files are read by everybody who can read the repository.

    A twelve-digit account id is not a secret and is still an unnecessary thing
    to publish; an access key is neither. Both are looked for, because the
    second one arrives by paste and the first by copying a working example.
    """
    offenders = []
    for path in INFRA.rglob("*.tf"):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            # `data.aws_caller_identity` is how an account id is meant to appear:
            # resolved at plan time, never typed.
            if re.search(r"\b\d{12}\b", line) and "aws_caller_identity" not in line:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {line.strip()[:60]}")
            if re.search(r"\bAKIA[0-9A-Z]{16}\b", line):
                offenders.append(f"{path.relative_to(REPO_ROOT)}: an access key id")
    assert not offenders, offenders


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #


def test_no_two_roots_share_a_literal_state_key() -> None:
    """The single worst thing that can go wrong in this directory.

    Two roots pointed at one key do not conflict, error or warn: the second apply
    reads the first one's state, concludes that everything it is about to create
    already exists under different names, and rewrites the other one into this
    one's shape. Production, adopted by a preview.
    """
    keys: dict[str, str] = {}
    for root in ROOTS:
        if root == "bootstrap":
            continue  # local state by design: the bucket cannot hold its own
        match = _BACKEND_KEY.search(_read(f"{root}/backend.tf"))
        if root == TEMPLATE_ROOT:
            continue  # asserted the other way round, below
        assert match is not None, f"{root}/backend.tf has no state key at all"
        assert match.group(1) not in keys.values(), (
            f"{root} shares a state key with {[k for k, v in keys.items() if v == match.group(1)]}"
        )
        keys[root] = match.group(1)

    for root, key in keys.items():
        leaf = root.rsplit("/", 1)[-1]
        assert leaf in key, (
            f"{root}'s state key is {key!r}, which does not name {leaf}. "
            "A key that does not carry its root is a key nobody can check."
        )


def test_the_template_root_declares_no_state_key() -> None:
    """The most valuable line in this file, and the least obvious.

    `preview/branch/` is applied once per branch, and its key is supplied at
    `init` with `-backend-config`. A literal key there would not fail: every
    preview would quietly share one state file, so the second branch to deploy
    would destroy the first one's stack and adopt its name. The absence IS the
    design, so the absence is what is asserted.
    """
    if TEMPLATE_ROOT not in ROOTS:
        pytest.skip(f"{TEMPLATE_ROOT} does not exist yet")

    backend = _read(f"{TEMPLATE_ROOT}/backend.tf")
    assert 'backend "s3"' in backend, f"{TEMPLATE_ROOT} declares no remote backend at all"
    assert _BACKEND_KEY.search(backend) is None, (
        f"{TEMPLATE_ROOT}/backend.tf names a state key. Every preview would share it, "
        "and the second branch to deploy would take over the first one's stack."
    )


def test_the_preview_role_is_denied_every_environment_state_key_that_exists() -> None:
    """The one security property in this tree that fails OPEN.

    The preview role carries `AdministratorAccess` and is narrowed by a `Deny` on
    the long-lived environments' state -- which is where the Aurora master password
    sits, in cleartext. The Deny names those state keys as literals, so an
    environment added, renamed or re-keyed leaves the Deny pointing at nothing:
    every preview would then be able to read production's state, and nothing would
    say so. A permissions bug that shows up as everything continuing to work is
    exactly the kind worth a test.
    """
    bootstrap = _read("bootstrap/main.tf")
    #: From the sid to the end of that statement's `resources` list -- the actions
    #: list comes first and closes a bracket of its own, so a lazy match to the
    #: first `]` reads the wrong half and passes over an empty resource set.
    denied = re.search(
        r'sid\s*=\s*"NotTheEnvironmentsState".*?resources\s*=\s*\[(.*?)\]',
        bootstrap,
        re.DOTALL,
    )
    assert denied is not None, "the preview role no longer denies the environments' state"

    for name in ENVIRONMENTS:
        key = _BACKEND_KEY.search(_read(f"envs/{name}/backend.tf"))
        assert key is not None
        #: With the trailing separator, because without it `sdd-guestbook/prod` is a
        #: substring of `sdd-guestbook/production/*` -- so a Deny that had drifted to
        #: the wrong prefix still read as covering the right one. Found by mutating
        #: this very file; the first version of the assertion could not fail.
        prefix = key.group(1).rsplit("/", 1)[0] + "/"
        assert prefix in denied.group(1), (
            f"a preview may read {name}'s state under {prefix!r}, which holds its master password"
        )


def test_the_preview_scripts_and_the_shared_layer_agree_on_where_to_look() -> None:
    """The parameter prefix has two homes and they cannot import each other.

    `preview/shared/main.tf` publishes under `/${project}/preview/`, and
    `scripts/preview.sh` reads a literal. They disagree loudly rather than quietly
    -- the teardown fails with `ParameterNotFound` -- but it fails at the moment
    somebody is trying to remove a stack, which is the worst time to discover a
    typo in a path.
    """
    project = re.search(
        r'variable "project"[^}]*?default\s*=\s*"([^"]+)"',
        _read("preview/shared/variables.tf"),
        re.DOTALL,
    )
    assert project is not None, "preview/shared no longer defaults a project name"

    script = (REPO_ROOT / "scripts" / "preview.sh").read_text(encoding="utf-8")
    assert f"/{project.group(1)}/preview/" in script, (
        f"scripts/preview.sh does not read parameters under /{project.group(1)}/preview/"
    )


# --------------------------------------------------------------------------- #
# The long-lived environments
# --------------------------------------------------------------------------- #


def test_every_environment_exists_and_has_the_same_files() -> None:
    """A missing `backend.tf` is the failure that hurts: Terraform falls back to
    LOCAL state, the apply succeeds, and the record of what exists is now on one
    laptop instead of in S3 -- discovered by the second person to deploy."""
    assert ENVIRONMENTS, "infra/terraform/envs/ holds no environment at all"
    expected = {"backend.tf", "main.tf", "outputs.tf", "variables.tf", "versions.tf"}
    for name in ENVIRONMENTS:
        present = {path.name for path in (INFRA / "envs" / name).glob("*.tf")}
        assert present == expected, f"{name} has {sorted(present)}, expected {sorted(expected)}"


def test_every_environment_is_built_from_the_same_module() -> None:
    """The whole reason `modules/stack` exists.

    An environment that stopped calling it and inlined the modules instead would
    look correct in review and would be the copy that drifts. With `dev` retired
    there are two of these left, which makes the pair matter more rather than
    less: `stage` exists to rehearse `prod`.
    """
    for name in ENVIRONMENTS:
        sources = _MODULE_SOURCE.findall(_read(f"envs/{name}/main.tf"))
        assert sources == ["../../modules/stack"], (
            f"{name} builds itself from {sources} rather than from the shared stack module"
        )


def test_the_environment_declares_itself_and_nothing_else_does() -> None:
    """`environment = "stage"` in stage's own directory and nowhere else.

    A copy-pasted directory that kept the previous name is a whole environment
    deployed under another one's resource names -- and Terraform is perfectly
    happy to do it.
    """
    for name in ENVIRONMENTS:
        text = _read(f"envs/{name}/main.tf")
        assert re.search(rf'environment\s*=\s*"{name}"', text), (
            f"{name}/main.tf does not declare environment = {name!r}"
        )
        for other in ENVIRONMENTS:
            if other != name:
                assert f'"{other}"' not in text, f"{name}/main.tf mentions {other}"


def test_nothing_long_lived_is_disposable() -> None:
    """`disposable` lets a destroy empty the web bucket and skip the final snapshot.

    It used to be true for `dev` and this test named `dev` to say so -- by matching
    a literal with three spaces of alignment in it, which any reformat would have
    broken. `dev` is gone and the throwaway environment is now a preview, which
    calls no stack module at all. So what is left to assert is the half that
    matters: nothing that holds real data may carry the switch.
    """
    for name in ENVIRONMENTS:
        match = re.search(r"disposable\s*=\s*(true|false)", _read(f"envs/{name}/main.tf"))
        assert match is not None, f"{name} does not say whether it is disposable"
        assert match.group(1) == "false", (
            f"{name} is marked disposable, which lets a destroy take it without a snapshot"
        )


def test_production_alone_pays_to_avoid_the_resume() -> None:
    """A capacity floor is the difference between "cheap" and "the first visitor
    of the day waits fifteen seconds". Everything else takes the wait; production
    does not, and nothing else should be quietly paying for a floor either."""
    floors = {}
    for name in ENVIRONMENTS:
        match = re.search(r"database_min_capacity\s*=\s*([0-9.]+)", _read(f"envs/{name}/main.tf"))
        assert match is not None, f"{name} does not state a capacity floor"
        floors[name] = float(match.group(1))

    assert floors.get("prod", 0) > 0, "production has no capacity floor"
    for name, floor in floors.items():
        if name != "prod":
            assert floor == 0, f"{name} pays for a floor it does not need"


# --------------------------------------------------------------------------- #
# Networks
# --------------------------------------------------------------------------- #


def test_no_two_stacks_share_a_network() -> None:
    """Overlapping CIDRs are fine until the day somebody peers two of these,
    and then they are unfixable without renumbering a live VPC."""
    owner: dict[str, str] = {}
    for root in (*(f"envs/{name}" for name in ENVIRONMENTS), "preview/shared"):
        found = set(_CIDR.findall(_root_text(root)))
        assert found, f"{root} declares no network"
        for cidr in found:
            assert cidr not in owner, f"{root} shares {cidr} with {owner[cidr]}"
            owner[cidr] = root


# --------------------------------------------------------------------------- #
# The shared preview layer
# --------------------------------------------------------------------------- #


def test_the_preview_cluster_can_be_rebuilt_the_same_week() -> None:
    """A destroyed secret keeps its name for its recovery window, and the name
    carries the layer. At the default of seven days, tearing this layer down and
    putting it back fails on `a secret with this name is already scheduled for
    deletion` -- an error about Secrets Manager, for a cause in Terraform.

    It is asserted here rather than anywhere else because this is the root most
    likely to be rebuilt, and because the knob was unreachable from any root at
    all until `modules/stack` learned to pass it through."""
    shared = _root_text("preview/shared")
    assert re.search(r"secret_recovery_days\s*=\s*0", shared), (
        "the shared preview layer keeps its master secret's name for days after a destroy"
    )
    assert re.search(r"skip_final_snapshot\s*=\s*true", shared), (
        "the preview cluster takes a final snapshot, whose name then collides on rebuild"
    )
    assert "secret_recovery_days" in _read("modules/stack/main.tf"), (
        "modules/stack does not pass secret_recovery_days through, so no environment can set it"
    )


def test_the_shared_layer_publishes_what_a_branch_needs_to_find_it() -> None:
    """A branch stack discovers this layer through named parameters, never through
    its state file: a `terraform_remote_state` data source reads the whole state
    object, and this one holds the cluster's master password in cleartext.

    The list is short on purpose. Each of these is read by
    `infra/terraform/preview/branch/` or by `scripts/preview.sh`, and a parameter
    that stopped being published is a preview that cannot be built or cannot be
    torn down.
    """
    shared = _root_text("preview/shared")
    for parameter in (
        "private_subnet_ids",
        "lambda_security_group_id",
        "database/endpoint",
        "database/maintenance_database",
        "database/master_secret_arn",
        "database/iam_auth_resource_arn",
        "maintenance_function_name",
    ):
        assert parameter in shared, f"the shared preview layer no longer publishes {parameter}"

    #: The secret has exactly one home, which is the one `modules/database` gives
    #: it. What is published here is where to find it, never what is in it -- a
    #: branch resolves the value itself through Secrets Manager.
    assert 'resource "random_password"' not in shared, (
        "a password generated in this root would sit beside the parameters that locate it"
    )
    published = re.findall(r'name\s*=\s*"(/[^"]+)"', shared)
    assert not [name for name in published if "password" in name], (
        f"a parameter here names a password: {published}"
    )


# --------------------------------------------------------------------------- #
# The refusal roots
# --------------------------------------------------------------------------- #


def test_the_gate_refuses_every_refusal_root_that_exists() -> None:
    """The parity that keeps a barrier exercised.

    A directory under `refusals/` that `infra-check.sh` does not name is a
    parameter nobody proves is still refused: the `validation` block guarding it
    can be relaxed or deleted and every gate stays green. Discovered from the tree
    rather than listed here, so a second refusal added tomorrow is covered without
    anybody remembering this file.
    """
    script = (REPO_ROOT / "scripts" / "infra-check.sh").read_text(encoding="utf-8")
    declared = re.search(r"^REFUSALS=\(([^)]*)\)", script, re.MULTILINE)
    assert declared is not None, "scripts/infra-check.sh no longer declares REFUSALS=(...)"

    named = tuple(
        sorted(entry.split("|", 1)[0] for entry in _REFUSAL_ENTRY.findall(declared.group(1)))
    )
    assert named == tuple(sorted(REFUSAL_ROOTS)), (
        f"infra-check.sh refuses {list(named)}, but the tree holds {sorted(REFUSAL_ROOTS)}"
    )


def test_every_refusal_the_gate_greps_for_is_a_message_the_tree_can_produce() -> None:
    """The half of that step that Terraform alone would find, and only in CI.

    `infra-check.sh` requires the refusal to SAY something, not merely to happen --
    so the phrase it greps for has to be text some `error_message` under
    `infra/terraform/` actually contains. If the two drift apart the gate turns red
    in the `infra` job, which is the only job with a Terraform binary; this
    assertion reads the files instead, so it fails in the `--no-db` subset on every
    platform, seconds after the edit.
    """
    script = (REPO_ROOT / "scripts" / "infra-check.sh").read_text(encoding="utf-8")
    declared = re.search(r"^REFUSALS=\(([^)]*)\)", script, re.MULTILINE)
    assert declared is not None, "scripts/infra-check.sh no longer declares REFUSALS=(...)"

    messages = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(INFRA.rglob("variables.tf"))
    )
    for entry in _REFUSAL_ENTRY.findall(declared.group(1)):
        root, _, phrase = entry.partition("|")
        assert phrase, f"{root} is declared with no phrase, so the gate would accept any failure"
        assert phrase in messages, (
            f"the gate requires {root}'s refusal to name {phrase!r}, and no error_message "
            "under infra/terraform/ says it. The step would fail for the wrong reason."
        )


def test_no_refusal_root_is_validated_as_though_it_should_pass() -> None:
    """The negative that makes the two loops in that script mean different things.

    `ROOTS` is checked for `validate` SUCCEEDING and `REFUSALS` for it failing. A
    refusal root in both lists would be asserted to pass and to fail at once, and
    the script would stop at the first loop -- reporting the barrier as broken while
    it worked.
    """
    script = (REPO_ROOT / "scripts" / "infra-check.sh").read_text(encoding="utf-8")
    declared = re.search(r"^ROOTS=\(([^)]*)\)", script, re.MULTILINE)
    assert declared is not None, "scripts/infra-check.sh no longer declares ROOTS=(...)"

    overlap = set(declared.group(1).split()) & set(REFUSAL_ROOTS)
    assert not overlap, f"these roots are required both to validate and to be refused: {overlap}"

    assert not set(ROOTS) & set(REFUSAL_ROOTS), (
        "a refusal root was discovered as a real one too, so `refusals/` has moved "
        "under envs/ or preview/ and every environment now inherits a config meant to fail"
    )


def test_no_refusal_root_is_reachable_from_the_interface() -> None:
    """The one declared exception to `test_the_interface_can_reach_every_root_that_exists`.

    That test's doctrine is article XII's: a root no script reaches is not really
    there. These are the roots where that is the point -- there is nothing to plan
    and nothing to apply, no `backend.tf` and no state, and an `apply` could not get
    past the `validate` they are built to fail. Handing an operator
    `./scripts/infra.sh refusals-database-proxy apply` would offer a command whose
    only outcome is an error. Asserted so the absence is a rule rather than an
    oversight somebody helpfully corrects.
    """
    script = (REPO_ROOT / "scripts" / "infra.sh").read_text(encoding="utf-8")
    reachable = {
        path.replace("$ENVIRONMENT", label)
        for labels, path in _INFRA_CASE.findall(script)
        for label in labels.split("|")
    }
    offered = reachable & set(REFUSAL_ROOTS)
    assert not offered, (
        f"scripts/infra.sh offers {sorted(offered)}, which exist only to fail `validate`"
    )


def test_every_refusal_root_pins_the_provider_and_the_language() -> None:
    """The same rule as for a real root, for the same reason.

    An unpinned refusal root is one `init` per machine: the day a provider release
    changes when a variable validation is evaluated, this root starts failing -- or
    stops -- for a reason that has nothing to do with the barrier it guards.
    """
    assert REFUSAL_ROOTS, (
        "infra/terraform/refusals/ holds nothing, so the loops above pass over nothing"
    )
    for root in REFUSAL_ROOTS:
        text = _root_text(root)
        assert "required_version" in text, f"{root} pins no Terraform version"
        assert re.search(r'version\s*=\s*"~>', text), f"{root} pins no provider version"
        #: No state to share, and no state key to collide with anything. The one
        #: property of a real root this kind must NOT have.
        assert not (INFRA / root / "backend.tf").exists(), (
            f"{root} declares a backend. Nothing here is applied, so a state key here "
            "is a key that can only ever collide with a real one."
        )
