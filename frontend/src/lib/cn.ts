type ClassValue = string | number | false | null | undefined

/**
 * Join class names, dropping falsy entries.
 *
 * Deliberately not `tailwind-merge`: no component here takes a `className`
 * that has to override a base utility, so conflict resolution would be dead
 * weight. If a variant needs to win, it is spelled out in the variant map
 * rather than layered on top.
 */
export function cn(...values: ClassValue[]): string {
  return values.filter(Boolean).join(' ')
}
