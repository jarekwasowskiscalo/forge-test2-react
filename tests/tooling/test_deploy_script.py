"""deploy.sh's two refusals and its one way through, proven without an AWS account.

Both refusals exist because of the same failure, found by reading rather than by
running. `deploy.sh` used to pass `-auto-approve` to `infra.sh`, which asks its
own question first; that question does a bare `read` on a closed stdin, and under
`set -euo pipefail` a failing `read` kills the shell **before** `die` can print
anything. A deployment from GitHub Actions therefore ended with exit 1 and not one
word saying why. The flag is now `--yes`, an intent the script turns into
Terraform's flag, and every path that could have hung now says so instead.

The stub: `deploy.sh` and `_lib.sh` are copied into a tmp tree verbatim --
`_lib.sh` derives `REPO_ROOT` from its own file location and never from `$PWD`,
so the copy re-roots itself for free -- and `package.sh` becomes a two-line stub
that leaves a marker and fails. The marker is the whole point: it says whether the
guards ran BEFORE the five minutes a real package takes, which is the difference
between a refusal that costs a second and one that costs a build.

The last two tests are about the health probe instead, and reach it differently.
`wait_for_health` is step 7 of a deployment and the stub above stops at step 1,
so a run cannot arrive there without an AWS account; the function's own text is
lifted out of the script and evaluated on its own, with `curl` stubbed to answer
whatever the case is about. That is worth the awkwardness, because the failure
it guards is a gate reporting green: CloudFront used to turn every 403 and 404
into `200 text/html` carrying the shell, and a probe that discarded the body
could not tell that from a healthy environment.
"""

import json
import pathlib
import shutil
import subprocess
import sys

_REPO = pathlib.Path(__file__).resolve().parents[2]

#: What deploy.sh shells out to before it reaches any AWS call. `aws` is stubbed
#: too, so the run reaches the build on a machine that has no AWS CLI at all --
#: which is every runner in the `scripts` job.
_MARKER = "reached"


def _plant(tmp_path: pathlib.Path) -> pathlib.Path:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("deploy.sh", "_lib.sh"):
        shutil.copy2(_REPO / "scripts" / name, scripts / name)

    package = scripts / "package.sh"
    package.write_text(f'#!/usr/bin/env bash\ntouch "$(dirname "$0")/../{_MARKER}"\nexit 1\n')
    package.chmod(0o755)

    #: Stubbed so the run reaches the build on a machine with no AWS CLI, which is
    #: every runner in the `scripts` job. It is never called: package.sh fails first.
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    aws = stub_bin / "aws"
    aws.write_text("#!/usr/bin/env bash\nexit 0\n")
    aws.chmod(0o755)

    return scripts / "deploy.sh"


def _run(
    script: pathlib.Path, *args: str, ci: bool = False, stdin_closed: bool = True
) -> subprocess.CompletedProcess[str]:
    root = script.parent.parent
    env = {"PATH": f"{root / 'bin'}:/usr/bin:/bin", "HOME": str(root)}
    if ci:
        env["GITHUB_ACTIONS"] = "true"
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        env=env,
        stdin=subprocess.DEVNULL if stdin_closed else None,
        timeout=60,
    )


def test_an_unknown_environment_is_refused_by_name(tmp_path: pathlib.Path) -> None:
    """The message names what was asked for and what exists, in that order.

    `dev` used to be one of the answers and is now the commonest wrong one, so the
    refusal points at the thing that replaced it rather than only listing two
    names.
    """
    script = _plant(tmp_path)
    result = _run(script, "dev", ci=True)

    assert result.returncode != 0
    assert "stage" in result.stderr
    assert "prod" in result.stderr
    assert "preview" in result.stderr, (
        "a branch that used to deploy to dev now gets a preview; the message should say so"
    )


