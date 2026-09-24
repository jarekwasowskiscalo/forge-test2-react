/**
 * One error shape for the whole frontend.
 *
 * The target contract is RFC 9457 problem details (`type` / `title` /
 * `status` / `detail`, plus `errors` for field-level validation). The Python
 * service currently answers with FastAPI's own `{"detail": ...}` bodies --
 * a bare string for `HTTPException`, and a list of Pydantic error objects
 * for a 422 -- so `toProblem` normalises all three into the RFC shape at the
 * single point where responses are unwrapped.
 *
 * Everything downstream (pages, components, error boundaries) sees only
 * `Problem`. When the backend starts emitting real problem details, the
 * legacy branches below are the only code that becomes dead.
 */

export const PROBLEM_BLANK = 'about:blank'

/** A field-level validation failure, keyed by dotted field path. */
export type FieldErrors = Record<string, string[]>

export interface Problem {
  type: string
  title: string
  status: number
  detail?: string
  errors?: FieldErrors
}

/** FastAPI's 422 body: `{"detail": [{loc, msg, type}, ...]}`. */
interface PydanticError {
  loc?: (string | number)[]
  msg?: string
  type?: string
}

function isPydanticErrorList(value: unknown): value is PydanticError[] {
  return (
    Array.isArray(value) &&
    value.every((entry) => typeof entry === 'object' && entry !== null && 'msg' in entry)
  )
}

/**
 * A refusal: `{"detail": {"code", "message", ...}}`.
 *
 * The shape `app/platform/schemas/refusals.py` declares and every route that can
 * refuse names in its `responses=`, so the generated contract carries it as
 * `RefusalDetail`. A stable `code` a screen can branch on, and a finished sentence
 * in `message` a person can read; the codes and their sentences are frozen in
 * `contracts/openapi/guestbook.yaml` (`x-refusals`) and stated in
 * `spec/design/api.md` § Refusals. Extra keys (`id`, ...) ride along untouched.
 */
interface RefusalDetail {
  code: string
  message: string
}

function isRefusalDetail(value: unknown): value is RefusalDetail {
  return (
    typeof value === 'object' &&
    value !== null &&
    !Array.isArray(value) &&
    typeof (value as RefusalDetail).message === 'string' &&
    typeof (value as RefusalDetail).code === 'string'
  )
}

/** The `type` URN a refusal is given, so a screen can branch without matching prose. */
export function refusalType(code: string): string {
  return `urn:app:refusal:${code}`
}

/**
 * Group Pydantic's flat error list by field path.
 *
 * `loc` arrives as `["body", "imported_by"]` -- the first element names the
 * request part, not the field, so it is dropped. A `loc` of length <= 1
 * describes the request as a whole and lands under `_`.
 */
function toFieldErrors(errors: PydanticError[]): FieldErrors {
  const grouped: FieldErrors = {}
  for (const error of errors) {
    const path = (error.loc ?? []).slice(1)
    const key = path.length > 0 ? path.join('.') : '_'
    const bucket = grouped[key] ?? (grouped[key] = [])
    bucket.push(error.msg ?? 'Invalid value')
  }
  return grouped
}

const TITLE_BY_STATUS: Record<number, string> = {
  400: 'Bad request',
  401: 'Session expired',
  403: 'Not allowed',
  404: 'Not found',
  409: 'Conflict',
  422: 'That did not pass validation',
  500: 'Server error',
  502: 'Service unavailable',
  503: 'Service unavailable',
  504: 'The request timed out',
}

function titleFor(status: number): string {
  return TITLE_BY_STATUS[status] ?? (status >= 500 ? 'Server error' : 'The request failed')
}

