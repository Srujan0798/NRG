import React, { useRef } from 'react'
import { twMerge } from 'tailwind-merge'
import { actionCopy } from '../../i18n'
import { useFocusTrap } from '../../hooks/useFocusTrap'

type Size = 'sm' | 'md' | 'lg'
type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
type PillTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

const cx = (...classes: Array<string | false | null | void>) => twMerge(classes.filter(Boolean).join(' '))

const sizeClass: Record<Size, string> = {
  sm: 'min-h-9 px-3 text-xs',
  md: 'min-h-11 px-4 text-sm',
  lg: 'min-h-12 px-5 text-base',
}

const buttonVariantClass: Record<ButtonVariant, string> = {
  primary: 'border-transparent bg-accent text-accent-fg shadow-sm hover:bg-accent-hover',
  secondary: 'border-border bg-surface text-fg hover:border-accent hover:text-accent',
  ghost: 'border-transparent bg-transparent text-fg-muted hover:bg-bg-subtle hover:text-fg',
  danger: 'border-transparent bg-danger text-accent-fg shadow-sm hover:opacity-90',
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: Size
  loading?: boolean
}

export function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      aria-busy={loading || void 0}
      className={cx(
        'inline-flex items-center justify-center gap-2 rounded-md border font-semibold transition duration-fast ease-standard',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
        'active:translate-y-px disabled:cursor-not-allowed disabled:opacity-60',
        sizeClass[size],
        buttonVariantClass[variant],
        className,
      )}
    >
      {loading ? <Spinner size="sm" label={actionCopy.loading} /> : null}
      <span className={loading ? 'opacity-90' : ''}>{children}</span>
    </button>
  )
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string | null
  leftSlot?: React.ReactNode
  rightSlot?: React.ReactNode
}

export function Input({ label, error, leftSlot, rightSlot, id, className, ...props }: InputProps) {
  const generatedId = React.useId()
  const fieldId = id || generatedId
  return (
    <label className="block">
      {label ? <span className="mb-2 block text-sm font-semibold text-fg">{label}</span> : null}
      <span className="relative block">
        {leftSlot ? <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-fg-muted">{leftSlot}</span> : null}
        <input
          {...props}
          id={fieldId}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${fieldId}-error` : props['aria-describedby']}
          className={cx(
            'min-h-12 w-full rounded-md border border-border bg-surface px-3 text-base text-fg shadow-sm transition',
            'placeholder:text-fg-subtle focus:border-accent focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-60',
            leftSlot && 'pl-10',
            rightSlot && 'pr-12',
            error && 'border-danger focus:border-danger',
            className,
          )}
        />
        {rightSlot ? <span className="absolute right-2 top-1/2 -translate-y-1/2">{rightSlot}</span> : null}
      </span>
      {error ? <span id={`${fieldId}-error`} className="mt-2 block text-sm font-medium text-danger">{error}</span> : null}
    </label>
  )
}

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string | null
}

export function Textarea({ label, error, id, className, ...props }: TextareaProps) {
  const generatedId = React.useId()
  const fieldId = id || generatedId
  return (
    <label className="block">
      {label ? <span className="mb-2 block text-sm font-semibold text-fg">{label}</span> : null}
      <textarea
        {...props}
        id={fieldId}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${fieldId}-error` : props['aria-describedby']}
        className={cx(
          'min-h-28 w-full resize-y rounded-md border border-border bg-surface px-3 py-3 text-base text-fg shadow-sm transition',
          'placeholder:text-fg-subtle focus:border-accent focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-60',
          error && 'border-danger focus:border-danger',
          className,
        )}
      />
      {error ? <span id={`${fieldId}-error`} className="mt-2 block text-sm font-medium text-danger">{error}</span> : null}
    </label>
  )
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
}

export function Select({ label, id, className, children, ...props }: SelectProps) {
  const generatedId = React.useId()
  const fieldId = id || generatedId
  return (
    <label className="block">
      {label ? <span className="mb-2 block text-sm font-semibold text-fg">{label}</span> : null}
      <select
        {...props}
        id={fieldId}
        className={cx(
          'min-h-11 w-full rounded-md border border-border bg-surface px-3 text-sm font-semibold text-fg shadow-sm transition',
          'focus:border-accent focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-60',
          className,
        )}
      >
        {children}
      </select>
    </label>
  )
}