def test_a_deployment_from_a_workstation_is_refused_with_a_sentence(
    tmp_path: pathlib.Path,
) -> None:
    """And refused before the build, so being told costs a second, not five minutes."""
    script = _plant(tmp_path)
    result = _run(script, "stage", "--yes", ci=False)

    assert result.returncode != 0
    assert "GitHub Actions" in result.stderr
    assert "SDD_DEPLOY_BREAK_GLASS" in result.stderr, (
        "a refusal with no way through is a refusal somebody works around"
    )
    assert not (tmp_path / _MARKER).exists(), (
        "the guard ran after package.sh, so the refusal cost a whole build"
    )


def test_a_pipeline_without_yes_is_told_rather_than_left_to_hang(
    tmp_path: pathlib.Path,
) -> None:
    """The regression this file exists for: a closed stdin used to kill the shell silently."""
    script = _plant(tmp_path)
    result = _run(script, "stage", ci=True)

    assert result.returncode != 0
    assert "--yes" in result.stderr, (
        "this is the failure that produced exit 1 and an empty log; it must speak"
    )
    assert not (tmp_path / _MARKER).exists()


def test_yes_from_actions_reaches_the_build(tmp_path: pathlib.Path) -> None:
    """The one way through, so the guards above cannot pass by refusing everything."""
    script = _plant(tmp_path)
    result = _run(script, "stage", "--yes", ci=True)

    assert (tmp_path / _MARKER).exists(), f"never reached package.sh: {result.stderr}"


def test_help_answers_on_a_runner_with_no_toolchain(tmp_path: pathlib.Path) -> None:
    """What `scripts/hygiene.sh` demands of every script here, exercised at the boundary."""
    script = _plant(tmp_path)
    result = _run(script, "--help", ci=False)

    assert result.returncode == 0
    assert "--yes" in result.stdout


# --------------------------------------------------------------------------- #
# The health probe reads the body
# --------------------------------------------------------------------------- #

#: Source `_lib.sh` for `info`/`warn`, lift `wait_for_health` out of `deploy.sh`
#: and call it. `deploy.sh` cannot be sourced -- it parses arguments and deploys
#: -- and the function is unreachable by running it without an AWS account, so
#: the shipped text is extracted and evaluated rather than re-typed here. A copy
#: of the function in this file would pass forever after the real one rotted.
_HEALTH_DRIVER = """\
set -euo pipefail
source "$1"
eval "$(sed -n '/^wait_for_health()/,/^}$/p' "$2")"
wait_for_health "$3"
"""


def _ask_health(tmp_path: pathlib.Path, answer: str) -> subprocess.CompletedProcess[str]:
    """Run `wait_for_health` against a `curl` that always succeeds with `answer`.

    Succeeding is the point: `curl -fsS` returning 0 is exactly what the edge
    used to manufacture out of a 404.
    """
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    curl = stub_bin / "curl"
    curl.write_text(f"#!/usr/bin/env bash\ncat <<'BODY'\n{answer}\nBODY\n")
    curl.chmod(0o755)

    return subprocess.run(
        [
            "bash",
            "-c",
            _HEALTH_DRIVER,
            "wait_for_health",
            str(_REPO / "scripts" / "_lib.sh"),
            str(_REPO / "scripts" / "deploy.sh"),
            "https://example.invalid",
        ],
        capture_output=True,
        text=True,
        env={"PATH": f"{stub_bin}:/usr/bin:/bin", "HOME": str(tmp_path)},
        #: Well under the two minutes twelve retries would take, so a probe that
        #: treats a wrong answer as a slow one fails here by timing out.
        timeout=45,
    )


def test_the_application_shell_is_not_a_healthy_api(tmp_path: pathlib.Path) -> None:
    """The regression this pair exists for, and the reason the edge fix is not enough alone.

    A deploy whose API answered nothing at all used to reach `ok` here, because
    `curl` was asked only whether it succeeded and the 200 it succeeded on was
    the SPA shell CloudFront substituted. The distribution no longer does that
    (`infra/terraform/modules/web/main.tf`), and this asks the probe to notice by
    itself regardless -- a gate that works only while the layer underneath is
    correct is not a gate.
    """
    result = _ask_health(tmp_path, '<!doctype html><html><body><div id="root"></div></body></html>')

    assert result.returncode != 0, "an HTML shell was accepted as a health document"
    assert "health document" in result.stderr, (
        f"the refusal has to say what came back instead: {result.stderr}"
    )


