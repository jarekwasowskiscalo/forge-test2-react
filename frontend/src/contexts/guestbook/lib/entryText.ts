/**
 * How the browser trims a text field and how long it considers it to be.
 *
 * The other half of `app/platform/schemas/text.py`, and a **copy** for the same
 * reason the bounds beside it are copies: the browser cannot import Python. What
 * makes the copy legal is not care -- it is the shared text-measurement corpus
 * that both sides read, asserting the same verdicts and the same lengths against
 * the same bytes. `entryText.test.ts` is the module that reads it and the only one
 * in this tree allowed to; this file names no corpus path, because a rule has no
 * business knowing where it is proved.
 *
 * **The unit is code points, after NFC normalization.** Before this module the
 * browser measured `value.length`, which is UTF-16 code units, while the server
 * measured code points. The two agreed for as long as nobody typed anything
 * outside the Basic Multilingual Plane, and then stopped: a signature of 41
 * grinning faces is 82 to `.length` and 41 to Python, so the browser refused an
 * entry the API stored with a 201. Nothing detected it, because every test on
 * each side read its own constant and both constants said `80`.
 *
 * **Trimming is a written set rather than this runtime's default.**
 * `String.prototype.trim` removes 25 code points and Python's `str.strip()`
 * removes 29; the BOM is in the first set only and the four C0 separators and NEL
 * in the second only. The set below is the union, so no code point is content in
 * one language and whitespace in the other. `app/platform/schemas/text.py` carries
 * the full argument, the reason each group is in it, and where the corpus lives.
 */

/**
 * Unicode's `White_Space` property -- the 25 code points both runtimes already
 * agreed about. Written as numbers rather than as escapes in a string literal, so
 * an editor, a checkout or a re-encoding cannot silently rewrite the data.
 */
export const WHITE_SPACE: readonly number[] = [
  0x0009, 0x000a, 0x000b, 0x000c, 0x000d, 0x0020, 0x0085, 0x00a0, 0x1680, 0x2000, 0x2001, 0x2002,
  0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f,
  0x3000,
]

/**
 * The C0 separators, which `str.strip()` has always removed and
 * `String.prototype.trim` never has. In the set because a file separator arriving
 * inside a signature is a paste accident either way.
 */
export const C0_SEPARATORS: readonly number[] = [0x001c, 0x001d, 0x001e, 0x001f]

/**
 * The byte order mark, which this runtime trims and Python does not. In the set
 * for the plainest of reasons: it arrives by itself at the front of text pasted
 * out of an ordinary editor, and a guest who pasted it did not type it.
 */
export const BYTE_ORDER_MARK: readonly number[] = [0xfeff]

/**
 * The 30 code points removed from either end of a value, and the only ones.
 *
 * `U+200B` ZERO WIDTH SPACE and `U+180E` MONGOLIAN VOWEL SEPARATOR are deliberately
 * absent: neither runtime treats them as whitespace, so they are content. The
 * corpus states that in a case of its own rather than leaving it to be discovered.
 */
export const TRIMMED: ReadonlySet<string> = new Set(
  [...WHITE_SPACE, ...C0_SEPARATORS, ...BYTE_ORDER_MARK].map((code) => String.fromCodePoint(code)),
)

/**
 * The value as it will be measured, sent and stored.
 *
 * NFC first, then the edges -- the same order as the server, and it matters in one
 * direction: normalizing afterwards could compose a combining mark with a letter
 * the trim had just exposed.
 *
 * Walks code points rather than calling `trim()`, because `trim()` is exactly the
 * runtime default this module exists to stop depending on. Every member of
 * `TRIMMED` is a single code point in the Basic Multilingual Plane, so iterating
 * the spread form is safe.
 *
 * Only the ends. Whitespace inside a value is content: a message is written in
 * lines and keeping them is the point (`BR-01`).
 */
export function normalizeText(value: string): string {
  const points = [...value.normalize('NFC')]
  // `noUncheckedIndexedAccess` cannot see that both indices stay inside the array
  // while `start < end <= points.length`. The empty string is in no set, so the
  // fallback can only end a loop -- which is what an out-of-range index would have
  // meant anyway.
  const at = (index: number): string => points[index] ?? ''
  let start = 0
  let end = points.length
  while (start < end && TRIMMED.has(at(start))) start += 1
  while (end > start && TRIMMED.has(at(end - 1))) end -= 1
  return points.slice(start, end).join('')
}

/**
 * How long `value` is, in the unit the bounds are written in.
 *
 * `[...value].length` and never `value.length`. The spread form iterates code
 * points, which is what the column, the published contract and Pydantic all count;
 * `.length` counts UTF-16 code units, which is what made the browser and the server
 * disagree about the same string while both read the literal `80`.
 *
 * Measures the value as given -- a caller that means the trimmed length calls
 * `normalizeText` first.
 */
export function textLength(value: string): number {
  return [...value].length
}
