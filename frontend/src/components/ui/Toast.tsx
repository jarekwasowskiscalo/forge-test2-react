import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

/**
 * Toasts: bottom-right, dark ink fill, 8px stack gap.
 *
 * Confirmations in this app name their consequence -- not "Saved" but
 * "Entry posted." `message` is therefore a sentence, not a status word.
 *
 * The tone is carried by a single leading glyph (green ✓ / amber ● / red ●),
 * never by a coloured background: a large green fill behind text is explicitly
 * out of bounds in this system.
 *
 * **An error toast does not expire and is announced immediately.** The other
 * two report something that went as intended, so they can be missed without
 * cost and live 3.6s in a `polite` region that waits its turn. An error is the
 * only thing a toast says that the operator has to act on -- and a run whose
 * upload failed leaves nothing else on screen naming the reason. Letting that
 * sentence disappear after 3.6s, behind whatever a screen reader happened to
 * be reading, would make the failure quieter than the success. So errors sit
 * in an `assertive` region and stay until dismissed.
 *
 * Every toast carries a close button for the same reason: 3.6s is short for a
 * long sentence, and a live region a user cannot dismiss re-announces itself
 * on some readers.
 */

/** How long a toast stays up before it dismisses itself. */
const TOAST_LIFE_MS = 3600

export type ToastTone = 'success' | 'warning' | 'error'

interface Toast {
  id: number
  tone: ToastTone
  message: string
}

interface ToastApi {
  /** Show a toast. Returns nothing -- toasts are fire-and-forget. */
  push: (message: string, tone?: ToastTone) => void
}

const ToastContext = createContext<ToastApi | undefined>(undefined)

const GLYPH: Record<ToastTone, { char: string; className: string }> = {
  success: { char: '✓', className: 'text-green-600' },
  warning: { char: '●', className: 'text-amber-600' },
  error: { char: '●', className: 'text-red-600' },
}

export interface ToastProviderProps {
  children: ReactNode
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const push = useCallback((message: string, tone: ToastTone = 'success') => {
    setToasts((current) => [
      ...current,
      // Not Date.now(): two toasts pushed in the same tick would collide on
      // the React key. A monotonic counter derived from the list cannot.
      { id: (current.at(-1)?.id ?? 0) + 1, tone, message },
    ])
  }, [])

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const api = useMemo<ToastApi>(() => ({ push }), [push])

  // Two regions, because a region's `aria-live` is fixed at the point the
  // browser starts observing it -- flipping the attribute on one shared region
  // per toast is unreliable across readers. Both are rendered at all times so
  // neither is a newly-inserted live region, which some readers skip.
  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="pointer-events-none fixed right-5 bottom-5 z-50 flex flex-col gap-2">
        <ToastStack
          toasts={toasts.filter((toast) => toast.tone !== 'error')}
          onDismiss={dismiss}
          live="polite"
          label="Notifications"
          expires
        />
        <ToastStack
          toasts={toasts.filter((toast) => toast.tone === 'error')}
          onDismiss={dismiss}
          live="assertive"
          label="Errors"
          expires={false}
        />
      </div>
    </ToastContext.Provider>
  )
}

function ToastStack({
  toasts,
  onDismiss,
  live,
  label,
  expires,
}: {
  toasts: readonly Toast[]
  onDismiss: (id: number) => void
  live: 'polite' | 'assertive'
  label: string
  expires: boolean
}) {
  return (
    <div role="region" aria-label={label} aria-live={live} className="flex flex-col gap-2">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} expires={expires} />
      ))}
    </div>
  )
}

function ToastItem({
  toast,
  onDismiss,
  expires,
}: {
  toast: Toast
  onDismiss: (id: number) => void
  expires: boolean
}) {
  useEffect(() => {
    if (!expires) return
    const timer = window.setTimeout(() => onDismiss(toast.id), TOAST_LIFE_MS)
    return () => window.clearTimeout(timer)
  }, [toast.id, onDismiss, expires])

  const glyph = GLYPH[toast.tone]

  return (
    <div
      className={cn(
        'pointer-events-auto flex max-w-md items-start gap-2.5 rounded-xl',
        'bg-ink px-3.5 py-2.5 text-xs font-bold text-inverse shadow-xl',
        'animate-rise leading-relaxed text-pretty',
      )}
    >
      <span className={cn('shrink-0 font-bold', glyph.className)} aria-hidden="true">
        {glyph.char}
      </span>
      <span className="min-w-0 flex-1">{toast.message}</span>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
        className={cn(
          'shrink-0 cursor-pointer rounded-full border-0 bg-transparent px-1',
          'text-sm font-bold text-inverse/60 hover:text-inverse',
        )}
      >
        <span aria-hidden="true">×</span>
      </button>
    </div>
  )
}

// The provider and its hook are one module by design -- the context object is
// private to this file, so a separate `useToast.ts` would have to export it and
// make the context reachable without the provider. Fast refresh loses this
// file's state on edit; a toast's state is a 3.6s timer, which is not state
// worth restructuring a context around.
// eslint-disable-next-line react-refresh/only-export-components
export function useToast(): ToastApi {
  const api = useContext(ToastContext)
  if (!api) throw new Error('useToast must be used inside <ToastProvider>')
  return api
}
