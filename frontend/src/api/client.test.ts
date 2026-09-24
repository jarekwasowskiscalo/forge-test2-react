import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from './problem'
import { client, unwrap } from './client'

/**
 * What the client actually puts on the wire, and what `unwrap` does with the
 * answer.
 *
 * The path assertion is the one that earns its keep: `client.ts` sets **no
 * `baseUrl`**, and the reason is that the generated `paths` type carries the
 * `/api` prefix. A `baseUrl: '/api'` added later would still compile at some
 * call sites and would silently send `/api/api/...`, so the absence is
 * asserted rather than commented.
 *
 * Stubbing, in the order it has to happen:
 *
 * 1. `vi.hoisted` -- `client.ts` calls `createClient()` at module scope and
 *    `openapi-fetch` reads `globalThis.fetch` exactly once, right then. A stub
 *    installed after the import would never be seen.
 * 2. `Request` is wrapped with an origin, because undici refuses to parse an
 *    origin-less `/api/...` path.
 */
const stubs = vi.hoisted(() => {
  const RealRequest = globalThis.Request

  function RequestWithBase(input: RequestInfo | URL, init?: RequestInit): Request {
    const absoluteInput =
      typeof input === 'string' && input.startsWith('/') ? `http://localhost${input}` : input
    return new RealRequest(absoluteInput, init)
  }
  RequestWithBase.prototype = RealRequest.prototype
  vi.stubGlobal('Request', RequestWithBase)

  const fetchStub = vi.fn(
    (_input: Request): Promise<Response> =>
      Promise.reject(new Error('fetch called before the test configured a response')),
  )
  vi.stubGlobal('fetch', fetchStub)
  return { fetchStub }
})

/** The last request the client actually put on the wire. */
function sentRequest(): Request {
  const call = stubs.fetchStub.mock.calls.at(-1)
  if (call === undefined) throw new Error('no request was sent')
  return call[0]
}

function answerWith(status: number, body: unknown): void {
  stubs.fetchStub.mockImplementation(() =>
    Promise.resolve(
      status === 204
        ? new Response(null, { status })
        : new Response(JSON.stringify(body), {
            status,
            headers: { 'content-type': 'application/json' },
          }),
    ),
  )
}

const ENTRY = {
  id: '0d0d5c3a-6d9c-4a1e-9a4a-2f7f6f0e5b11',
  author: 'Anna',
  message: 'Good morning',
  created_at: '2026-08-30T20:00:00Z',
  updated_at: '2026-08-30T20:00:00Z',
}

beforeEach(() => {
  answerWith(200, [ENTRY])
})

afterEach(() => {
  stubs.fetchStub.mockReset()
})

describe('the client sends the path the schema names', () => {
  it('keeps the /api prefix, because it is part of the generated path type', async () => {
    await unwrap(client.GET('/api/guestbook-entries'))

    expect(new URL(sentRequest().url).pathname).toBe('/api/guestbook-entries')
  })

  it('substitutes a path parameter rather than sending the template', async () => {
    answerWith(200, ENTRY)

    await unwrap(
      client.PATCH('/api/guestbook-entries/{entry_id}', {
        params: { path: { entry_id: ENTRY.id } },
        body: { message: 'corrected' },
      }),
    )

    const request = sentRequest()
    expect(new URL(request.url).pathname).toBe(`/api/guestbook-entries/${ENTRY.id}`)
    expect(request.method).toBe('PATCH')
  })

  it('sends no credentials, because this template has no session to carry', async () => {
    // The counterpart of the paragraph in `client.ts`: authentication is absent
    // by decision, not by oversight, and `credentials: 'include'` added without
    // a service that sets a cookie would read like protection that is not there.
    await unwrap(client.GET('/api/guestbook-entries'))

    expect(sentRequest().credentials).not.toBe('include')
  })
})

describe('unwrap turns a refusal into a throw', () => {
  it('throws ApiError carrying the status, so TanStack Query sees a failure', async () => {
    answerWith(404, {
      detail: { code: 'guestbook_entry_not_found', message: 'There is no such entry.' },
    })

    await expect(
      unwrap(
        client.GET('/api/guestbook-entries/{entry_id}', {
          params: { path: { entry_id: ENTRY.id } },
        }),
      ),
    ).rejects.toBeInstanceOf(ApiError)
  })

  it('returns the body on success', async () => {
    const entries = await unwrap(client.GET('/api/guestbook-entries'))

    expect(entries).toEqual([ENTRY])
  })

  it('resolves a 204 rather than failing on its missing body', async () => {
    // `DELETE` answers 204 with nothing at all. `unwrap` returning `undefined`
    // there is what lets the void-returning mutation await it; an implementation
    // that insisted on a body would make every successful delete look like an
    // error.
    answerWith(204, null)

    await expect(
      unwrap(
        client.DELETE('/api/guestbook-entries/{entry_id}', {
          params: { path: { entry_id: ENTRY.id } },
        }),
      ),
    ).resolves.toBeUndefined()
  })
})
