"""Smoke UI: the built SPA, in a real browser, against the running application.

Plain pytest over bare Playwright (sync, Chromium only) -- no Gherkin, no
pytest-playwright plugin. The decision, its rejected alternatives and the
artefact policy live in
`spec/design/testing.md` § The UI smoke in a browser; the policy's
implementation is the conftest beside this file.
"""