/** Normalise any error body into a `Problem`. */
export function toProblem(status: number, body: unknown): Problem {
  const base: Problem = { type: PROBLEM_BLANK, title: titleFor(status), status }

  if (typeof body !== 'object' || body === null) {
    return typeof body === 'string' && body !== '' ? { ...base, detail: body } : base
  }

  const record = body as Record<string, unknown>

  // Already RFC 9457.
  if (typeof record.title === 'string' && typeof record.status === 'number') {
    return {
      type: typeof record.type === 'string' ? record.type : PROBLEM_BLANK,
      title: record.title,
      status: record.status,
      detail: typeof record.detail === 'string' ? record.detail : undefined,
      errors: (record.errors as FieldErrors | undefined) ?? undefined,
    }
  }

  const { detail } = record

  if (typeof detail === 'string') return { ...base, detail }

  if (isPydanticErrorList(detail)) {
    const errors = toFieldErrors(detail)
    return {
      ...base,
      detail: 'Correct the highlighted fields and send again.',
      errors,
    }
  }

  // A refusal. Checked after the Pydantic list because a 422 can be either and
  // only the shape tells them apart -- a list is field-level validation, an
  // object is a refusal with a code.
  //
  // Without this branch the whole class fell through to `base`, so `detail` was
  // undefined and the screen rendered its "the service returned no details"
  // fallback while the service had in fact returned a finished sentence.
  if (isRefusalDetail(detail)) {
    return { ...base, type: refusalType(detail.code), detail: detail.message }
  }

  return base
}

/** What an error surface needs to render a `Problem`. Prose, not status codes. */
export interface ProblemCopy {
  title: string
  detail: string
  /** Field path -> messages, ready to list. Empty when there are none. */
  fields: [field: string, messages: string[]][]
  /** False when retrying cannot help, so no retry action is offered. */
  retryable: boolean
}

/**
 * Turn a `Problem` into the sentences a screen shows.
 *
 * Here rather than in `components/ui/Feedback`, which renders it: reading a
 * status code and deciding what it means to an operator is knowledge of this
 * API, and `spec/design/conventions.md` § Frontend keeps that out of the shared
 * primitives. `ErrorState`
 * is handed finished prose and paints it.
 *
 * A 404 is described as its own thing rather than as a generic failure:
 * "somebody else deleted this" and "this broke" are different facts, and only
 * one of them is worth retrying. It is the refusal this API emits most, because
 * every route that takes an id can produce it.
 */
export function describeProblem(problem: Problem): ProblemCopy {
  if (problem.status === 404) {
    return {
      title: 'That is gone',
      detail:
        problem.detail ??
        'What you asked for does not exist. Somebody else may have deleted it.',
      fields: [],
      // Retrying re-asks for something that is gone, so the retry action goes
      // away with the refusal that means it cannot come back.
      retryable: false,
    }
  }

  return {
    title: problem.title,
    detail:
      problem.detail ??
      'The service returned no detail. Try again, or check whether the backend answers on /api/health.',
    // Listed because a 422 is almost always a fixable form problem, and naming
    // the field is the whole of the fix.
    fields: Object.entries(problem.errors ?? {}),
    retryable: true,
  }
}

/**
 * A `Problem` thrown as an Error so TanStack Query treats it as a failure.
 *
 * `message` carries `detail ?? title` because that is what generic error
 * surfaces (an error boundary, a console log) will print; components that
 * need structure read `.problem` instead.
 */
export class ApiError extends Error {
  readonly problem: Problem

  constructor(problem: Problem) {
    super(problem.detail ?? problem.title)
    this.name = 'ApiError'
    this.problem = problem
  }

  get status(): number {
    return this.problem.status
  }
}

/** The problem to show for an error of unknown provenance. */
export function problemOf(error: unknown): Problem {
  if (error instanceof ApiError) return error.problem
  if (error instanceof Error) {
    return {
      type: PROBLEM_BLANK,
      title: 'Could not reach the service',
      status: 0,
      detail: error.message,
    }
  }
  return { type: PROBLEM_BLANK, title: 'Unknown error', status: 0 }
}