def test_the_health_document_the_contract_promises_is_accepted(tmp_path: pathlib.Path) -> None:
    """So the test above cannot be passed by refusing everything.

    The body is the one `contracts/openapi/health.yaml` freezes -- `status`,
    `environment` and `version` -- which is why `status` is what the probe looks
    for.
    """
    result = _ask_health(tmp_path, '{"status": "ok", "environment": "stage", "version": "0.1.0"}')

    assert result.returncode == 0, f"a healthy environment was refused: {result.stderr}"


# --------------------------------------------------------------------------- #
# The rollback chooses from the register of what served
# --------------------------------------------------------------------------- #

#: The whole rollback path runs, against an account that is a directory of canned
#: answers. Nothing is lifted and nothing is re-typed: the assertion is on what the
#: script asked the CLI to do, which is the only thing that matters about a rollback.
_AWS_STUB = """\
#!/usr/bin/env bash
answers="$(dirname "$0")/../answers"
case "$1 $2" in
    "lambda get-alias")               cat "$answers/current" ;;
    "ssm get-parameter")              [ -s "$answers/manifest" ] || exit 255
                                      cat "$answers/manifest" ;;
    "lambda get-function-configuration")
                                      [ -s "$answers/digest" ] || exit 255
                                      cat "$answers/digest" ;;
    "lambda update-alias")            echo "$*" >>"$answers/update-alias" ; echo done ;;
    "ssm put-parameter")              echo "$*" >>"$answers/put-parameter" ; echo done ;;
    *)                                exit 0 ;;
esac
"""

#: Answers whatever the case put in `answers/`, keyed by the path asked for, and
#: appends the status and media type `post_deploy_smoke` reads through `-w`. A stub
#: that ignored the path could not tell the two questions the contract declares apart.
_CURL_STUB = """\
#!/usr/bin/env bash
answers="$(dirname "$0")/../answers"
url="${@: -1}"
case "$url" in
    *"/api/health"*)             file=health ;;
    *"/api/"*)                   file=list ;;
    *)                           file=shell ;;
esac
cat "$answers/$file"
for argument in "$@"; do
    if [ "$argument" = "-w" ]; then
        printf '\n%s\n%s\n' "$(cat "$answers/$file.status")" "$(cat "$answers/$file.type")"
        break
    fi
done
"""

#: `wait_for_health` waits ten seconds between attempts, and nothing here is ever
#: slow. Without this a case that makes the probe retry costs two minutes.
_SLEEP_STUB = "#!/usr/bin/env bash\nexit 0\n"

_HEALTHY = '{"status": "ok", "environment": "prod", "version": "1.0.0"}'
_SHELL = '<!doctype html><html><body><div id="root"></div></body></html>'
_PAGE = '{"items": [], "total": 0, "total_all": 0}'

#: `uv run python X` -> `python X`, so the tmp tree's copies of the real Python
#: modules run under the interpreter this suite is already using.
_UV_STUB = """\
#!/usr/bin/env bash
case "$1" in
    run) shift 2; exec "{python}" "$@" ;;
    *)   exit 0 ;;
esac
"""

#: What `read_outputs` reads. `infra.sh` is stubbed rather than run: it would reach
#: Terraform, and every name below is a string this script only passes along.
_OUTPUTS = """\
#!/usr/bin/env bash
cat <<'JSON'
{"api_function_name": {"value": "fn"},
 "api_alias_name": {"value": "live"},
 "url": {"value": "https://example.invalid"},
 "release_manifest_parameter": {"value": "/p/prod/releases"}}
JSON
"""


def _answer(tmp_path: pathlib.Path, which: str, body: str, status: str, media: str) -> None:
    """What the stubbed `curl` says when that question is asked."""
    answers = tmp_path / "answers"
    (answers / which).write_text(body)
    (answers / f"{which}.status").write_text(status)
    (answers / f"{which}.type").write_text(media)