export function Checkbox(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      type="checkbox"
      className={cx('h-5 w-5 rounded-sm border-border text-accent focus:ring-ring', props.className)}
    />
  )
}

export function Radio(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      type="radio"
      className={cx('h-5 w-5 border-border text-accent focus:ring-ring', props.className)}
    />
  )
}

export interface CardProps extends React.HTMLAttributes<HTMLElement> {
  as?: 'article' | 'section' | 'div'
  padding?: 'sm' | 'md' | 'lg'
  interactive?: boolean
}

export function Card({ as: Tag = 'section', padding = 'md', interactive = false, className, ...props }: CardProps) {
  const paddingClass = padding === 'sm' ? 'p-3' : padding === 'lg' ? 'p-6' : 'p-4'
  return (
    <Tag
      {...props}
      className={cx(
        'rounded-lg border border-border bg-surface shadow-sm',
        paddingClass,
        interactive && 'transition hover:-translate-y-px hover:border-accent hover:shadow-md',
        className,
      )}
    />
  )
}

const pillToneClass: Record<PillTone, string> = {
  neutral: 'border-border bg-bg-subtle text-fg-muted',
  info: 'border-accent bg-accent/10 text-accent',
  success: 'border-success bg-success/10 text-success',
  warning: 'border-warning bg-warning/10 text-warning',
  danger: 'border-danger bg-danger/10 text-danger',
}

export interface PillProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: PillTone
}

export function Pill({ tone = 'neutral', className, ...props }: PillProps) {
  return (
    <span
      {...props}
      className={cx('inline-flex items-center gap-1 rounded-pill border px-2.5 py-1 text-xs font-semibold', pillToneClass[tone], className)}
    />
  )
}

export interface DrawerProps {
  open: boolean
  title: string
  onClose: () => void
  children: React.ReactNode
  testId?: string
}

export function Drawer({ open, title, onClose, children, testId }: DrawerProps) {
  const panelRef = useRef<HTMLElement>(null)
  useFocusTrap(panelRef, open, onClose)

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label={title} data-testid={testId}>
      <button className="absolute inset-0 bg-fg/20" type="button" tabIndex={-1} aria-label={actionCopy.closeDrawer} onClick={onClose} />
      <aside ref={panelRef} className="absolute bottom-0 right-0 top-0 flex w-full max-w-xl flex-col border-l border-border bg-surface shadow-lg max-md:max-w-none">
        <header className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-base font-bold text-fg">{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>{actionCopy.close}</Button>
        </header>
        <div className="min-h-0 flex-1 overflow-auto p-5">{children}</div>
      </aside>
    </div>
  )
}

export type ModalProps = DrawerProps

export function Modal({ open, title, onClose, children }: ModalProps) {
  const panelRef = useRef<HTMLElement>(null)
  useFocusTrap(panelRef, open, onClose)

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4" role="dialog" aria-modal="true" aria-label={title}>
      <button className="absolute inset-0 bg-fg/20" type="button" tabIndex={-1} aria-label={actionCopy.closeModal} onClick={onClose} />
      <section ref={panelRef} className="relative w-full max-w-lg rounded-lg border border-border bg-surface p-5 shadow-lg">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-base font-bold text-fg">{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>{actionCopy.close}</Button>
        </div>
        {children}
      </section>
    </div>
  )
}

export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  tone?: PillTone
}

export function Toast({ tone = 'info', className, ...props }: ToastProps) {
  return (
    <div
      {...props}
      role="status"
      aria-live="polite"
      className={cx('rounded-md border bg-surface px-4 py-3 text-sm shadow-md', pillToneClass[tone], className)}
    />
  )
}

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div {...props} className={cx('animate-pulse rounded-md bg-bg-subtle', className)} />
}

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

export function Spinner({ size = 'md', label = actionCopy.loading }: SpinnerProps) {
  const spinnerSize = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-6 w-6' : 'h-5 w-5'
  return (
    <span className={cx('inline-block animate-spin rounded-full border-2 border-current border-t-transparent', spinnerSize)} role="status" aria-label={label} />
  )
}
