#!/usr/bin/env bash
# The record of a change that did NOT go through the change process.
#
# A behaviour change carries its reasoning in `spec/changes/<CR>/`. Everything else --
# the scripts, CI, the documentation, the tooling, a repair on the trunk -- is made
# with no change record at all (spec/constitution.md, Article XIII), and until this
# script existed its reasoning survived only in a squash-commit body. One file per
# pull request, under changelog/, is where it survives now.
#
# Two verbs: `new` writes the form, `check` is the gate CI runs on the pull request.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

ENTRIES_DIR="changelog"
TEMPLATE="$ENTRIES_DIR/TEMPLATE.md"

#: The sections every entry answers, in the order it answers them. A section is never
#: removed: "None -- nothing about running this repository moves" is information, and a
#: missing heading is a hole nobody can tell from an oversight.
SECTIONS=(
    "## What changed"
    "## Why"
    "## From what, to what"
    "## How it works now"
    "## What it means for the process"
    "## What it does not change"
    "## How it was verified"
)

#: What a change is. Coarse on purpose -- this sorts a list, it does not drive anything.
KINDS="feature fix chore ci docs process deps"

usage() {
    cat <<'TEXT'
usage: changelog.sh new "<title>"
       changelog.sh check [--base <ref>] [--author <login>] [--labels <a,b>]
       changelog.sh check --file <path>

The record of a change made outside the SDD process. One file per pull request,
under changelog/, named <YYYY-MM-DD>-<slug>.md. See changelog/README.md.

  new "<title>"     Write today's entry from changelog/TEMPLATE.md and print its
                    path. The title is the commit subject: an imperative sentence,
                    no type prefix and no ticket.

  check             The gate. Reads the diff against <ref> and demands that the
                    pull request adds a well-formed entry. It passes, saying why,
                    when there is no base to diff against, when the author is a
                    bot, when the labels carry `no-changelog`, or when the diff
                    touches a change directory under spec/changes/CR-*.

  check --file P    Just the shape of one entry: front matter, one title, every
                    section present and none of them still empty.

Options, each with an environment fallback so a workflow can pass it once:
  --base <ref>      CHANGELOG_BASE     the commit the pull request is against
  --author <login>  CHANGELOG_AUTHOR   the pull request's author
  --labels <a,b>    CHANGELOG_LABELS   its labels, comma or space separated

Exit: 0 the entry is there and well formed, or the change is exempt; 1 otherwise.
TEXT
}

#: The front matter, without its fences. Empty when the file opens with anything else.
front_matter() {
    awk 'NR == 1 && $0 != "---" { exit } NR > 1 && $0 == "---" { exit } NR > 1' "$1"
}

#: The value of one front-matter key, or empty.
front_matter_value() {
    # One awk that reads to the end rather than `sed | head -1`: `head` quits at its
    # first line, and under `pipefail` the SIGPIPE it hands the stage before it is a
    # failure of the whole value.
    front_matter "$1" | awk -v key="$2:" \
        'index($0, key) == 1 && !found { sub("^" key "[[:space:]]*", ""); print; found = 1 }'
}

#: The sections whose body is nothing but blank lines and the form's own prompts.
#:
#: HTML comments are stripped before the body is judged, and across lines: the form
#: leaves a comment under every heading, so an entry nobody filled in reads as seven
#: sections with content unless they are taken out first.
empty_sections() {
    awk '
        /^## / { if (heading != "" && body == 0) print heading; heading = $0; body = 0; next }
        {
            line = $0
            if (open) {
                if (line !~ /-->/) next
                sub(/^.*-->/, "", line)
                open = 0
            }
            while (index(line, "<!--") > 0) {
                before = substr(line, 1, index(line, "<!--") - 1)
                after = substr(line, index(line, "<!--") + 4)
                if (index(after, "-->") > 0) {
                    line = before substr(after, index(after, "-->") + 3)
                } else {
                    line = before
                    open = 1
                    break
                }
            }
            if (heading != "" && line ~ /[^[:space:]]/) body = 1
        }
        END { if (heading != "" && body == 0) print heading }
    ' "$1"
}

#: Is this entry well formed? Says every way in which it is not, and returns 1.
verify_entry() {
    local path="$1" bad=0 value section empty
    if [ ! -f "$path" ]; then
        fail "$path does not exist"
        return 1
    fi
    case "${path##*/}" in
        [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.md) ;;
        *) fail "$path: an entry is named <YYYY-MM-DD>-<slug>.md, so the directory sorts by date"; bad=1 ;;
    esac
    if grep -q '^<!-- TEMPLATE:' "$path"; then
        fail "$path: still carries the template marker, so it counts as unwritten"
        bad=1
    fi
    if [ "$(head -1 "$path")" != "---" ]; then
        fail "$path: no front matter -- the first line has to be ---"
        bad=1
    fi
    value="$(front_matter_value "$path" date)"
    case "$value" in
        [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
        *) fail "$path: front matter has no 'date: YYYY-MM-DD'"; bad=1 ;;
    esac
    value="$(front_matter_value "$path" kind)"
    case " $KINDS " in
        *" $value "*) ;;
        *) fail "$path: 'kind: $value' is not one of $KINDS"; bad=1 ;;
    esac
    if [ "$(grep -c '^# ' "$path")" -ne 1 ]; then
        fail "$path: an entry has exactly one title, and it says what the change makes true"
        bad=1
    fi
    for section in "${SECTIONS[@]}"; do
        grep -qxF "$section" "$path" || { fail "$path: no section '$section'"; bad=1; }
    done
    empty="$(empty_sections "$path")"
    if [ -n "$empty" ]; then
        while IFS= read -r section; do
            fail "$path: '$section' is empty -- write the sentence that says there is nothing, do not delete the heading"
        done <<<"$empty"
        bad=1
    fi
    [ "$bad" -eq 0 ] || return 1
    ok "$path"
}