def _rollback_tree(
    tmp_path: pathlib.Path,
    *,
    manifest: str,
    current: str,
    digest: str,
    contracts: bool = False,
) -> pathlib.Path:
    """A tree whose `aws` answers exactly what this case is about.

    Without `contracts` the tree carries no `contracts/openapi/`, so the smoke refuses
    for want of a question and the run ends in seconds -- which is all the cases about
    choosing a version need, since the choice happens before it.
    """
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in (
        "deploy.sh",
        "_lib.sh",
        "release_manifest.py",
        "smoke_contract.py",
        # `smoke_contract` reads the contracts through it: one reader, two callers.
        "openapi_contract.py",
    ):
        shutil.copy2(_REPO / "scripts" / name, scripts / name)
    if contracts:
        shutil.copytree(_REPO / "contracts", tmp_path / "contracts")

    infra = scripts / "infra.sh"
    infra.write_text(_OUTPUTS)
    infra.chmod(0o755)

    # Outside the tree, so stating an answer never dirties the thing under test.
    answers = tmp_path / "answers"
    answers.mkdir()
    (answers / "manifest").write_text(manifest)
    (answers / "current").write_text(f"{current}\n")
    (answers / "digest").write_text(digest)

    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    aws = stub_bin / "aws"
    aws.write_text(_AWS_STUB)
    aws.chmod(0o755)
    uv = stub_bin / "uv"
    uv.write_text(_UV_STUB.format(python=sys.executable))
    uv.chmod(0o755)
    curl = stub_bin / "curl"
    curl.write_text(_CURL_STUB)
    curl.chmod(0o755)
    nap = stub_bin / "sleep"
    nap.write_text(_SLEEP_STUB)
    nap.chmod(0o755)

    _answer(tmp_path, "health", _HEALTHY, "200", "application/json")
    _answer(tmp_path, "shell", _SHELL, "200", "text/html")
    _answer(tmp_path, "list", _PAGE, "200", "application/json")

    return scripts / "deploy.sh"


def _rolled_to(tmp_path: pathlib.Path) -> str:
    """The version the script asked the alias to serve, or `""` if it asked nothing."""
    calls = tmp_path / "answers" / "update-alias"
    if not calls.is_file():
        return ""
    words = calls.read_text().split()
    return words[words.index("--function-version") + 1]


def _served(version: str, digest: str = "sha-of-" + "a" * 8, **extra: str) -> dict[str, str]:
    return {
        "version": version,
        "commit": "abc1234",
        "environment": "prod",
        "digest": digest,
        **extra,
    }


def test_the_rollback_goes_to_the_version_that_served_not_the_one_published_after_it(
    tmp_path: pathlib.Path,
) -> None:
    """**The finding, end to end.** Version 5 exists on the account -- an apply published
    it and the deploy stopped before the alias moved -- and only 4 and 6 ever served.
    The rule this replaces took "the highest published version below 6" and answered 5:
    production traffic onto code that was never live, reported as `Rollback: OK`.
    """
    script = _rollback_tree(
        tmp_path,
        manifest=json.dumps([_served("4"), _served("6")]),
        current="6",
        digest="sha-of-aaaaaaaa\n",
    )

    _run(script, "prod", "--rollback", "--yes", ci=True)

    assert _rolled_to(tmp_path) == "4", "the alias was not moved to the last version that served"


def test_a_rollback_without_a_manifest_refuses_and_moves_nothing(tmp_path: pathlib.Path) -> None:
    """The register is the only thing that can answer, so no register is a refusal --
    and the refusal carries the command a person runs when they know what they want,
    because the behaviour being replaced always moved a pointer.
    """
    script = _rollback_tree(tmp_path, manifest="", current="6", digest="sha\n")

    result = _run(script, "prod", "--rollback", "--yes", ci=True)

    assert result.returncode != 0
    assert _rolled_to(tmp_path) == "", "an alias was moved with nothing saying where to"
    assert "no release manifest yet" in result.stderr, result.stderr
    assert "aws lambda update-alias" in result.stderr, (
        f"a refusal during an incident has to name the manual way: {result.stderr}"
    )


