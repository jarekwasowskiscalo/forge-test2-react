"""The branch name is a preview's whole identity chain, so the reduction must hold.

    branch name -> slug -> Terraform state key
                        -> AWS resource names
                        -> PostgreSQL database name

Every step after the first is derived, which is what lets a teardown work from a
`delete` webhook alone: the branch is gone, its name is not, and the name is
enough to find the state. It also means a slug that is wrong is wrong in four
places at once.

Two of the failures below are silent rather than loud, which is why they are
tested rather than trusted:

- **Two branches reducing to one slug share a state key.** That does not conflict,
  error or warn. The second apply reads the first one's state, concludes its
  resources already exist under other names, and takes the stack over.
- **A slug that is one character too long** produces a Lambda function name over
  64 characters, which fails several resources into an apply.

`scripts/preview.sh slug` needs no toolchain -- no uv, no Python, no AWS -- so
this runs it as the shell script it is, on the bare interpreter the `scripts` CI
job provides.
"""

import re
import subprocess

import pytest

from app.lambda_handler import PREVIEW_DATABASE_PATTERN
from tests._repo import REPO_ROOT

_PREVIEW = REPO_ROOT / "scripts" / "preview.sh"

#: The same condition `infra/terraform/preview/branch/variables.tf` validates.
#: Copied rather than imported, because Terraform cannot export it -- and the copy
#: is the point: if the two ever disagree, this test is where it shows.
_TERRAFORM_RULE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,25}[a-z0-9])?$")

#: `sdd-guestbook` + `-preview-` + slug + `-migrate`, the longest name a preview
#: builds. Lambda refuses anything over 64.
_FIXED_NAME_COST = len("sdd-guestbook") + len("-preview-") + len("-migrate")


def slug_of(branch: str) -> str:
    result = subprocess.run(
        [str(_PREVIEW), "slug", branch],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return result.stdout.strip()


BRANCHES = [
    "main",
    "feat/JIRA-123_add-toast",
    "fix/a",
    "release/2026.09",
    "a-branch-name-that-goes-on-well-past-anything-reasonable-and-then-some",
    "UPPER/Case",
    "___",
    "feature/ünïcodé",
]


@pytest.mark.parametrize("branch", BRANCHES)
def test_a_slug_is_legal_everywhere_it_is_used(branch: str) -> None:
    """One string has to satisfy AWS, Terraform, S3 and PostgreSQL at once."""
    slug = slug_of(branch)

    assert _TERRAFORM_RULE.fullmatch(slug), (
        f"{branch!r} produced {slug!r}, which the branch root's own validation would refuse"
    )
    assert len(slug) + _FIXED_NAME_COST <= 64, (
        f"{branch!r} produces a Lambda function name of {len(slug) + _FIXED_NAME_COST} characters"
    )
    assert PREVIEW_DATABASE_PATTERN.fullmatch(f"preview_{slug.replace('-', '_')}"), (
        f"{branch!r} produces a database name app/lambda_handler.py would refuse to create"
    )


@pytest.mark.parametrize("branch", BRANCHES)
def test_a_slug_is_the_same_every_time(branch: str) -> None:
    """A teardown recomputes it from the branch name long after the branch is gone.

    If this were not stable, `preview-teardown.yml` would compute a state key that
    addresses nothing and report success over a stack still running.
    """
    assert slug_of(branch) == slug_of(branch)


def test_branches_that_read_alike_still_get_separate_stacks() -> None:
    """The reason the hash is appended ALWAYS, not only on truncation.

    `feat/x` and `feat-x` reduce to the same readable part, because the reduction
    turns every character that is not a letter or a digit into a hyphen. Sharing a
    slug means sharing a state key, and sharing a state key means the second
    branch adopts the first one's stack.
    """
    assert slug_of("feat/JIRA-123_add-toast") != slug_of("feat-JIRA-123_add-toast")
    assert slug_of("feat/x") != slug_of("feat-x")

    # Long branches whose first twenty characters are identical: the case where
    # truncation alone would collide.
    assert slug_of("feature/the-same-prefix-but-ending-one") != slug_of(
        "feature/the-same-prefix-but-ending-two"
    )


def test_the_database_name_is_derived_the_same_way_in_both_homes() -> None:
    """`preview.sh` computes it for the teardown; Terraform computes it for the stack.

    They have to agree exactly, and they cannot import each other. If either of
    these literals changes, a preview's stack points at one database and its
    teardown drops another -- which fails silently, because dropping a database
    that does not exist is a success.
    """
    shell = (REPO_ROOT / "scripts" / "preview.sh").read_text(encoding="utf-8")
    terraform = (REPO_ROOT / "infra" / "terraform" / "preview" / "branch" / "main.tf").read_text(
        encoding="utf-8"
    )

    expected_shell = "DATABASE=\"preview_$(printf '%s' \"$SLUG\" | tr '-' '_')\""
    expected_terraform = 'database_name = "preview_${replace(var.slug, "-", "_")}"'

    assert expected_shell in shell, f"scripts/preview.sh no longer computes {expected_shell}"
    assert expected_terraform in terraform, (
        f"preview/branch/main.tf no longer computes {expected_terraform}"
    )


def test_a_branch_of_pure_punctuation_still_gets_a_legal_name() -> None:
    """Every character reduces to a hyphen, and a slug may not start with one."""
    slug = slug_of("___")
    assert slug.startswith("branch-")
    assert _TERRAFORM_RULE.fullmatch(slug)


def test_the_slug_command_needs_no_toolchain() -> None:
    """It runs in the teardown workflow, which deliberately installs nothing.

    `preview-teardown.yml` sets up Terraform and nothing else -- no uv, no Node --
    because a teardown that could not run while the toolchain was broken would
    leave stacks up for exactly as long as that took to fix.
    """
    result = subprocess.run(
        [str(_PREVIEW), "slug", "some/branch"],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(REPO_ROOT)},
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert _TERRAFORM_RULE.fullmatch(result.stdout.strip())