cmd_new() {
    local title="${1:-}" today slug path
    [ -n "$title" ] || die "changelog.sh new needs a title: changelog.sh new \"Say what the change makes true\""
    [ -f "$TEMPLATE" ] || die "$TEMPLATE is missing; it is the form every entry is copied from"
    today="$(date +%Y-%m-%d)"
    slug="$(printf '%s' "$title" | tr '[:upper:]' '[:lower:]' \
        | sed -e 's/[^a-z0-9]\{1,\}/-/g' -e 's/^-//' -e 's/-$//' | cut -c1-60 | sed -e 's/-$//')"
    [ -n "$slug" ] || die "the title has no letters or digits in it, so there is no name to give the file"
    path="$ENTRIES_DIR/$today-$slug.md"
    [ ! -e "$path" ] || die "$path already exists -- edit it, or give this change a different title"
    mkdir -p "$ENTRIES_DIR"
    {
        printf -- '---\ndate: %s\nbranch: %s\npr:\nkind: chore\n---\n\n# %s\n\n' \
            "$today" "$(git branch --show-current 2>/dev/null || echo '-')" "$title"
        # Everything from the first section on: the form's marker, front matter and
        # title are rewritten above, and `0,/re/` is a GNU extension this would be the
        # only user of on a Mac.
        awk '/^## / { body = 1 } body' "$TEMPLATE"
    } >"$path"
    step "Wrote $path"
    info "fill in every section, then: ./scripts/changelog.sh check --file $path"
    info "the form and the rules: $ENTRIES_DIR/README.md"
}

cmd_check() {
    local base="" author="" labels="" file="" resolved="" changed="" added="" problems=0 entry
    while [ $# -gt 0 ]; do
        case "$1" in
            --base) base="${2:-}"; shift 2 ;;
            --author) author="${2:-}"; shift 2 ;;
            --labels) labels="${2:-}"; shift 2 ;;
            --file) file="${2:-}"; shift 2 ;;
            *) usage >&2; die "unknown option: $1" ;;
        esac
    done
    base="${base:-${CHANGELOG_BASE:-}}"
    author="${author:-${CHANGELOG_AUTHOR:-}}"
    labels="${labels:-${CHANGELOG_LABELS:-}}"

    if [ -n "$file" ]; then
        step "The shape of one entry"
        verify_entry "$file" || summary "Changelog" 1
        summary "Changelog" 0
    fi

    step "Is an entry owed?"
    if [ -z "$base" ]; then
        ok "no base to diff against: this gate answers a question only a diff has"
        summary "Changelog" 0
    fi
    case "$author" in
        *"[bot]")
            ok "$author is a bot: it cannot write the reasoning, and a rule demanding it would be red every week"
            summary "Changelog" 0
            ;;
    esac
    case " ${labels//,/ } " in
        *" no-changelog "*)
            ok "the no-changelog label is on this pull request"
            summary "Changelog" 0
            ;;
    esac

    resolved="$base"
    git rev-parse --verify --quiet "$resolved^{commit}" >/dev/null 2>&1 || resolved="origin/$base"
    git rev-parse --verify --quiet "$resolved^{commit}" >/dev/null 2>&1 ||
        die "cannot resolve '$base' -- CI passes the pull request's base sha, and a local run needs a fetched ref"
    info "against $resolved"

    changed="$(git diff --name-only "$resolved...HEAD")"
    # A here-string, not `printf | grep -q`: grep quits at the first match, and a
    # printf still writing a large diff then fails on EPIPE, which `pipefail` reads
    # as "no change directory" -- a found answer reported as a missing one.
    if grep -q '^spec/changes/CR-' <<<"$changed"; then
        ok "this change has a change directory under spec/changes/, which is its record"
        summary "Changelog" 0
    fi

    # Two steps, so that `|| true` no longer forgives two different things at once: grep
    # answering "no entry" is 1 and is an answer; a git diff that failed is not.
    added_any="$(git diff --name-only --diff-filter=A "$resolved...HEAD" -- "$ENTRIES_DIR")"
    added="$(grep -E "^$ENTRIES_DIR/[0-9]{4}-[0-9]{2}-[0-9]{2}-.*\.md$" <<<"$added_any")" ||
        [ $? -eq 1 ] || die "could not filter the entries this change adds"
    if [ -z "$added" ]; then
        fail "this pull request adds no entry under $ENTRIES_DIR/"
        info "write one:  ./scripts/changelog.sh new \"Say what the change makes true\""
        info "or, for a typo, put the no-changelog label on the pull request"
        summary "Changelog" 1
    fi

    step "The entries it adds"
    while IFS= read -r entry; do
        verify_entry "$entry" || problems=1
    done <<<"$added"
    summary "Changelog" "$problems"
}

case "${1:-}" in
    -h|--help|"") usage; exit 0 ;;
    new) shift; cd "$REPO_ROOT"; cmd_new "$@" ;;
    check) shift; cd "$REPO_ROOT"; cmd_check "$@" ;;
    *) usage >&2; die "unknown verb: $1" ;;
esac