def test_an_alias_no_green_deploy_recorded_is_refused(tmp_path: pathlib.Path) -> None:
    """What a deploy that failed after moving the alias leaves behind -- the commonest
    way to need a rollback. The old rule would have picked a number here regardless.
    """
    script = _rollback_tree(
        tmp_path,
        manifest=json.dumps([_served("4"), _served("6")]),
        current="9",
        digest="sha\n",
    )

    result = _run(script, "prod", "--rollback", "--yes", ci=True)

    assert result.returncode != 0
    assert _rolled_to(tmp_path) == ""
    assert "failed after moving the alias" in result.stderr, result.stderr


def test_a_version_that_is_no_longer_on_the_account_is_refused(tmp_path: pathlib.Path) -> None:
    """The register says it served; the account says it is gone. Moving an alias onto a
    version that does not exist takes the environment down rather than back."""
    script = _rollback_tree(
        tmp_path,
        manifest=json.dumps([_served("4"), _served("6")]),
        current="6",
        digest="",
    )

    result = _run(script, "prod", "--rollback", "--yes", ci=True)

    assert result.returncode != 0
    assert _rolled_to(tmp_path) == ""
    assert "no such version any more" in result.stderr, result.stderr


def test_a_version_whose_build_is_not_the_recorded_one_is_refused(tmp_path: pathlib.Path) -> None:
    """Replace the function and Lambda starts numbering at 1 again, so a recorded "4"
    then names different code. The digest is what makes the number checkable rather
    than merely findable."""
    script = _rollback_tree(
        tmp_path,
        manifest=json.dumps([_served("4", digest="the-build-that-served"), _served("6")]),
        current="6",
        digest="a-different-build\n",
    )

    result = _run(script, "prod", "--rollback", "--yes", ci=True)

    assert result.returncode != 0
    assert _rolled_to(tmp_path) == ""
    assert "not the build the manifest recorded" in result.stderr, result.stderr


def test_a_rollback_records_itself_and_what_it_rolled_away_from(tmp_path: pathlib.Path) -> None:
    """Without that second half the next rollback of the same incident walks forward
    into the release this one was called to escape -- the trap the replaced code tried
    to avoid with a comment and could not."""
    script = _rollback_tree(
        tmp_path,
        manifest=json.dumps([_served("4"), _served("6")]),
        current="6",
        digest="sha-of-aaaaaaaa\n",
        contracts=True,
    )

    result = _run(script, "prod", "--rollback", "--yes", ci=True)

    assert result.returncode == 0, f"a healthy rollback was reported as failed: {result.stderr}"
    written = (tmp_path / "answers" / "put-parameter").read_text()
    assert "/p/prod/releases" in written
    assert '"rolled_back_from":"6"' in written, (
        f"the register does not say what was left: {written}"
    )
    assert '"version":"4"' in written


# --------------------------------------------------------------------------- #
# The smoke asks what the contract says, and says which of three things went wrong
# --------------------------------------------------------------------------- #

#: The real `post_deploy_smoke`, run against the real `contracts/openapi/` and the real
#: `smoke_contract.py`, with only the answers faked. `REPO_ROOT` comes from the real
#: `_lib.sh`, which is what makes "the question is read out of the contract" a claim
#: this file can check rather than restate.
_SMOKE_DRIVER = """\
set -euo pipefail
source "$1"
eval "$(sed -n '/^wait_for_health()/,/^}$/p' "$2")"
eval "$(sed -n '/^post_deploy_smoke()/,/^}$/p' "$2")"
post_deploy_smoke "$3"
"""


