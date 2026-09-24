"""Nothing reaches AWS except through a GitHub Environment.

The deployment role carries `AdministratorAccess` (`infra/terraform/bootstrap/`
says so outright), so what keeps an account safe is **who may assume it**, not what
it may do. That is a trust policy listing `sub` claims, and the whole arrangement
rests on one fact: when a job declares an `environment:`, GitHub's `sub` is
`repo:O/R:environment:NAME` and no ref claim is presented at all.

Two consequences, and this file is both of them:

- **A job that assumes the role without declaring an environment presents a ref
  claim instead**, and a trust policy that accepted one would let any future job on
  the trunk take an administrator role without passing the gate a required reviewer
  lives on. So the policy accepts environments only, and no job may skip one.
- **The two lists have to agree.** An environment named in a workflow and missing
  from the policy is a deployment that fails at `AssumeRoleWithWebIdentity` --
  survivable. One named in the policy and reachable from no workflow is a door
  nobody is watching, which is not.

Reads both as text. No AWS, no credentials, no Terraform binary.
"""

import pathlib
import re
from typing import Any, Final

import yaml

from tests._repo import REPO_ROOT

WORKFLOWS: Final[pathlib.Path] = REPO_ROOT / ".github" / "workflows"
BOOTSTRAP: Final[pathlib.Path] = REPO_ROOT / "infra" / "terraform" / "bootstrap" / "main.tf"

#: The action that turns an OIDC token into AWS credentials. Every path to the
#: account goes through it; there is no other.
ASSUMES_A_ROLE: Final = "aws-actions/configure-aws-credentials"

#: `environment:` is often an expression rather than a literal, because one job in
#: `deploy.yml` serves stage and prod. The literals inside the expression are the
#: environment names; `none` is the deliberate non-name that expression falls to
#: when no trigger supplied one, and is refused downstream by `deploy.sh`.
_QUOTED: Final = re.compile(r"'([a-z][a-z0-9-]*)'")
_NOT_AN_ENVIRONMENT: Final = frozenset({"none"})

#: `"repo:${var.github_repository}:environment:preview",` in the trust policy.
_SUBJECT: Final = re.compile(r'"repo:\$\{var\.github_repository\}:([^"]+)"')


def _workflows() -> list[tuple[str, dict[Any, Any]]]:
    parsed = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        parsed.append((path.name, yaml.safe_load(path.read_text(encoding="utf-8"))))
    return parsed


def _jobs_that_assume_a_role() -> list[tuple[str, dict[Any, Any], str, dict[Any, Any]]]:
    found = []
    for name, document in _workflows():
        for job_id, job in (document.get("jobs") or {}).items():
            steps = job.get("steps") or []
            if any(ASSUMES_A_ROLE in str(step.get("uses", "")) for step in steps):
                found.append((name, document, job_id, job))
    return found


def _triggers(document: dict[Any, Any]) -> dict[Any, Any]:
    """The `on:` block. YAML reads a bare `on` as the boolean True, so both keys."""
    return document.get("on") or document.get(True) or {}


def _dispatch_options(document: dict[Any, Any], field: str) -> set[str]:
    """What a `workflow_dispatch` input is allowed to be. Empty when it is not a choice."""
    dispatch = _triggers(document).get("workflow_dispatch") or {}
    declared = (dispatch.get("inputs") or {}).get(field) or {}
    return set(declared.get("options") or [])


def _environment_names(document: dict[Any, Any], job: dict[Any, Any]) -> set[str]:
    """Every environment a job can land in.

    A literal name is the easy case. An expression is the interesting one, and it
    has two sources: the names written into it (`'prod'`, for the tag trigger) and
    the values the input it reads is allowed to take. Reading only the first missed
    `stage`, which reaches the expression through `workflow_dispatch`'s `options`
    and appears nowhere in it -- and a missing name here would have read as a
    trust policy that was too wide, which is the wrong thing to go looking for.
    """
    declared = job.get("environment")
    if declared is None:
        return set()
    name = declared if isinstance(declared, str) else str(declared.get("name", ""))
    if "${{" not in name:
        return {name} if name else set()

    names = set(_QUOTED.findall(name))
    for field in re.findall(r"inputs\.([A-Za-z_][A-Za-z0-9_]*)", name):
        names |= _dispatch_options(document, field)
    return names - _NOT_AN_ENVIRONMENT


