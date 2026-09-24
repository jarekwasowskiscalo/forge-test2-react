import createClient from 'openapi-fetch'

import { ApiError, toProblem } from './problem'
import type { paths } from './schema'

/**
 * The single fetch client for `/api/*`.
 *
 * There is deliberately **no `baseUrl`**. The `/api` prefix is applied on the
 * server (`app.include_router(api_router, prefix="/api")`), so it is part of
 * every path in the OpenAPI document and therefore part of the generated
 * `paths` type. Setting `baseUrl: '/api'` here would make call sites write
 * `/guestbook-entries` -- a string that does not exist in the schema, which
 * silently discards the type checking this client exists to provide.
 *
 * With no baseUrl, requests resolve relative to the page origin. The SPA and
 * the API are served from the same origin in production (one image, one
 * process) and the Vite dev server proxies `/api` to uvicorn, so every request
 * is same-origin in both. That is precisely why there is no CORS
 * configuration anywhere in this repo -- hardcoding an absolute origin here is
 * the one change that would break it.
 *
 * **There is no authentication in this template, so there is nothing here that
 * carries a credential and no 401 interceptor.** Adding one is two edits: give
 * this client `credentials: 'include'` so its cookie rides along, and register
 * a middleware that routes a 401 to your login screen. `main.tsx` is the
 * place the handler is installed from. Neither is stubbed out in advance,
 * because a security layer that is present but wired to nothing is the failure
 * mode this file has already had once: it echoed a `csrftoken` cookie into an
 * `X-CSRF-Token` header that no service ever set or checked, so it protected
 * nothing while reading, to an auditor, exactly like protection.
 */
export const client = createClient<paths>()

/**
 * Unwrap an openapi-fetch result, throwing `ApiError` on failure.
 *
 * TanStack Query decides success/failure by whether the query function
 * throws, so every call goes through here rather than each caller checking
 * `error` by hand. Errors are normalised to RFC 9457 problem details in one
 * place (see api/problem.ts).
 */
export async function unwrap<
  R extends { data?: unknown; error?: unknown; response: Response },
>(result: Promise<R>): Promise<NonNullable<R['data']>> {
  const { data, error, response } = await result

  if (error !== undefined || !response.ok) {
    throw new ApiError(toProblem(response.status, error))
  }
  // A 2xx with no body only happens for 204 -- `DELETE /api/guestbook-entries/{id}`
  // is the one, and its caller wants the success, not a body. `data` is
  // `undefined` there, which is what the void-returning mutation expects.
  return data as NonNullable<R['data']>
}
