import type { CSSProperties } from 'react'

import { describeProblem, type Problem } from '@/api/problem'
import { cn } from '@/lib/cn'

import { Button } from './Button'

/**
 * Loading and error surfaces.
 *
 * Every list and detail view in this app needs both, so they live together here
 * rather than being re-derived per page. Neither knows a status code or a domain
 * rule: `ErrorState` takes a `Problem` and asks `describeProblem` what it means,
 * which is where the knowledge of this API belongs. (An `EmptyState` used to live
 * beside them and nothing rendered it -- the guestbook says "nothing here" in its
 * own words, `entryListCopy.ts` -- so it went, as `conventions.md` § Frontend asks
 * of a primitive with no caller.)
 */

export interface SkeletonProps {
  className?: string
  style?: CSSProperties
}

/** A static grey block. Skeletons in this system do NOT shimmer. */
export function Skeleton({ className, style }: SkeletonProps) {
  return (
    <div
      className={cn('rounded-md bg-surface-medium', className)}
      style={style}
      aria-hidden="true"
    />
  )
}

export interface ErrorStateProps {
  problem: Problem
  onRetry?: () => void
  className?: string
}

/** The error surface for a failed query or mutation. */
export function ErrorState({ problem, onRetry, className }: ErrorStateProps) {
  const { title, detail, fields, retryable } = describeProblem(problem)

  return (
    <div
      role="alert"
      className={cn(
        'rounded-card border border-hairline bg-card px-6 py-8 text-center',
        className,
      )}
    >
      <p className="m-0 text-base font-bold">{title}</p>
      <p className="mx-auto mt-2 mb-0 max-w-2xl text-sm text-muted leading-relaxed text-pretty">{detail}</p>
      {fields.length > 0 && (
        <ul className="mx-auto mt-3 mb-0 max-w-2xl list-none p-0 text-left text-xs">
          {fields.map(([field, messages]) => (
            <li key={field} className="flex gap-2 border-t border-hairline py-1.5">
              <span className="shrink-0 font-bold text-danger">●</span>
              <span className="min-w-0 flex-1">
                <b>{field === '_' ? 'Request' : field}</b> — {messages.join('; ')}
              </span>
            </li>
          ))}
        </ul>
      )}
      {onRetry !== undefined && retryable && (
        <div className="mt-3.5 flex justify-center">
          <Button variant="outlined" onClick={onRetry}>
            Try again
          </Button>
        </div>
      )}
    </div>
  )
}