def test_something_actually_assumes_the_role() -> None:
    """Guards every assertion below, all of which pass vacuously over an empty list."""
    assert _jobs_that_assume_a_role(), (
        f"no workflow uses {ASSUMES_A_ROLE}. Either deployment moved, or this file "
        "has been silently passing."
    )


def test_no_job_reaches_aws_without_declaring_an_environment() -> None:
    """The gate a required reviewer stands on, and the claim the trust policy accepts.

    A job without `environment:` presents `repo:O/R:ref:...` instead, which the
    policy refuses -- so this failing means either a job that cannot deploy, or a
    policy widened to let it, and the second is the one worth catching early.
    """
    for workflow, _, job_id, job in _jobs_that_assume_a_role():
        assert job.get("environment"), (
            f"{workflow}: job {job_id!r} assumes the deployment role without declaring "
            "an environment, so it presents a ref claim and passes through no gate"
        )


def test_the_trust_policy_accepts_environments_and_nothing_else() -> None:
    """No `ref:` claim, ever.

    Two used to be there -- `ref:refs/heads/main` and `ref:refs/tags/v*` -- and
    neither ever authorised anything, because every deploying job declares an
    environment and a ref claim is then not presented. What they could have done is
    let some later job on the trunk take an AdministratorAccess role with no
    environment, and no reviewer.
    """
    subjects = _SUBJECT.findall(BOOTSTRAP.read_text(encoding="utf-8"))
    assert subjects, "the bootstrap trust policy names no subjects at all"

    refs = [subject for subject in subjects if not subject.startswith("environment:")]
    assert not refs, (
        f"the trust policy accepts {refs}, which are not environment claims. A job "
        "that declares an environment never presents one, so these can only widen it."
    )


def test_the_policy_and_the_workflows_name_the_same_environments() -> None:
    """A door in the policy that no workflow opens is a door nobody is watching."""
    trusted = {
        subject.removeprefix("environment:")
        for subject in _SUBJECT.findall(BOOTSTRAP.read_text(encoding="utf-8"))
        if subject.startswith("environment:")
    }
    used: set[str] = set()
    for _, document, _, job in _jobs_that_assume_a_role():
        used |= _environment_names(document, job)

    assert used == trusted, (
        f"the workflows deploy to {sorted(used)} and the trust policy accepts "
        f"{sorted(trusted)}. Whichever list is longer is the one to look at."
    )


#: Triggers that fire without anybody asking. A job on one of these runs on every
#: merge, every closed pull request or every deleted branch -- so on a repository
#: where the deployment role has not been bootstrapped yet, it runs and fails, and
#: the failure is attached to work that had nothing to do with deployment.
#:
#: `workflow_dispatch` and `workflow_call` are deliberately absent. Those are asks,
#: and an ask deserves a loud failure: somebody pressed the button, so somebody is
#: reading the result. `deploy.yml` states the same split at its trigger block.
_AUTOMATIC: Final[frozenset[str]] = frozenset({"push", "pull_request", "delete", "schedule"})

#: The repository variable that says a role exists to assume. Empty until
#: `infra/terraform/bootstrap/` has been applied and its output named to GitHub
#: (`infra/README.md` § The first run).
_ROLE_VARIABLE: Final = "AWS_DEPLOY_ROLE_ARN"


def _trigger_names(document: dict[Any, Any]) -> set[str]:
    """The events a workflow fires on.

    Every workflow here writes `on:` in mapping form, because each trigger carries
    options -- `types:`, `branches:`, `cron:`. `_triggers` types it as a mapping for
    that reason, so the keys are the event names.
    """
    return {str(event) for event in _triggers(document)}


def test_a_job_on_an_automatic_trigger_checks_the_role_before_assuming_it() -> None:
    """A red check nobody asked for is a red check everybody learns to ignore.

    `deploy.yml` carries this guard and says why: until the bootstrap has been
    applied and the role named to GitHub, a deployment cannot succeed, and a
    trigger added before then "would paint `main` red on every merge". The
    argument is about the trigger, not about `deploy.yml` -- so it holds for
    every job that reaches for credentials without being asked to.

    `preview-teardown.yml` is what this was written for. It fires on `delete` and
    on `pull_request: closed`, it had three guards -- event type, not-a-tag,
    not-a-fork -- and none of them asked whether there was a role to assume, so
    every merged dependabot pull request left a red "Preview teardown" behind it.

    The check reads the job's `if:` as text. It is the condition GitHub evaluates
    BEFORE the environment resolves, which is also why the variable this names is
    the repository-level one rather than the `preview` environment's override.
    """
    for workflow, document, job_id, job in _jobs_that_assume_a_role():
        automatic = _trigger_names(document) & _AUTOMATIC
        if not automatic:
            continue
        assert _ROLE_VARIABLE in str(job.get("if", "")), (
            f"{workflow}: job {job_id!r} fires on {sorted(automatic)} -- which nobody "
            f"asked for -- and assumes the deployment role without checking that "
            f"{_ROLE_VARIABLE} is set. On a repository whose bootstrap has not been "
            "applied, that is a red run on every one of those events. Add "
            f"`vars.{_ROLE_VARIABLE} != ''` to the job's `if:`, as deploy.yml does."
        )


