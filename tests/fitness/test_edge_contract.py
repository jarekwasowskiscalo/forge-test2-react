"""The edge serves the SPA fallback without touching a status or a body it did not produce.

CloudFront used to do the fallback with two `custom_error_response` blocks, and
that field is a member of the DISTRIBUTION -- `CacheBehavior` has no equivalent,
so there is no narrower form of it. It therefore applied in front of both
origins: every 403 and 404 became `200 text/html` carrying the application
shell, including the API's own refusals, which the application was getting
right all along (`app/main.py`, and `tests/unit/test_spa_fallback.py` proves it
there). A contract that holds in the process and stops holding at the edge holds
nowhere a browser can see.

**What this file can and cannot prove.** It reads the Terraform and the function
source as text. No binary, no credentials, no network -- so it runs in the
`no_db` subset on every platform leg. What it pins is the CONFIGURATION: that the
distribution-wide rewriting has not come back, that the fallback is attached to
one behaviour rather than to the distribution, and that the function excludes the
two prefixes it must exclude. The BEHAVIOUR -- a real 404 arriving as a 404 --
needs a live distribution and an AWS account, and nothing in this repository
reaches the edge. That evidence is the deploy to `stage` and step 6 of
`docs/runbooks/release-to-production.md`; it is named here so the gap is a
sentence rather than a silence.
"""

import pathlib
import re
from typing import Final

from tests._repo import REPO_ROOT

INFRA: Final[pathlib.Path] = REPO_ROOT / "infra" / "terraform"

WEB: Final[pathlib.Path] = INFRA / "modules" / "web"

#: The function's own source, referenced from `main.tf` by `file()`.
FALLBACK: Final[pathlib.Path] = WEB / "spa-fallback.js"


def _distribution() -> str:
    """The `aws_cloudfront_distribution` block, brace-matched from its header.

    Read by counting braces rather than by a lazy regex: every assertion below is
    about what is INSIDE this resource versus what is inside one of its
    behaviours, and a pattern that stops at the first `}` cannot tell those
    apart.

    The counter does not know a brace in a comment from a brace in the language.
    It does not have to while every one of them is written in a pair -- and an
    odd one raises below, rather than quietly widening a slice, because the depth
    never returns to zero.
    """
    text = (WEB / "main.tf").read_text(encoding="utf-8")
    start = text.index('resource "aws_cloudfront_distribution"')
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError("the distribution's braces do not balance in modules/web/main.tf")


def _attribute(name: str, value: str) -> re.Pattern[str]:
    """`name = value`, however `terraform fmt` has aligned the equals signs today.

    The alignment is a property of the LONGEST name in the block, so a literal
    with the spacing baked in fails the day somebody adds a longer neighbour --
    a red gate that reports nothing about what it guards.
    """
    return re.compile(rf"{re.escape(name)}\s*=\s*{value}")


def _block(name: str) -> str:
    """One block of the distribution, brace-matched the same way."""
    distribution = _distribution()
    start = distribution.index(f"{name} {{")
    depth = 0
    for index in range(start, len(distribution)):
        if distribution[index] == "{":
            depth += 1
        elif distribution[index] == "}":
            depth -= 1
            if depth == 0:
                return distribution[start : index + 1]
    raise AssertionError(f"the braces of `{name}` do not balance in modules/web/main.tf")


#: A DECLARATION of the field, not a mention of it. `main.tf` says in prose that
#: the absence is a decision, and a detector that could not tell that apart from
#: the thing itself would force the explanation out of the file that needs it
#: most. The brace is safe to rely on: `terraform fmt -check` is a gate
#: (`scripts/infra-check.sh`), and canonical HCL puts exactly one space there.
_ERROR_RESPONSE_BLOCK: Final = re.compile(r"^\s*custom_error_response \{", re.MULTILINE)


def test_nothing_rewrites_an_error_response_anywhere_in_the_tree() -> None:
    """The whole tree, not just this module: a second distribution would repeat the defect.

    Written as a search over every `.tf` rather than over the one file that had
    it, because the reason the field is refused is a property of the field and
    not of the module that happened to use it.
    """
    offenders = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in INFRA.rglob("*.tf")
        if _ERROR_RESPONSE_BLOCK.search(path.read_text(encoding="utf-8"))
    )
    assert not offenders, (
        f"`custom_error_response` is back in {offenders} -- it is a member of the "
        "distribution and cannot be narrowed to a behaviour, so it rewrites the API's "
        "refusals too. The SPA fallback is the viewer-request function in modules/web/"
    )


