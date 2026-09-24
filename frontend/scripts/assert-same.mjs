/**
 * Fail unless two files are byte-identical, printing a readable diff.
 *
 * Replaces `diff -u a b` in `gen:api:check`. An npm script that shells out to a
 * POSIX binary is a gate that depends on what happens to be installed beside
 * node; this one depends on node alone, which `package.json` already requires.
 * It also normalises line endings, which `diff` does not.
 *
 * Usage: node scripts/assert-same.mjs <committed> <regenerated> [label]
 */
import { readFileSync } from 'node:fs'

const [, , committedPath, regeneratedPath, label = 'file'] = process.argv
if (!committedPath || !regeneratedPath) {
  console.error('usage: assert-same.mjs <committed> <regenerated> [label]')
  process.exit(2)
}

const read = (path) => {
  try {
    // Normalised so a CRLF checkout on Windows is not reported as a difference:
    // the generator always writes LF, and .gitattributes stores LF.
    return readFileSync(path, 'utf8').replace(/\r\n/g, '\n')
  } catch (error) {
    console.error(`could not read ${path}: ${error.message}`)
    process.exit(2)
  }
}

const committed = read(committedPath).split('\n')
const regenerated = read(regeneratedPath).split('\n')

const differences = []
for (let i = 0; i < Math.max(committed.length, regenerated.length); i += 1) {
  if (committed[i] !== regenerated[i]) {
    differences.push(`  line ${i + 1}:\n    committed:   ${committed[i] ?? '(absent)'}\n    regenerated: ${regenerated[i] ?? '(absent)'}`)
    if (differences.length === 10) break
  }
}

if (differences.length === 0) {
  console.log(`${label} is up to date`)
  process.exit(0)
}

console.error(
  `error: ${committedPath} is stale — it does not match what the backend now generates.\n` +
    `Regenerate it and commit the result.\n\n${differences.join('\n')}\n`,
)
process.exit(1)
