"""Keep a preview out of search results.

A per-branch preview answers on a public, unauthenticated URL
(`infra/terraform/modules/preview_app/main.tf` says why: `AWS_IAM` authorization
would make it unopenable in a browser, which is the one thing a preview is for).
Short-lived and throwaway is an acceptable answer to "who can reach it"; it is not
an answer to "what if a crawler finds it", because an indexed page outlives the
branch that produced it by however long the index holds.

`X-Robots-Tag` is the header form of a `noindex` meta tag and applies to every
response, including the JSON ones -- which a `robots.txt` cannot do, and which a
meta tag in `index.html` cannot do either.

**Deployment-dependent, decided once.** The environment is read at construction
rather than per request, because it cannot change under a running process and a
liveness probe should not re-read it a thousand times a day. Stage and production
are untouched: there the middleware is not added at all.
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

#: The environments whose URLs are public and disposable. Only `preview` today;
#: a named set rather than a `!= "prod"` so adding an environment cannot silently
#: hide it from every search engine.
UNLISTED_ENVIRONMENTS = frozenset({"preview"})

_HEADER = (b"x-robots-tag", b"noindex, nofollow")


class NoIndexMiddleware:
    """Add `X-Robots-Tag: noindex, nofollow` to every response.

    Pure ASGI, like `RequestIdMiddleware` beside it: nothing is buffered, and a
    streamed response is untouched apart from its header block.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].append(_HEADER)
            await send(message)

        await self.app(scope, receive, send_with_header)