def _smoke(
    tmp_path: pathlib.Path, list_body: str, status: str = "200", media: str = "application/json"
) -> subprocess.CompletedProcess[str]:
    (tmp_path / "answers").mkdir(exist_ok=True)
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir(exist_ok=True)
    for name, text in (
        ("curl", _CURL_STUB),
        ("sleep", _SLEEP_STUB),
        ("uv", _UV_STUB.format(python=sys.executable)),
    ):
        stub = stub_bin / name
        stub.write_text(text)
        stub.chmod(0o755)

    _answer(tmp_path, "health", _HEALTHY, "200", "application/json")
    _answer(tmp_path, "shell", _SHELL, "200", "text/html")
    _answer(tmp_path, "list", list_body, status, media)

    return subprocess.run(
        [
            "bash",
            "-c",
            _SMOKE_DRIVER,
            "post_deploy_smoke",
            str(_REPO / "scripts" / "_lib.sh"),
            str(_REPO / "scripts" / "deploy.sh"),
            "https://example.invalid",
        ],
        capture_output=True,
        text=True,
        env={"PATH": f"{stub_bin}:/usr/bin:/bin", "HOME": str(tmp_path)},
        timeout=60,
    )


def test_the_smoke_asks_the_collection_the_contract_declares(tmp_path: pathlib.Path) -> None:
    """**The defect, and it could not be seen from inside this file before.** The smoke
    asked `/api/entries` for a field `matching`; the contract has said
    `/api/guestbook-entries` with `total_all` since before either was typed. Now the
    path and the keys come out of `contracts/openapi/`, so this asserts the real one.
    """
    result = _smoke(tmp_path, _PAGE)

    assert result.returncode == 0, (
        f"a deployment answering its contract was refused: {result.stderr}"
    )
    assert "/api/guestbook-entries" in result.stdout, result.stdout
    assert "/api/entries " not in result.stdout


def test_an_envelope_missing_a_promised_field_names_the_field(tmp_path: pathlib.Path) -> None:
    result = _smoke(tmp_path, '{"items": [], "total": 0}')

    assert result.returncode != 0, "a page without total_all was accepted"
    assert "total_all" in result.stderr, result.stderr


def test_a_path_the_deployment_does_not_serve_is_not_reported_as_a_bad_envelope(
    tmp_path: pathlib.Path,
) -> None:
    """The sentence that sent an operator into the application to look for a fault in
    the smoke. A 404 is the deployment saying it does not serve that path, and it now
    says exactly that instead of blaming the envelope."""
    result = _smoke(tmp_path, '{"detail": "Not found"}', status="404")

    assert result.returncode != 0
    assert "404" in result.stderr, result.stderr
    assert "envelope" not in result.stderr, (
        f"a 404 was reported as an envelope fault: {result.stderr}"
    )


def test_an_answer_that_is_not_json_is_reported_as_what_arrived(tmp_path: pathlib.Path) -> None:
    """The third of the three, and the one the old single check could not express: it
    piped into `json.load`, so every failure past the request came out as one sentence.
    """
    result = _smoke(tmp_path, _SHELL, media="text/html")

    assert result.returncode != 0
    assert "not JSON" in result.stderr, result.stderr
    assert "text/html" in result.stderr, result.stderr


def test_the_spa_is_published_without_deleting_what_earlier_releases_wrote() -> None:
    """Read as text, because no test here uploads anything and the damage this guards
    against is permanent. `package.sh` empties the build directory before it builds, so
    the source holds exactly one release: `--delete` on either sync meant "remove every
    file every earlier release wrote", and the bundles an already-loaded shell names
    went with it. Nothing else in the repository would notice it coming back.
    """
    text = (_REPO / "scripts" / "deploy.sh").read_text(encoding="utf-8")
    publish = text[text.index('step "Uploading the hashed assets"') : text.index("6. Invalidate")]
    # Comments stripped: the block explains at length that `--delete` is gone, and a
    # check that matched its own explanation would be red while the code was right.
    commands = [line for line in publish.splitlines() if not line.lstrip().startswith("#")]

    assert any("aws s3 sync" in line for line in commands), (
        "this no longer reads the block it means to"
    )
    assert not any("--delete" in line for line in commands), (
        "a sync that deletes is back in the publication step; a release before this one "
        "cannot be served after it"
    )
