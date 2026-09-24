import { forwardRef } from 'react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { cn } from '@/lib/cn'

/**
 * The button, in the mock-up's language: 10px radius, 34px tall, medium weight.
 *
 * Three variants:
 * - `primary`  solid accent green. The one decisive action on a surface.
 * - `outlined` white on a hairline, going accent on hover. Secondary.
 * - `quiet`    borderless, tints on hover. Chrome.
 *
 * **Green is the accent and the accent is a decision.** Only `primary` fills
 * with it, and only one primary belongs on a surface -- a screen with three
 * green buttons has told the reader nothing about which one it means.
 *
 * Deliberately not shadcn/ui: shadcn's defaults (radii, 36/40px heights, `ring`
 * focus) contradict the hairline-and-cream language this screen is drawn in, so
 * every component would need overriding into the ground. These primitives are
 * source-in-repo for the same reason shadcn is -- no dependency drift with the
 * designed components -- but they adhere to this system's tokens.
 */
export type ButtonVariant = 'primary' | 'outlined' | 'quiet'
export type ButtonSize = 'md' | 'lg'

const VARIANT: Record<ButtonVariant, string> = {
  primary:
    'bg-accent text-inverse border border-accent hover:brightness-112 active:scale-[0.97] ' +
    'disabled:opacity-35 disabled:brightness-100',
  outlined:
    'bg-card text-ink border border-hairline hover:border-accent hover:text-accent ' +
    'active:scale-[0.97] disabled:text-disabled disabled:border-hairline',
  quiet:
    'bg-transparent text-muted border border-transparent hover:bg-surface-medium hover:text-ink ' +
    'active:scale-[0.97] disabled:text-disabled',
}

const SIZE: Record<ButtonSize, string> = {
  md: 'h-8.5 px-4',
  lg: 'h-10 px-5',
}

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  /** Stretch to the container's width, as in a sidebar or panel footer. */
  block?: boolean
  children?: ReactNode
}

/** Shared shell so a button and a link-styled-as-a-button cannot drift apart. */
function shell(variant: ButtonVariant, size: ButtonSize, block: boolean, className?: string) {
  return cn(
    'inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 rounded-control no-underline',
    'font-medium text-sm whitespace-nowrap',
    'transition-colors duration-100',
    'disabled:cursor-default',
    VARIANT[variant],
    SIZE[size],
    block && 'w-full',
    className,
  )
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', block = false, className, type = 'button', ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={shell(variant, size, block, className)}
      {...rest}
    />
  )
})

export interface LinkButtonProps {
  to: string
  variant?: ButtonVariant
  size?: ButtonSize
  block?: boolean
  children?: ReactNode
  className?: string
}

/**
 * A router link wearing the button's clothes.
 *
 * Navigation stays an `<a>` -- middle-click, copy-link and the browser's own
 * affordances all keep working, which a `<button onClick={navigate}>` throws
 * away.
 */
export function LinkButton({
  to,
  variant = 'primary',
  size = 'md',
  block = false,
  children,
  className,
}: LinkButtonProps) {
  return (
    <Link to={to} className={shell(variant, size, block, className)}>
      {children}
    </Link>
  )
}
