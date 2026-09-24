# One deployable artifact: one image, one process, one port.
#
# The Node stage exists only to run Vite. It does not survive into the final
# image -- production has no Node runtime, and FastAPI serves the compiled
# bundle itself. Because both halves answer on the same origin there is no
# CORS configuration anywhere and cookies work with zero setup.
#
# **Both bases are pinned by DIGEST, and the tag is kept beside it for a reader.**
# A tag is a moving name: `python:3.12-slim` is a different image this month than
# last, so an image built from a tag is not reproducible and CI's `image` job --
# which is a gate -- would be checking something different every week. That is the
# case Article XIII of the constitution refuses ("unpinned tool versions in a
# gate"), and it was true here until now. A digest is the bytes.
#
# The cost is that a digest goes stale silently, since nothing warns you that a
# base has security fixes you have not taken. That is why `.github/dependabot.yml`
# has a `docker` ecosystem: the bump arrives as a pull request somebody reads,
# rather than as rot nobody sees or as a surprise nobody asked for.
# `tests/tooling/test_container_pins.py` holds both halves.

FROM node:26-alpine@sha256:2d984a15c9b54fd0aeb608b8e0d0d83529eb34d2966db27a1fb4f1edc3d298a3 AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# outDir in vite.config.ts points at ../app/static, which does not exist in
# this stage; --outDir keeps the build inside /fe/dist instead.
RUN npm run build -- --outDir dist --emptyOutDir


FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
# `--no-default-groups`, not `--no-dev`: the latter is an alias of
# `--no-group dev` and nothing more, so with `default-groups = ["dev", "e2e"]`
# in pyproject.toml it would install pytest, pytest-bdd, gherkin-official,
# parse and parse-type into the runtime image. Nothing downstream would notice
# -- the image job only asks /api/health whether it is alive.
RUN pip install --no-cache-dir uv==0.12.5 && uv sync --frozen --no-default-groups --no-install-project

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/

# Build output lands where app/main.py looks for it.
COPY --from=frontend /fe/dist ./app/static

# Nothing in the image needs to write to it, so nothing runs as root. `app` owns
# no files: the tree is copied by root and only read at runtime.
RUN useradd --system --create-home --uid 10001 app
USER app

EXPOSE 8000

# The API's own liveness route, not the SPA shell: `/health` (no prefix) is
# matched by the catch-all in app/main.py and answers 200 with HTML for as long
# as index.html exists, which would make a broken API look healthy.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health').read()"

# Migrations are deliberately NOT run here: Alembic owns the schema and a
# container that migrates on start would race every other replica. Run
# `alembic upgrade head` as a release step before rolling this image out.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