def test_the_error_response_detector_still_detects() -> None:
    """The sweep above passes on an empty tree too, so the pattern is proved first.

    Both halves: the declaration is caught, and the sentence in `main.tf` that
    explains why there is none is not.
    """
    declared = """
      custom_error_response {
        error_code         = 403
        response_code      = 200
        response_page_path = "/index.html"
      }
    """
    assert _ERROR_RESPONSE_BLOCK.search(declared), "the detector would not see the defect return"
    assert not _ERROR_RESPONSE_BLOCK.search(
        "  # No `custom_error_response` here, and that absence is a decision."
    ), "the detector cannot tell a declaration from the comment that explains its absence"


def test_the_fallback_is_attached_to_the_static_behaviour_alone() -> None:
    """A function association is a behaviour's field, and that is why the fix works."""
    assert "function_association" in _block("default_cache_behavior"), (
        "the SPA fallback is not attached to the S3 behaviour -- a deep link would "
        "reach the bucket as a key that does not exist"
    )
    api = _block("ordered_cache_behavior")
    assert _attribute("path_pattern", r'"/api/\*"').search(api), (
        "this test found an ordered behaviour that is not the API's -- point it at the "
        "right one rather than deleting it"
    )
    assert "function_association" not in api, (
        "the SPA fallback is attached to `/api/*` -- that is the distribution-wide "
        "defect again, spelled differently"
    )


def test_the_association_runs_on_the_viewer_request() -> None:
    """`viewer-request` is what makes it a rewrite rather than a redirect.

    On the viewer request the URI is changed before the cache is consulted, so
    every deep link shares `/index.html`'s cache entry and the single-path
    invalidation after a deploy covers all of them. On a viewer RESPONSE it would
    be too late to change what was fetched.
    """
    association = _block("default_cache_behavior")
    assert _attribute("event_type", '"viewer-request"').search(association), (
        "the fallback is not on the viewer request, so it cannot rewrite the URI"
    )


def test_the_function_leaves_the_api_and_the_assets_alone() -> None:
    """The two prefixes whose errors are answers.

    `/api/` is belt and braces -- the behaviour above already keeps the function
    away from it. `/assets/` is not: those requests DO reach this function, and a
    missing hashed bundle rewritten to the shell is a blank screen with nothing
    in the log.
    """
    source = FALLBACK.read_text(encoding="utf-8")
    for prefix in ("/api/", "/assets/"):
        assert f"startsWith('{prefix}')" in source, (
            f"the fallback no longer excludes `{prefix}` -- a request under it would be "
            "answered with the shell instead of with what actually happened"
        )
    assert "'/index.html'" in source, "the fallback rewrites to nothing"


def test_the_excluded_asset_prefix_is_the_one_the_deploy_publishes_to() -> None:
    """The exclusion is a path, and the path is decided somewhere else.

    `assets/` is Vite's default directory, and `scripts/deploy.sh` step 5 syncs it
    under that name with a year of immutable caching. If either moved, the
    function would stop recognising bundles and start answering a missing one
    with the shell -- which is the defect this whole change removes, returned
    through a door nobody was watching.
    """
    deploy = (REPO_ROOT / "scripts" / "deploy.sh").read_text(encoding="utf-8")
    assert '"s3://$BUCKET/assets"' in deploy, (
        "the deploy no longer publishes the bundles under `assets/`, so the prefix "
        f"{FALLBACK.name} excludes is the wrong one -- move both together"
    )


def test_the_function_source_is_the_one_terraform_publishes() -> None:
    """The file exists and `main.tf` reads it, so this suite and AWS see one text."""
    assert FALLBACK.is_file(), f"{FALLBACK.relative_to(REPO_ROOT)} is gone"
    main = (WEB / "main.tf").read_text(encoding="utf-8")
    assert f'file("${{path.module}}/{FALLBACK.name}")' in main, (
        "modules/web/main.tf no longer publishes this file -- an inlined copy is a "
        "second text that drifts from the one the tests read"
    )
    assert _attribute("runtime", '"cloudfront-js-2.0"').search(main), (
        "the runtime moved; `startsWith` is ES6 and runtime 1.0 does not have it"
    )


def test_a_missing_key_can_answer_that_it_is_missing() -> None:
    """`s3:ListBucket` is granted to change a status, not to expose a listing.

    Without it S3 answers a missing key with 403 rather than 404, and a bundle
    that a deploy deleted reads as a permissions fault -- which sends whoever is
    debugging it to the policy instead of to the publication order. The listing
    itself stays unreachable: it is `GET /?list-type=2`, and the cache policy on
    the static behaviour forwards no query string.
    """
    policy = (WEB / "main.tf").read_text(encoding="utf-8")
    assert '"s3:ListBucket"' in policy, (
        "the bucket policy grants `s3:GetObject` alone again, so a missing asset is a "
        "403 and says the wrong thing about why"
    )
    conditions = re.findall(r'variable\s*=\s*"AWS:SourceArn"', policy)
    assert len(conditions) >= 2, (
        "a statement in the bucket policy has no `AWS:SourceArn` condition -- every "
        "grant here is to THIS distribution, not to CloudFront in general"
    )
