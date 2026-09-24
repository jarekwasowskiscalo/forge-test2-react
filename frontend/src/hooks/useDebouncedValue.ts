import { useEffect, useState } from 'react'

/**
 * `value`, but only after it has stopped changing for `delayMs`.
 *
 * The search box needs this and nothing else does yet. It is a hook rather than
 * a `setTimeout` inside the page because the cleanup is the whole of it: without
 * clearing the previous timer on every keystroke, "debounced" becomes "one
 * request per character, each arriving late", which is worse than not
 * debouncing at all -- the answers race and the last one to land wins.
 *
 * The first value is returned immediately rather than after a delay, so a screen
 * that mounts with a phrase already in hand (a restored draft, a test) does not
 * spend the first quarter-second showing the unfiltered book.
 */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [settled, setSettled] = useState(value)

  useEffect(() => {
    if (settled === value) return
    const timer = setTimeout(() => setSettled(value), delayMs)
    return () => clearTimeout(timer)
    // `settled` is read to skip a no-op timer, not to drive the effect: adding
    // it to the dependencies would restart the delay when the value finally
    // settles, which is a timer that exists only to do nothing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, delayMs])

  return settled
}
