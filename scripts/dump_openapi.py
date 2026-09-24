"""Write the app's OpenAPI schema to a file without starting a server.

The frontend's `src/api/schema.d.ts` is generated from this schema and is the
only thing that keeps the two halves of the app in agreement about the JSON
shape of `/api/*`. CI regenerates it and fails on a diff, which turns
contract drift into a build error instead of a runtime one.

Reading the schema from a running Uvicorn (the form ARCHITECTURE.md shows)
works too, but needs a server and a reachable database in CI just to print a
JSON document. `app.openapi()` needs neither: importing `app.main` only
constructs a SQLAlchemy Engine, which does not connect until a session is
used. `DATABASE_URL` therefore never has to point at a live database here --
it only has to parse -- so this script defaults it to a URL that is well formed
and deliberately unreachable. If anything downstream ever DOES open a session,
it fails on a refused connection rather than quietly writing to whichever
database the developer's shell happened to name.

Usage:
    uv run scripts/dump_openapi.py [output_path]

Defaults to writing `openapi.json` in the repository root.
"""

import json
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "openapi.json"

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://nobody@no-database.invalid:5432/none")
sys.path.insert(0, str(REPO_ROOT))

from app.main import app  # noqa: E402  (import needs the path/env set up above)


def main(argv: list[str]) -> int:
    """Write the schema to `argv[1]` (or the default path) and report where."""
    output = pathlib.Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    # `encoding="utf-8"` is load-bearing, not tidiness. `ensure_ascii=False`
    # means this file carries the text in the schema descriptions
    # verbatim, and without an explicit encoding Python writes it in the
    # platform default -- not UTF-8 under a C locale, which either raises or emits
    # bytes `openapi-typescript` then reads as mojibake. The failure would be
    # a corrupt committed artifact, not an error.
    output.write_text(
        json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