#: A `./scripts/*.sh` call whose exit status then passes through a pipe on the same
#: line -- `cmd | tee`, or `$(cmd | tail -1)`. `||` is not a pipe and must not match,
#: which is what the two exclusions are for.
_PIPED_SCRIPT: Final = re.compile(r"\./scripts/[A-Za-z0-9_.-]+\.sh(?:[^\n|]|\|\|)*\|(?!\|)")

#: Shells that give a pipeline the status of its first failing command. GitHub spells
#: `bash` as `bash --noprofile --norc -eo pipefail {0}`; the DEFAULT, used when no
#: `shell:` is named at all, is `bash -e {0}` -- `-e` and no `pipefail`.
_PIPEFAIL_SHELLS: Final[frozenset[str]] = frozenset({"bash", "pwsh", "python"})


def _effective_shell(document: dict[Any, Any], job: dict[Any, Any], step: dict[Any, Any]) -> str:
    """What GitHub will run this step's `run:` with, nearest declaration winning.

    A step names its own `shell:`; otherwise the job's `defaults.run.shell`, then the
    workflow's. Naming none of them is the case this whole test exists for: the
    fallback is `bash -e {0}`, which has no `pipefail`.
    """
    if step.get("shell"):
        return str(step["shell"])
    for scope in (job, document):
        named = ((scope.get("defaults") or {}).get("run") or {}).get("shell")
        if named:
            return str(named)
    return ""


def _joined(body: str) -> str:
    """A `run:` body with its backslash line-continuations collapsed.

    Without this the pattern below misses `./scripts/deploy.sh x \\` + newline +
    `| tee log`, which is the same defect spread over two lines -- and the more
    likely spelling once a command grows arguments.
    """
    return re.sub(r"\\\n\s*", " ", body)


def test_no_deployment_discards_a_script_exit_code_into_a_pipe() -> None:
    """A failed deployment must not report success.

    GitHub's default `run:` shell is `bash -e {0}`: `-e`, and **no `pipefail`**. So
    `./scripts/deploy.sh ... | tee deploy.log` exits with `tee`'s status, which is
    always 0 -- the script could fail and the step stayed green. What usually
    reddened the job instead was the following line failing to find a `url` in
    output that was never produced; that is luck, not a gate, and the `--rollback`
    path has no such second line.

    The same shape was in `preview.yml` (`preview.sh up | tee`) and twice in
    `release.yml`, where `version=$(./scripts/release.sh "$BUMP" | tail -1)` takes
    `tail`'s status and hands an empty version to a green step -- ironic, since
    `release.sh` keeps its stdout clean specifically so that read works.

    Read as text over every workflow, not just the deploying ones: the defect is a
    property of piping a script whose exit code somebody is relying on, and the next
    one will be written in whichever file needs it.
    """
    offenders: list[str] = []
    for name, document in _workflows():
        for job_id, job in (document.get("jobs") or {}).items():
            for index, step in enumerate(job.get("steps") or []):
                body = _joined(str(step.get("run", "")))
                if not _PIPED_SCRIPT.search(body):
                    continue
                if "pipefail" in body:
                    continue
                shell = _effective_shell(document, job, step)
                if shell not in _PIPEFAIL_SHELLS:
                    named = step.get("name", f"step {index}")
                    offenders.append(
                        f"{name}: {job_id}/{named!r} under {shell or 'the default shell'}"
                    )

    assert offenders == [], (
        "a script's exit code is piped away under a shell without pipefail, so a "
        f"failure of that script reports a green step: {offenders}. Add `shell: bash` "
        "to the step -- that selects `bash --noprofile --norc -eo pipefail {0}` -- or "
        "`set -o pipefail` at the top of the body."
    )
